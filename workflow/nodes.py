#!/usr/bin/env python3
"""
Customer Care Workflow Nodes for LangGraph

This file defines all the nodes for the centralized customer care LangGraph workflow:
1. Listener Node - Handles audio input and conversation
2. Conditional Node - Routes to appropriate company agent
3. Amazon Agent Node - Handles Amazon customer service with hybrid RAG
4. Facebook Agent Node - Handles Facebook customer service with hybrid RAG
5. Protocol Execution Node - Final resolution with TTS output
"""

import os
import json
import requests
import whisper
import sounddevice as sd
import numpy as np
import wave
import pygame
import tempfile
import base64
from gtts import gTTS
from pathlib import Path
from typing import Dict, Any, TypedDict
from datetime import datetime
from groq import Groq

# LangChain imports
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# State schema for LangGraph
class CustomerCareState(TypedDict, total=False):
    """State structure for the customer care workflow"""
    # Input data
    audio_input: str
    query: str
    
    # Conversation data
    customer_name: str
    problem_description: str
    product_name: str
    company_name: str
    customer_phone: str
    customer_email: str
    conversation_history: list
    
    # Processing data
    agent_response: str
    final_solution: str
    protocol_execution: str  # Protocol execution output
    customer_reassurance: str  # Final customer message
    error: str
    
    # Execution tracking
    execution_log: list  # Track what happened in each node
    protocol_steps: list  # Final protocol as bullet points
    protocol_execution: str  # New field for protocol execution output
    customer_reassurance: str  # New field for final customer message
    error: str

# Initialize global components
project_root = Path(__file__).parent.parent
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_retriever(company_name: str) -> EnsembleRetriever:
    """Load hybrid retriever for a specific company"""
    vector_store_path = project_root / "data" / "vector_data" / f"{company_name}_customer_service_augmented"
    
    if not vector_store_path.exists():
        raise FileNotFoundError(f"Vector store not found for {company_name}: '{vector_store_path}'")
    
    # Load FAISS vectorstore
    vectorstore = FAISS.load_local(str(vector_store_path), embeddings, allow_dangerous_deserialization=True)
    
    # Create semantic retriever
    semantic_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    # Create BM25 retriever from vectorstore documents
    raw_documents = vectorstore.similarity_search("customer service", k=1000)
    bm25_retriever = BM25Retriever.from_documents(raw_documents)
    bm25_retriever.k = 5
    
    # Create hybrid retriever
    hybrid_retriever = EnsembleRetriever(
        retrievers=[semantic_retriever, bm25_retriever],
        weights=[0.7, 0.3]  # 70% semantic, 30% keyword
    )
    
    return hybrid_retriever

def format_docs(docs: list) -> str:
    """Extract resolution steps from documents for clean LLM context"""
    formatted_steps = []
    for i, doc in enumerate(docs):
        content = doc.page_content
        if "Resolution Steps:" in content:
            steps = content.split("Resolution Steps:", 1)[1].strip()
            formatted_steps.append(f"--- Potential Protocol Option {i+1} ---\n{steps}")
    
    if not formatted_steps:
        return "No specific resolution steps were found in the retrieved documents."
        
    return "\n\n".join(formatted_steps)

def record_audio(duration: int = 15, sample_rate: int = 16000) -> np.ndarray:
    """Record audio from microphone"""
    print(f"Recording ({duration}s)... Please speak now.")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
    sd.wait()
    print("Recording complete.")
    return audio_data.flatten()

def transcribe_audio(audio_data: np.ndarray, whisper_model, sample_rate: int = 16000) -> str:
    """Convert audio to text using Whisper"""
    try:
        # Save audio to temporary file
        temp_file = "temp_audio.wav"
        with wave.open(temp_file, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            # Convert float32 to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())
        
        # Transcribe using Whisper
        result = whisper_model.transcribe(temp_file)
        
        # Clean up temp file
        os.remove(temp_file)
        
        return result["text"].strip()
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return ""

def speak_text(text: str):
    """Convert text to speech using Murf API with Google TTS fallback"""
    # Always display text immediately
    print(f"Agent: {text}")
    
    murf_api_key = os.getenv("MURF_API_KEY")
    
    # Try Murf API first if available
    if murf_api_key:
        try:
            print("🔊 Generating speech with Murf...")
            
            headers = {
                "api-key": murf_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "voiceId": "en-US-natalie",
                "text": text,
                "rate": 0,
                "pitch": 0,
                "sampleRate": 44100,
                "format": "wav"
            }
            
            response = requests.post(
                "https://api.murf.ai/v1/speech/generate", 
                json=payload, 
                headers=headers, 
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if we got audio data
                if "audioFile" in response_data:
                    audio_data = response_data["audioFile"]
                    
                    # Handle different response formats
                    if isinstance(audio_data, str):
                        # Could be base64 or URL
                        if audio_data.startswith('http'):
                            # It's a URL - download the file
                            audio_response = requests.get(audio_data, timeout=30)
                            if audio_response.status_code == 200:
                                audio_bytes = audio_response.content
                            else:
                                raise Exception(f"Failed to download audio from URL: {audio_response.status_code}")
                        else:
                            # Try to decode as base64
                            try:
                                audio_bytes = base64.b64decode(audio_data)
                            except Exception:
                                raise Exception("Failed to decode base64 audio data")
                    else:
                        audio_bytes = audio_data
                    
                    # Save to temporary file and play
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        temp_file.write(audio_bytes)
                        temp_file_path = temp_file.name
                    
                    # Initialize pygame mixer and play
                    pygame.mixer.init()
                    pygame.mixer.music.load(temp_file_path)
                    pygame.mixer.music.play()
                    
                    # Wait for playback to complete
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                    
                    # Clean up
                    pygame.mixer.quit()
                    os.unlink(temp_file_path)
                    
                    print("✅ Murf TTS audio played successfully")
                    return True
                else:
                    print("❌ No audio file in Murf response")
                    print(f"Response keys: {list(response_data.keys())}")
                    raise Exception("No audio data from Murf")
            else:
                print(f"❌ Murf API error: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                raise Exception(f"Murf API failed: {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️ Murf TTS failed: {e}")
            print("🔄 Falling back to Google TTS...")
    else:
        print("⚠️ No Murf API key found, using Google TTS...")
    
    # Fallback to Google TTS
    try:
        print("🔊 Generating speech with Google TTS...")
        
        # Create gTTS object
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file_path = temp_file.name
            
        # Save TTS audio to file
        tts.save(temp_file_path)
        
        # Initialize pygame mixer and play
        pygame.mixer.init()
        pygame.mixer.music.load(temp_file_path)
        pygame.mixer.music.play()
        
        # Wait for playback to complete
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        
        # Clean up
        pygame.mixer.quit()
        os.unlink(temp_file_path)
        
        print("✅ Google TTS audio played successfully")
        return True
        
    except Exception as e:
        print(f"❌ Google TTS failed: {e}")
        print("📝 Text-only mode activated")
        return False

# --- NODE DEFINITIONS ---

def listener_node(state: CustomerCareState) -> CustomerCareState:
    """
    Customer conversation with audio input/output
    """
    print("\nStarting customer service conversation...")
    
    # Initialize execution log
    if "execution_log" not in state:
        state["execution_log"] = []
    
    try:
        # Initialize speech services
        whisper_model = whisper.load_model("tiny")
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Questions for customer
        questions = [
            "Hello! I'm here to help you today. Please tell me your name and describe your issue.",
            "Could you please provide your phone number or email address?",
            "Can you give me more details about what exactly happened?",
            "What is the product name or model you're having issues with?",
            "What is the company name that you are facing issues with?",
            "When did you purchase this or when did the issue start?",
            "Is there anything else that might help us resolve this?"
        ]
        
        conversation_history = []
        responses = []
        
        # Conduct conversation
        for i, question in enumerate(questions, 1):
            print(f"\nQuestion {i}:")
            
            # Ask question with TTS
            speak_text(question)
            conversation_history.append({"role": "agent", "message": question})
            
            # Get customer response
            try:
                audio_data = record_audio(duration=15)
                customer_response = transcribe_audio(audio_data, whisper_model)
                
                if not customer_response.strip():
                    customer_response = input("Please type your response: ").strip()
                
                print(f"Customer: {customer_response}")
                conversation_history.append({"role": "customer", "message": customer_response})
                responses.append(customer_response)
                
            except KeyboardInterrupt:
                print("\nUsing demo data...")
                state.update({
                    "customer_name": "chahi",
                    "problem_description": "Macbook suddenly stopped working, screen went black",
                    "product_name": "MacBook Pro 13-inch",
                    "company_name": "apple",
                    "customer_phone": "45654e456",
                    "customer_email": "abcd@123.com",
                    "conversation_history": [{"role": "customer", "message": "Demo data"}],
                    "query": "Macbook suddenly stopped working, screen went black"
                })
                return state
        
        # Process conversation data with improved extraction
        extraction_prompt = f"""
You are an expert customer service data extractor. Analyze this conversation and extract key information accurately.

CONVERSATION DATA:
{json.dumps(conversation_history, indent=2)}

EXTRACTION RULES:
1. customer_name: Extract the person's actual name (not "Customer" or generic terms)
2. problem_description: Summarize the main issue in 1-2 clear sentences
3. product_name: Extract specific product/service mentioned (phone model, app name, etc.)
4. company_name: CRITICAL - Extract the company name exactly as mentioned:
   - "Facebook" or "Meta" → "facebook"
   - "Amazon" → "amazon"  
   - "Apple" → "apple"
   - Look in ALL messages, not just the company question
5. customer_phone: Extract phone number (clean format)
6. customer_email: Extract email address

REQUIRED OUTPUT FORMAT (valid JSON only):
{{
    "customer_name": "actual name from conversation",
    "problem_description": "clear summary of the issue", 
    "product_name": "specific product mentioned",
    "company_name": "facebook/amazon/apple/etc",
    "customer_phone": "phone number", 
    "customer_email": "email address"
}}

IMPORTANT: Return ONLY the JSON object, no additional text or explanation.
"""
        
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": extraction_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,  # Slightly higher for better extraction
            max_tokens=500    # Ensure enough tokens for complete response
        )
        
        # Extract and update state with better parsing
        try:
            response_text = response.choices[0].message.content.strip()
            
            # Clean response text (remove code blocks if present)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].strip()
            
            extracted_data = json.loads(response_text)
            
            # Validate and clean extracted data
            cleaned_data = {
                "customer_name": str(extracted_data.get("customer_name", "")).strip() or "Customer",
                "problem_description": str(extracted_data.get("problem_description", "")).strip() or "Issue reported",
                "product_name": str(extracted_data.get("product_name", "")).strip() or "Product",
                "company_name": str(extracted_data.get("company_name", "")).lower().strip(),
                "customer_phone": str(extracted_data.get("customer_phone", "")).strip() or "Not provided",
                "customer_email": str(extracted_data.get("customer_email", "")).strip() or "Not provided"
            }
            
            state.update({
                "customer_name": cleaned_data["customer_name"],
                "problem_description": cleaned_data["problem_description"],
                "product_name": cleaned_data["product_name"],
                "company_name": cleaned_data["company_name"],
                "customer_phone": cleaned_data["customer_phone"],
                "customer_email": cleaned_data["customer_email"],
                "conversation_history": conversation_history,
                "query": cleaned_data["problem_description"]
            })
            
            print(f"✅ Extracted: {cleaned_data['customer_name']} | Company: {cleaned_data['company_name'] or 'Unknown'}")
        except (json.JSONDecodeError, KeyError, Exception) as e:
            print(f"⚠️ LLM extraction failed: {e}")
            print(f"Raw response: {response.choices[0].message.content[:200]}...")
            
            # Enhanced fallback data with smart company detection
            conversation_text = " ".join([msg["message"].lower() for msg in conversation_history])
            
            # Detect company from conversation text
            company_name = ""
            if "facebook" in conversation_text or "meta" in conversation_text:
                company_name = "facebook"
            elif "amazon" in conversation_text:
                company_name = "amazon"
            elif "apple" in conversation_text:
                company_name = "apple"
            
            # Try to extract name from first response
            customer_name = "Customer"
            if responses and len(responses) > 0:
                first_response = responses[0].lower()
                if "my name is" in first_response:
                    try:
                        name_part = first_response.split("my name is")[1].strip()
                        potential_name = name_part.split()[0].strip(".,!?")
                        if potential_name.isalpha() and len(potential_name) > 1:
                            customer_name = potential_name.title()
                    except:
                        pass
            
            state.update({
                "customer_name": customer_name,
                "problem_description": " ".join(responses[:3]) if responses else "Issue reported",
                "product_name": responses[3] if len(responses) > 3 else "Product",
                "company_name": company_name,
                "customer_phone": "Not provided",
                "customer_email": "Not provided",
                "conversation_history": conversation_history,
                "query": " ".join(responses[:3]) if responses else "Issue reported"
            })
            
            print(f"🔄 Fallback extraction: {customer_name} | Company: {company_name or 'Unknown'}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        # Demo fallback
        state.update({
            "customer_name": "Demo Customer",
            "problem_description": "Demo issue",
            "product_name": "Demo Product",
            "company_name": "amazon",
            "customer_phone": "555-0123",
            "customer_email": "demo@test.com",
            "conversation_history": [{"role": "customer", "message": "Demo"}],
            "query": "Demo issue"
        })
    
    # Log execution
    state["execution_log"].append({
        "node": "Listener Node",
        "status": "completed",
        "description": f"Conducted 7-question conversation with {state.get('customer_name', 'customer')}, extracted information, identified company: {state.get('company_name', 'unknown')}"
    })
    
    return state

def routing_node(state: CustomerCareState) -> str:
    """
    Route to appropriate company agent
    """
    company = state.get("company_name", "").lower().strip()
    
    print(f"🔍 Routing decision: company_name = '{company}'")
    
    if "amazon" in company:
        print("📦 Routing to Amazon agent")
        return "amazon_agent"
    elif "facebook" in company or "meta" in company:
        print("📘 Routing to Facebook agent")
        return "facebook_agent"
    elif "apple" in company:
        print("🍎 Routing to Amazon agent (Apple fallback)")
        return "amazon_agent"  # Route to Amazon for now
    else:
        print("⚠️ No company match found, defaulting to Amazon agent")
        return "amazon_agent"  # Default

def amazon_agent_node(state: CustomerCareState) -> CustomerCareState:
    """
    Amazon agent node with hybrid RAG
    """
    print("\n🛒 AMAZON AGENT - Processing customer issue...")
    
    try:
        # Load Amazon hybrid retriever
        retriever = load_retriever("amazon")
        
        # Initialize LLM
        llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=300  # Reduced for concise protocols
        )
        
        # Create prompt template
        prompt_template = """
You are an expert Amazon customer service agent. Generate a CONCISE, actionable resolution protocol.

CUSTOMER: {customer_name}
PRODUCT: {product_name}
ISSUE: {problem_description}
CONTACT: {customer_email}, {customer_phone}

RELEVANT SOLUTIONS:
{context}

INSTRUCTIONS:
- Create a BRIEF, step-by-step resolution plan (maximum 4 steps)
- Focus on IMMEDIATE actions that resolve the issue
- Be specific and actionable
- No lengthy explanations
- If no relevant solution exists, state: "Resolution protocol not available in knowledge base."

CONCISE RESOLUTION PROTOCOL:"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Create chain
        chain = prompt | llm | StrOutputParser()
        
        # Get query and retrieve documents
        query = state.get("query", "")
        retrieved_docs = retriever.invoke(query)
        
        # Format context
        context = format_docs(retrieved_docs)
        
        # Generate response
        response = chain.invoke({
            "context": context,
            "query": query,
            "customer_name": state.get("customer_name", ""),
            "product_name": state.get("product_name", ""),
            "problem_description": state.get("problem_description", ""),
            "customer_email": state.get("customer_email", ""),
            "customer_phone": state.get("customer_phone", "")
        })
        
        # Update state
        state["agent_response"] = response
        state["final_solution"] = response
        
        print("✅ Amazon protocol generated efficiently")
        
    except Exception as e:
        error_msg = f"Amazon agent error: {str(e)}"
        state["error"] = error_msg
        print(f"❌ Amazon agent failed: {e}")
    
    # Log execution
    if "execution_log" not in state:
        state["execution_log"] = []
    
    if not state.get("error"):
        state["execution_log"].append({
            "node": "Amazon Agent",
            "status": "completed", 
            "description": f"Retrieved relevant Amazon support documents, generated resolution protocol using hybrid RAG (FAISS + BM25)"
        })
    else:
        state["execution_log"].append({
            "node": "Amazon Agent",
            "status": "failed",
            "description": f"Failed to process: {state.get('error', 'unknown error')}"
        })
    
    return state

def facebook_agent_node(state: CustomerCareState) -> CustomerCareState:
    """
    Facebook agent node with hybrid RAG
    """
    print("\n📘 FACEBOOK AGENT - Processing customer issue...")
    
    try:
        # Load Facebook hybrid retriever
        retriever = load_retriever("facebook")
        
        # Initialize LLM
        llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=300
        )
        
        # Create prompt template
        prompt_template = """
You are an expert Facebook customer service agent. Generate a CONCISE, actionable resolution protocol.

CUSTOMER: {customer_name}
PRODUCT: {product_name}
ISSUE: {problem_description}
CONTACT: {customer_email}, {customer_phone}

RELEVANT SOLUTIONS:
{context}

INSTRUCTIONS:
- Create a BRIEF, step-by-step resolution plan (maximum 4 steps)
- Focus on IMMEDIATE actions that resolve the issue
- Be specific and actionable
- No lengthy explanations
- If no relevant solution exists, state: "Resolution protocol not available in knowledge base."

CONCISE RESOLUTION PROTOCOL:"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Create chain
        chain = prompt | llm | StrOutputParser()
        
        # Get query and retrieve documents
        query = state.get("query", "")
        retrieved_docs = retriever.invoke(query)
        
        # Format context
        context = format_docs(retrieved_docs)
        
        # Generate response
        response = chain.invoke({
            "context": context,
            "query": query,
            "customer_name": state.get("customer_name", ""),
            "product_name": state.get("product_name", ""),
            "problem_description": state.get("problem_description", ""),
            "customer_email": state.get("customer_email", ""),
            "customer_phone": state.get("customer_phone", "")
        })
        
        # Update state
        state["agent_response"] = response
        state["final_solution"] = response
        
        print("✅ Facebook protocol generated efficiently")
        
    except Exception as e:
        error_msg = f"Facebook agent error: {str(e)}"
        state["error"] = error_msg
        print(f"❌ Facebook agent failed: {e}")
    
    # Log execution
    if "execution_log" not in state:
        state["execution_log"] = []
        
    if not state.get("error"):
        state["execution_log"].append({
            "node": "Facebook Agent", 
            "status": "completed",
            "description": f"Retrieved relevant Facebook support documents, generated resolution protocol using hybrid RAG (FAISS + BM25)"
        })
    else:
        state["execution_log"].append({
            "node": "Facebook Agent",
            "status": "failed", 
            "description": f"Failed to process: {state.get('error', 'unknown error')}"
        })
    
    return state

def protocol_execution_node(state: CustomerCareState) -> CustomerCareState:
    """
    Final resolution delivery with separate protocol execution and customer reassurance
    """
    print("\n🎯 PROTOCOL EXECUTION NODE - Generating successful resolution outcome...")
    
    try:
        protocol = state.get("final_solution", "")
        customer_name = state.get("customer_name", "Customer")
        company_name = state.get("company_name", "").title()
        
        if not protocol:
            state["error"] = "No protocol found to execute"
            return state
        
        # Initialize LLM
        llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=150
        )
        
        # First: Generate protocol execution message (showing what agent is doing)
        execution_prompt = """
You are a {company_name} agent actively working on a customer's issue. Show what you're doing RIGHT NOW.

CUSTOMER: {customer_name}
ISSUE: {problem_description}
PRODUCT: {product_name}
PROTOCOL: {protocol}

INSTRUCTIONS:
- Use present tense: "I am checking...", "Now I'm processing...", "Currently verifying..."
- Show specific actions you're taking
- Maximum 4 sentences
- Sound professional and active

WHAT I'M DOING RIGHT NOW:"""

        # Second: Generate customer reassurance (final confirmation)
        reassurance_prompt = """
You are a {company_name} representative who has COMPLETED resolving the customer's issue.

CUSTOMER: {customer_name}
ISSUE: {problem_description}
PRODUCT: {product_name}
ACTIONS COMPLETED: {protocol_execution}

INSTRUCTIONS:
- Confirm the issue is RESOLVED
- Use past tense: "I have completed...", "Your issue has been resolved..."
- Maximum 3 sentences
- Include what happens next

FINAL CONFIRMATION:"""

        # Generate protocol execution
        execution_chain = ChatPromptTemplate.from_template(execution_prompt) | llm | StrOutputParser()
        protocol_execution = execution_chain.invoke({
            "company_name": company_name,
            "customer_name": customer_name,
            "problem_description": state.get("problem_description", ""),
            "product_name": state.get("product_name", ""),
            "protocol": protocol
        })
        
        # Generate customer reassurance  
        reassurance_chain = ChatPromptTemplate.from_template(reassurance_prompt) | llm | StrOutputParser()
        customer_reassurance = reassurance_chain.invoke({
            "company_name": company_name,
            "customer_name": customer_name,
            "problem_description": state.get("problem_description", ""),
            "product_name": state.get("product_name", ""),
            "protocol_execution": protocol_execution
        })
        
        # Update state with DIFFERENT messages
        state["protocol_execution"] = protocol_execution
        state["customer_reassurance"] = customer_reassurance
        
        # Show what agent is doing
        print("Processing...")
        print(f"Agent: {protocol_execution}")
        
        # Final confirmation with TTS
        print("\n🔊 Resolution complete. Converting message to speech...")
        speak_text(customer_reassurance)
        
        # Extract protocol steps as bullet points
        protocol_text = state.get("final_solution", "")
        protocol_steps = []
        
        # Try to extract numbered steps or bullet points
        lines = protocol_text.split('\n')
        for line in lines:
            line = line.strip()
            if (line and 
                (line[0].isdigit() or 
                 line.startswith('•') or 
                 line.startswith('-') or 
                 line.startswith('*') or
                 any(line.startswith(f"{i}.") for i in range(1, 10)))):
                # Clean up the step text
                clean_step = line
                if line[0].isdigit() and '.' in line:
                    clean_step = line.split('.', 1)[1].strip()
                elif line.startswith(('•', '-', '*')):
                    clean_step = line[1:].strip()
                protocol_steps.append(clean_step)
        
        # If no structured steps found, create them from the protocol
        if not protocol_steps and protocol_text:
            # Split by sentences and create steps
            sentences = [s.strip() for s in protocol_text.replace('.', '.\n').split('\n') if s.strip()]
            protocol_steps = sentences[:6]  # Limit to 6 key steps
        
        state["protocol_steps"] = protocol_steps
        
    except Exception as e:
        error_msg = f"Protocol execution error: {str(e)}"
        state["error"] = error_msg
        print(f"❌ Protocol execution failed: {e}")
    
    # Log execution
    if "execution_log" not in state:
        state["execution_log"] = []
        
    if not state.get("error"):
        state["execution_log"].append({
            "node": "Protocol Execution",
            "status": "completed",
            "description": f"Generated dual responses (process execution + customer reassurance), delivered via TTS, extracted {len(state.get('protocol_steps', []))} actionable steps"
        })
    else:
        state["execution_log"].append({
            "node": "Protocol Execution", 
            "status": "failed",
            "description": f"Failed to execute: {state.get('error', 'unknown error')}"
        })
    
    return state