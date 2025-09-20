import json
import assemblyai as aai
from typing import Dict, Any, Optional, List, TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
import os
from datetime import datetime
from dotenv import load_dotenv
import wave
import sounddevice as sd
import numpy as np
import pyttsx3
import threading
import time

# Load environment variables from .env file
load_dotenv()

# Enhanced TypedDict for Conversational Agent
class ConversationState(TypedDict):
    # Audio Processing
    audio_file_path: Optional[str]
    transcribed_text: Optional[str]
    transcription_confidence: Optional[float]
    
    # Customer Information (progressively filled)
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_email: Optional[str]
    customer_address: Optional[str]
    
    # Complaint Details (progressively filled)
    problem_description: Optional[str]
    problem_category: Optional[str]
    urgency_level: Optional[str]
    order_id: Optional[str]
    product_name: Optional[str]
    purchase_date: Optional[str]
    
    # Company Information
    company_name: Optional[str]
    company_confidence: Optional[float]
    
    # Conversation Management
    conversation_history: List[Dict[str, str]]  # [{"role": "agent"/"customer", "message": "..."}]
    current_question_count: int
    max_questions: int
    conversation_active: bool
    agent_current_question: Optional[str]
    waiting_for_response: bool
    
    # Processing Metadata
    processing_timestamp: Optional[str]
    processing_stage: str
    errors: List[str]
    
    # Final Output
    structured_output: Optional[Dict[str, Any]]

# Utility functions
def ensure_folders_exist():
    """Create necessary folders if they don't exist"""
    os.makedirs("audio_recordings", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("conversations", exist_ok=True)

def get_timestamped_filename(prefix: str, extension: str, folder: str) -> str:
    """Generate timestamped filename in specified folder"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"{prefix}_{timestamp}.{extension}")

# Text-to-Speech System
class TTSManager:
    def __init__(self):
        self.tts_available = False
        self.engine = None
        
        try:
            self.engine = pyttsx3.init()
            # Set properties for better speech quality
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
            
            # Try to set a female voice if available
            voices = self.engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            
            # Test TTS functionality
            self.engine.say("")
            self.engine.runAndWait()
            self.tts_available = True
            print("✅ Text-to-Speech system initialized successfully")
            
        except Exception as e:
            print(f"⚠️ Text-to-Speech not available: {e}")
            print("📝 Will use text-only mode (agent responses shown as text)")
            self.tts_available = False
    
    def speak(self, text: str):
        """Convert text to speech and play it, with fallback to text-only"""
        print(f"🤖 Agent: {text}")
        
        if self.tts_available and self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"⚠️ TTS error: {e}")
                print("💬 (Continuing in text-only mode)")
        else:
            print("💬 (Text-only mode - TTS not available)")
    
    def speak_async(self, text: str):
        """Convert text to speech asynchronously with fallback"""
        def speak_thread():
            self.speak(text)
        
        thread = threading.Thread(target=speak_thread)
        thread.daemon = True
        thread.start()
        return thread

# Enhanced Audio Recording for Conversation
class ConversationAudioRecorder:
    def __init__(self, sample_rate=44100, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
    
    def _save_audio(self, audio_data: np.ndarray, filename: str) -> str:
        """Save audio data to WAV file"""
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
        return filename
    
    def record_response(self, prompt_text: str = "Please speak your response:") -> str:
        """Record customer response with better UX"""
        filename = get_timestamped_filename("customer_response", "wav", "audio_recordings")
        
        print(f"\n🎤 {prompt_text}")
        print("Recording will auto-stop after 2 seconds of silence...")
        
        chunk_duration = 0.1  # 100ms chunks
        chunk_size = int(self.sample_rate * chunk_duration)
        audio_chunks = []
        silence_chunks = 0
        max_silence_chunks = 20  # 2 seconds of silence
        min_recording_chunks = 10  # Minimum 1 second of recording
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16,
                blocksize=chunk_size
            ) as stream:
                print("🔴 Recording... Speak now!")
                while True:
                    chunk, overflowed = stream.read(chunk_size)
                    if overflowed:
                        print("⚠️ Audio buffer overflowed")
                    
                    audio_chunks.append(chunk)
                    
                    # Check if chunk is mostly silence
                    chunk_volume = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                    
                    if chunk_volume < 50:  # Silence threshold
                        silence_chunks += 1
                    else:
                        silence_chunks = 0
                    
                    # Stop if we have enough silence and minimum recording
                    if silence_chunks >= max_silence_chunks and len(audio_chunks) >= min_recording_chunks:
                        print("⏹️ Silence detected. Stopping recording...")
                        break
                    
                    # Safety limit - max 30 seconds
                    if len(audio_chunks) > 3000:  # 30 seconds
                        print("⏹️ Maximum recording time reached.")
                        break
            
            # Combine all chunks and save
            if audio_chunks:
                audio_data = np.concatenate(audio_chunks, axis=0)
                
                # Apply audio boost if needed
                max_amplitude = np.max(np.abs(audio_data))
                if max_amplitude < 1000:
                    boost_factor = min(5.0, 5000.0 / max(max_amplitude, 1))
                    audio_data = (audio_data * boost_factor).astype(np.int16)
                    print(f"🔊 Applied {boost_factor:.1f}x audio boost")
                
                self._save_audio(audio_data, filename)
                print(f"✅ Response recorded: {filename}")
                return filename
            
        except KeyboardInterrupt:
            print("\n❌ Recording cancelled by user")
            return None
        except Exception as e:
            print(f"❌ Recording error: {str(e)}")
            return None

# Speech-to-Text for Conversation
class ConversationSTT:
    def __init__(self, api_key: str):
        aai.settings.api_key = api_key
        self.config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.universal,
            language_code="en"
        )
        self.transcriber = aai.Transcriber()
    
    def transcribe_response(self, file_path: str) -> Dict[str, Any]:
        """Transcribe customer response"""
        try:
            if not os.path.exists(file_path):
                raise Exception(f"Audio file not found: {file_path}")
            
            print("🔄 Transcribing your response...")
            transcript = self.transcriber.transcribe(file_path, config=self.config)
            
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")
            
            text_result = transcript.text if transcript.text else "[No speech detected]"
            
            return {
                "text": text_result,
                "confidence": transcript.confidence if hasattr(transcript, 'confidence') else 0.95
            }
        except Exception as e:
            raise Exception(f"Transcription error: {str(e)}")

# Intelligent Question Generator
def generate_next_question(api_key: str, state: ConversationState) -> str:
    """Generate the next best question based on current conversation state"""
    
    # Customer service agent persona prompt
    agent_persona = """
    You are an exceptional customer service agent with years of experience. You are:
    - Empathetic and understanding
    - Efficient and goal-oriented
    - Professional yet friendly
    - Skilled at asking the right questions to solve problems quickly
    
    Your goal is to gather essential information to help resolve the customer's complaint in maximum 3 questions.
    """
    
    # Analyze what information we still need
    missing_info = []
    current_data = {}
    
    # Check what we have and what we need
    if not state.get("customer_name"):
        missing_info.append("customer name")
    else:
        current_data["name"] = state["customer_name"]
        
    if not state.get("problem_description"):
        missing_info.append("problem description")
    else:
        current_data["problem"] = state["problem_description"]
        
    if not state.get("order_id") and not state.get("product_name"):
        missing_info.append("order/product details")
    else:
        if state.get("order_id"):
            current_data["order_id"] = state["order_id"]
        if state.get("product_name"):
            current_data["product"] = state["product_name"]
    
    if not state.get("customer_phone") and not state.get("customer_email"):
        missing_info.append("contact information")
    else:
        if state.get("customer_phone"):
            current_data["phone"] = state["customer_phone"]
        if state.get("customer_email"):
            current_data["email"] = state["customer_email"]
    
    # Build conversation context
    conversation_context = ""
    for msg in state.get("conversation_history", []):
        role = "Agent" if msg["role"] == "agent" else "Customer"
        conversation_context += f"{role}: {msg['message']}\n"
    
    # Generate question prompt
    current_data_str = json.dumps(current_data, indent=2) if current_data else "None collected yet"
    missing_info_str = ', '.join(missing_info) if missing_info else 'Most essential information collected'
    
    question_prompt = f"""
    {agent_persona}
    
    CONVERSATION SO FAR:
    {conversation_context}
    
    CURRENT CUSTOMER DATA COLLECTED:
    {current_data_str}
    
    MISSING INFORMATION:
    {missing_info_str}
    
    QUESTION COUNT: {state.get('current_question_count', 0)}/3
    
    Generate the next most important question to ask the customer. Consider:
    1. What's the most critical missing information for resolving their issue?
    2. Keep questions natural and conversational
    3. Be empathetic and professional
    4. If this is question 3/3, focus on the most essential details for resolution
    5. If you have enough info, ask a clarifying question to ensure resolution
    
    Respond with ONLY the question to ask, nothing else. Keep it under 25 words.
    """
    
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=100,
        groq_api_key=api_key
    )
    
    response = llm.invoke(question_prompt)
    
    return response.content.strip()

# Extract information from customer response
def extract_info_from_response(api_key: str, question: str, response: str, current_state: ConversationState) -> Dict[str, Any]:
    """Extract relevant information from customer response"""
    
    extraction_prompt = f"""
    You are an expert at extracting customer information from conversations.
    
    PREVIOUS QUESTION ASKED: {question}
    CUSTOMER RESPONSE: {response}
    
    CURRENT CUSTOMER DATA:
    - Name: {current_state.get('customer_name', 'Unknown')}
    - Phone: {current_state.get('customer_phone', 'Unknown')}
    - Email: {current_state.get('customer_email', 'Unknown')}
    - Problem: {current_state.get('problem_description', 'Unknown')}
    - Order ID: {current_state.get('order_id', 'Unknown')}
    - Product: {current_state.get('product_name', 'Unknown')}
    - Company: {current_state.get('company_name', 'Unknown')}
    
    Extract any new information from the customer's response and return it as JSON.
    Only include fields that can be clearly identified. Use null for unclear/missing values.
    
    Return JSON in this exact format:
    {
        "customer_name": "extracted name or null",
        "customer_phone": "extracted phone or null",
        "customer_email": "extracted email or null", 
        "problem_description": "extracted/updated problem description or null",
        "problem_category": "delivery/product_quality/payment/refund/customer_service/other or null",
        "urgency_level": "low/medium/high/critical or null",
        "order_id": "extracted order ID or null",
        "product_name": "extracted product name or null",
        "purchase_date": "extracted date or null",
        "company_name": "amazon/flipkart/other or null",
        "company_confidence": 0.0
    }
    """
    
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=500,
        groq_api_key=api_key
    )
    
    response_extraction = llm.invoke(extraction_prompt)
    
    try:
        return json.loads(response_extraction.content.strip())
    except json.JSONDecodeError:
        print(f"⚠️ Failed to parse extraction result: {response_extraction.content}")
        return {}

# LangGraph Nodes for Conversation Flow
def conversation_start_node(state: ConversationState) -> Dict[str, Any]:
    """Start the conversation with initial greeting"""
    print("DEBUG: Starting conversation")
    
    # Initialize TTS
    tts = TTSManager()
    
    # Initial greeting
    greeting = "Hello! I'm here to help you with your complaint today. To get started, could you please tell me your name and briefly describe the issue you're experiencing?"
    
    tts.speak(greeting)
    
    updates = {
        "processing_stage": "conversation_started",
        "conversation_active": True,
        "current_question_count": 1,
        "agent_current_question": greeting,
        "waiting_for_response": True,
        "conversation_history": [{"role": "agent", "message": greeting}],
        "processing_timestamp": datetime.now().isoformat()
    }
    
    return updates

def customer_response_node(state: ConversationState) -> Dict[str, Any]:
    """Record and process customer response"""
    print("DEBUG: Processing customer response")
    
    updates = {"processing_stage": "processing_response"}
    
    try:
        # Record customer response
        recorder = ConversationAudioRecorder()
        audio_file = recorder.record_response("Please respond to the question:")
        
        if not audio_file:
            updates["errors"] = state.get("errors", []) + ["Failed to record customer response"]
            updates["processing_stage"] = "failed"
            return updates
        
        # Transcribe response
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            updates["errors"] = state.get("errors", []) + ["ASSEMBLYAI_API_KEY not found"]
            updates["processing_stage"] = "failed"
            return updates
        
        stt = ConversationSTT(api_key)
        transcription = stt.transcribe_response(audio_file)
        
        customer_text = transcription["text"]
        print(f"👤 Customer: {customer_text}")
        
        # Add to conversation history
        conversation_history = state.get("conversation_history", [])
        conversation_history.append({"role": "customer", "message": customer_text})
        
        # Extract information from response (only if we have meaningful text)
        if customer_text and customer_text != "[No speech detected]":
            groq_api_key = os.getenv("GROQ_API_KEY")
            if groq_api_key:
                try:
                    current_question = state.get("agent_current_question", "")
                    extracted_info = extract_info_from_response(groq_api_key, current_question, customer_text, state)
                    
                    # Update state with extracted information
                    for key, value in extracted_info.items():
                        if value and value != "null" and value is not None:
                            updates[key] = value
                except Exception as e:
                    print(f"⚠️ Info extraction error: {e}")
                    # Continue without extraction
        
        updates.update({
            "transcribed_text": customer_text,
            "transcription_confidence": transcription["confidence"],
            "conversation_history": conversation_history,
            "waiting_for_response": False,
            "processing_stage": "response_processed"
        })
        
    except Exception as e:
        error_msg = f"Customer response error: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        updates["errors"] = state.get("errors", []) + [error_msg]
        updates["processing_stage"] = "failed"
    
    return updates

def next_question_node(state: ConversationState) -> Dict[str, Any]:
    """Generate and ask the next question"""
    print("DEBUG: Generating next question")
    
    updates = {"processing_stage": "generating_question"}
    
    try:
        current_count = state.get("current_question_count", 0)
        
        # Check if we've reached the question limit
        if current_count >= state.get("max_questions", 3):
            updates["processing_stage"] = "conversation_complete"
            updates["conversation_active"] = False
            return updates
        
        # Generate next question
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            updates["errors"] = state.get("errors", []) + ["GROQ_API_KEY not found"]
            updates["processing_stage"] = "failed"
            return updates
        
        next_question = generate_next_question(groq_api_key, state)
        
        # Speak the question
        tts = TTSManager()
        tts.speak(next_question)
        
        # Update conversation history
        conversation_history = state.get("conversation_history", [])
        conversation_history.append({"role": "agent", "message": next_question})
        
        updates.update({
            "agent_current_question": next_question,
            "current_question_count": current_count + 1,
            "waiting_for_response": True,
            "conversation_history": conversation_history,
            "processing_stage": "waiting_for_response"
        })
        
    except Exception as e:
        error_msg = f"Question generation error: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        updates["errors"] = state.get("errors", []) + [error_msg]
        updates["processing_stage"] = "failed"
    
    return updates

def conversation_complete_node(state: ConversationState) -> Dict[str, Any]:
    """Complete the conversation and generate final output"""
    print("DEBUG: Completing conversation")
    
    updates = {"processing_stage": "finalizing"}
    
    try:
        # Generate final summary
        tts = TTSManager()
        final_message = "Thank you for providing that information. I've recorded all the details about your complaint and we'll work on resolving this for you as soon as possible."
        tts.speak(final_message)
        
        # Add final message to history
        conversation_history = state.get("conversation_history", [])
        conversation_history.append({"role": "agent", "message": final_message})
        
        # Create structured output
        structured_data = {
            "metadata": {
                "processing_timestamp": state.get("processing_timestamp"),
                "conversation_completed": datetime.now().isoformat(),
                "total_questions": state.get("current_question_count", 0),
                "errors": state.get("errors", [])
            },
            "conversation": {
                "full_history": conversation_history,
                "total_exchanges": len([msg for msg in conversation_history if msg["role"] == "customer"])
            },
            "customer_info": {
                "name": state.get("customer_name"),
                "phone": state.get("customer_phone"),
                "email": state.get("customer_email"),
                "address": state.get("customer_address")
            },
            "complaint_details": {
                "description": state.get("problem_description"),
                "category": state.get("problem_category"),
                "urgency_level": state.get("urgency_level"),
                "order_id": state.get("order_id"),
                "product_name": state.get("product_name"),
                "purchase_date": state.get("purchase_date")
            },
            "company_info": {
                "company_name": state.get("company_name"),
                "confidence": state.get("company_confidence", 0.0)
            },
            "status": "conversation_completed"
        }
        
        # Save conversation
        conversation_file = get_timestamped_filename("conversation", "json", "conversations")
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Conversation saved: {conversation_file}")
        
        updates.update({
            "structured_output": structured_data,
            "conversation_history": conversation_history,
            "processing_stage": "completed",
            "conversation_active": False
        })
        
    except Exception as e:
        error_msg = f"Conversation completion error: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        updates["errors"] = state.get("errors", []) + [error_msg]
        updates["processing_stage"] = "failed"
    
    return updates

# Conditional function for conversation flow
def should_continue_conversation(state: ConversationState) -> str:
    """Determine the next step in conversation"""
    stage = state.get("processing_stage", "")
    errors = state.get("errors", [])
    conversation_active = state.get("conversation_active", False)
    current_count = state.get("current_question_count", 0)
    max_questions = state.get("max_questions", 3)
    
    if errors:
        return "end"
    elif stage == "conversation_started":
        return "customer_response"
    elif stage == "response_processed":
        if current_count >= max_questions:
            return "complete_conversation"
        else:
            return "next_question"
    elif stage == "waiting_for_response":
        return "customer_response"
    elif stage == "conversation_complete" or stage == "completed":
        return "complete_conversation"
    else:
        return "end"

# Build the Conversational LangGraph
def create_conversation_graph():
    """Create the conversational workflow graph"""
    workflow = StateGraph(ConversationState)
    
    # Add nodes
    workflow.add_node("start_conversation", conversation_start_node)
    workflow.add_node("customer_response", customer_response_node)
    workflow.add_node("next_question", next_question_node)
    workflow.add_node("complete_conversation", conversation_complete_node)
    
    # Set entry point
    workflow.set_entry_point("start_conversation")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "start_conversation",
        should_continue_conversation,
        {
            "customer_response": "customer_response",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "customer_response",
        should_continue_conversation,
        {
            "next_question": "next_question",
            "complete_conversation": "complete_conversation",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "next_question",
        should_continue_conversation,
        {
            "customer_response": "customer_response",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "complete_conversation",
        should_continue_conversation,
        {
            "end": END
        }
    )
    
    return workflow.compile()

# Main conversation function
def start_conversation(max_questions: int = 3) -> Optional[Dict[str, Any]]:
    """Start a conversational complaint processing session"""
    
    # Initialize state
    initial_state: ConversationState = {
        "audio_file_path": None,
        "transcribed_text": None,
        "transcription_confidence": None,
        "customer_name": None,
        "customer_phone": None,
        "customer_email": None,
        "customer_address": None,
        "problem_description": None,
        "problem_category": None,
        "urgency_level": None,
        "order_id": None,
        "product_name": None,
        "purchase_date": None,
        "company_name": None,
        "company_confidence": None,
        "conversation_history": [],
        "current_question_count": 0,
        "max_questions": max_questions,
        "conversation_active": False,
        "agent_current_question": None,
        "waiting_for_response": False,
        "processing_timestamp": datetime.now().isoformat(),
        "processing_stage": "initialized",
        "errors": [],
        "structured_output": None
    }
    
    # Create and run the conversation graph
    app = create_conversation_graph()
    final_state = app.invoke(initial_state)
    
    return final_state.get("structured_output")

def main():
    """Main execution function for conversational agent"""
    # Ensure folders exist
    ensure_folders_exist()
    
    # Check API keys
    if not os.getenv("ASSEMBLYAI_API_KEY"):
        print("❌ Error: ASSEMBLYAI_API_KEY not found in environment variables")
        return
    
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY not found in environment variables")
        return
    
    print("✅ Using Groq API for conversation intelligence")
    print("✅ Using AssemblyAI for speech recognition")
    
    try:
        print("\n" + "="*60)
        print("🤖 INTELLIGENT CUSTOMER SERVICE AGENT")
        print("🗣️  Two-way Conversational Complaint Processing")
        print("="*60)
        
        print("\nℹ️  Instructions:")
        print("   • The agent will ask up to 3 intelligent questions")
        print("   • Speak clearly after each question")  
        print("   • Recording stops automatically after 2 seconds of silence")
        print("   • Press Ctrl+C anytime to exit")
        
        input("\nPress Enter to start the conversation...")
        
        # Start the conversation
        result = start_conversation(max_questions=3)
        
        if result:
            print("\n" + "="*60)
            print("✅ CONVERSATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\n📋 Final Summary:")
            print(json.dumps(result, indent=2))
        else:
            print("\n❌ Conversation failed. Please check the error messages above.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Conversation ended by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()