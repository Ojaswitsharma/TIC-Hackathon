import json
import assemblyai as aai
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
import openai
import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv
import pyaudio
import wave
import sounddevice as sd
import numpy as np

# Load environment variables from .env file
load_dotenv()

# State Schema
class ComplaintState(BaseModel):
    # Audio Processing
    audio_file_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    transcription_confidence: Optional[float] = None
    
    # Customer Information
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    
    # Complaint Details
    problem_description: Optional[str] = None
    problem_category: Optional[str] = None
    urgency_level: Optional[str] = None
    order_id: Optional[str] = None
    product_name: Optional[str] = None
    purchase_date: Optional[str] = None
    
    # Company Information
    company_name: Optional[str] = None  # amazon or flipkart
    company_confidence: Optional[float] = None
    
    # Processing Metadata
    processing_timestamp: Optional[str] = None
    processing_stage: str = "initialized"
    errors: list = []
    
    # Final Output
    structured_output: Optional[Dict[str, Any]] = None

# Audio Recording Class
class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
    
    def record_audio(self, duration=10, filename="recorded_audio.wav"):
        """Record audio from microphone for specified duration"""
        print(f"Recording audio for {duration} seconds... Press Ctrl+C to stop early")
        print("Speak now!")
        
        try:
            # Record audio using sounddevice
            audio_data = sd.rec(
                int(duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=self.channels,
                dtype=np.int16
            )
            
            # Wait for recording to complete
            sd.wait()
            
            # Save to WAV file
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 2 bytes for int16
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())
            
            print(f"Recording saved to: {filename}")
            return filename
            
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
            # Save what we have recorded so far
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                if 'audio_data' in locals():
                    wf.writeframes(audio_data.tobytes())
            return filename
        except Exception as e:
            print(f"Recording error: {str(e)}")
            return None
    
    def record_until_silence(self, filename="recorded_audio.wav", silence_threshold=0.01, silence_duration=2):
        """Record audio until silence is detected"""
        print("Recording... Speak now! (Will stop after 2 seconds of silence)")
        
        chunk_duration = 0.1  # 100ms chunks
        chunk_size = int(self.sample_rate * chunk_duration)
        audio_chunks = []
        silence_chunks = 0
        max_silence_chunks = int(silence_duration / chunk_duration)
        
        try:
            # Start recording in chunks
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16
            )
            
            with stream:
                print("Recording started...")
                while True:
                    # Record a small chunk
                    chunk = sd.rec(
                        chunk_size,
                        samplerate=self.sample_rate,
                        channels=self.channels,
                        dtype=np.int16
                    )
                    sd.wait()
                    
                    audio_chunks.append(chunk)
                    
                    # Check if chunk is mostly silence
                    chunk_volume = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                    
                    if chunk_volume < silence_threshold:
                        silence_chunks += 1
                    else:
                        silence_chunks = 0
                    
                    # Stop if we have enough silence
                    if silence_chunks >= max_silence_chunks:
                        print("Silence detected. Stopping recording...")
                        break
            
            # Combine all chunks
            if audio_chunks:
                audio_data = np.concatenate(audio_chunks, axis=0)
                
                # Save to WAV file
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data.tobytes())
                
                print(f"Recording saved to: {filename}")
                return filename
            
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
            if audio_chunks:
                audio_data = np.concatenate(audio_chunks, axis=0)
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data.tobytes())
                return filename
        except Exception as e:
            print(f"Recording error: {str(e)}")
            return None

# Free Speech-to-Text using AssemblyAI SDK (Free tier: 100 minutes/month)
import assemblyai as aai

class SpeechToTextProcessor:
    def __init__(self, api_key: str):
        aai.settings.api_key = api_key
        # Configure transcription settings
        self.config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.universal,
            language_detection=True
        )
        self.transcriber = aai.Transcriber(self.config)
    
    def transcribe_audio(self, file_path: str) -> Dict[str, Any]:
        """Transcribe audio using AssemblyAI SDK"""
        try:
            # Transcribe the audio file
            transcript = self.transcriber.transcribe(file_path)
            
            # Check for errors
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")
            
            return {
                "text": transcript.text,
                "confidence": transcript.confidence if hasattr(transcript, 'confidence') else 0.95
            }
        except Exception as e:
            raise Exception(f"Transcription error: {str(e)}")

# LLM Client (supports both OpenAI and Google Gemini)
class LLMClient:
    def __init__(self, api_key: str, provider: str = "google", base_url: str = "https://api.openai.com/v1"):
        self.provider = provider
        
        if provider == "google":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        elif provider == "openai":
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        else:
            raise ValueError("Provider must be 'google' or 'openai'")
    
    def analyze_text(self, prompt: str, text: str) -> str:
        if self.provider == "google":
            # Combine system prompt and user text for Gemini
            full_prompt = f"{prompt}\n\nText to analyze:\n{text}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048,
                )
            )
            return response.text
            
        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content

# Node Functions
def speech_to_text_node(state: ComplaintState) -> ComplaintState:
    """Node 1: Convert speech to text"""
    try:
        state.processing_stage = "speech_to_text"
        state.processing_timestamp = datetime.now().isoformat()
        
        if not state.audio_file_path:
            state.errors.append("No audio file path provided")
            return state
        
        # Initialize AssemblyAI client
        stt_processor = SpeechToTextProcessor(os.getenv("ASSEMBLYAI_API_KEY"))
        
        # Transcribe audio directly
        result = stt_processor.transcribe_audio(state.audio_file_path)
        
        # Update state
        state.transcribed_text = result["text"]
        state.transcription_confidence = result["confidence"]
        state.processing_stage = "speech_to_text_completed"
        
        # Print the transcribed text for verification
        print(f"\n=== Speech-to-Text Result ===")
        print(f"Transcribed Text: {state.transcribed_text}")
        print(f"Confidence: {state.transcription_confidence:.2f}")
        print("=" * 50)
        
    except Exception as e:
        state.errors.append(f"Speech-to-text error: {str(e)}")
    
    return state

def semantic_analysis_node(state: ComplaintState) -> ComplaintState:
    """Node 2: Extract customer data and problem details"""
    try:
        state.processing_stage = "semantic_analysis"
        
        if not state.transcribed_text:
            state.errors.append("No transcribed text available for analysis")
            return state
        
        # Use Google API if available, fallback to OpenAI
        google_api_key = os.getenv("GOOGLE_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if google_api_key:
            llm_client = LLMClient(google_api_key, provider="google")
        elif openai_api_key:
            llm_client = LLMClient(openai_api_key, provider="openai")
        else:
            raise Exception("No API key found. Please set GOOGLE_API_KEY or OPENAI_API_KEY in your .env file")
        
        # Semantic analysis prompt
        analysis_prompt = """
        You are an expert at extracting customer information from complaint text. 
        Extract the following information from the customer complaint:
        
        1. Customer Information:
           - Name, Phone, Email, Address (if mentioned)
        
        2. Problem Details:
           - Problem description (summarize the main issue)
           - Problem category (delivery, product quality, payment, refund, etc.)
           - Urgency level (low, medium, high, critical)
           - Order ID (if mentioned)
           - Product name (if mentioned)
           - Purchase date (if mentioned)
        
        3. Company Identification:
           - Identify if this is about Amazon or Flipkart
           - Provide confidence level (0.0 to 1.0)
        
        Return the information in this exact JSON format:
        {
            "customer_name": "extracted name or null",
            "customer_phone": "extracted phone or null",
            "customer_email": "extracted email or null",
            "customer_address": "extracted address or null",
            "problem_description": "concise problem summary",
            "problem_category": "category",
            "urgency_level": "urgency",
            "order_id": "extracted order id or null",
            "product_name": "extracted product or null",
            "purchase_date": "extracted date or null",
            "company_name": "amazon or flipkart",
            "company_confidence": 0.95
        }
        """
        
        # Get analysis
        analysis_result = llm_client.analyze_text(analysis_prompt, state.transcribed_text)
        
        # Parse JSON response
        try:
            parsed_data = json.loads(analysis_result)
            
            # Update state with extracted information
            state.customer_name = parsed_data.get("customer_name")
            state.customer_phone = parsed_data.get("customer_phone")
            state.customer_email = parsed_data.get("customer_email")
            state.customer_address = parsed_data.get("customer_address")
            state.problem_description = parsed_data.get("problem_description")
            state.problem_category = parsed_data.get("problem_category")
            state.urgency_level = parsed_data.get("urgency_level")
            state.order_id = parsed_data.get("order_id")
            state.product_name = parsed_data.get("product_name")
            state.purchase_date = parsed_data.get("purchase_date")
            state.company_name = parsed_data.get("company_name")
            state.company_confidence = parsed_data.get("company_confidence")
            
            state.processing_stage = "semantic_analysis_completed"
            
        except json.JSONDecodeError as e:
            state.errors.append(f"Failed to parse semantic analysis result: {str(e)}")
    
    except Exception as e:
        state.errors.append(f"Semantic analysis error: {str(e)}")
    
    return state

def structured_output_node(state: ComplaintState) -> ComplaintState:
    """Node 3: Generate final structured JSON output"""
    try:
        state.processing_stage = "generating_structured_output"
        
        # Create comprehensive structured output
        structured_data = {
            "complaint_id": f"COMP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "processing_info": {
                "timestamp": state.processing_timestamp,
                "processing_stage": state.processing_stage,
                "transcription_confidence": state.transcription_confidence,
                "errors": state.errors
            },
            "audio_processing": {
                "original_audio_path": state.audio_file_path,
                "transcribed_text": state.transcribed_text,
                "transcription_confidence": state.transcription_confidence
            },
            "customer_information": {
                "name": state.customer_name,
                "phone": state.customer_phone,
                "email": state.customer_email,
                "address": state.customer_address
            },
            "complaint_details": {
                "description": state.problem_description,
                "category": state.problem_category,
                "urgency_level": state.urgency_level,
                "order_id": state.order_id,
                "product_name": state.product_name,
                "purchase_date": state.purchase_date
            },
            "company_info": {
                "company_name": state.company_name,
                "confidence": state.company_confidence
            },
            "status": "processed" if not state.errors else "processed_with_errors"
        }
        
        # Update state
        state.structured_output = structured_data
        state.processing_stage = "completed"
        
        # Save to JSON file
        output_filename = f"complaint_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        
        print(f"Structured output saved to: {output_filename}")
    
    except Exception as e:
        state.errors.append(f"Structured output error: {str(e)}")
    
    return state

# Build the LangGraph workflow
def create_complaint_processing_graph():
    # Create the graph
    workflow = StateGraph(ComplaintState)
    
    # Add nodes
    workflow.add_node("speech_to_text", speech_to_text_node)
    workflow.add_node("semantic_analysis", semantic_analysis_node)
    workflow.add_node("structured_output", structured_output_node)
    
    # Define edges
    workflow.add_edge("speech_to_text", "semantic_analysis")
    workflow.add_edge("semantic_analysis", "structured_output")
    workflow.add_edge("structured_output", END)
    
    # Set entry point
    workflow.set_entry_point("speech_to_text")
    
    return workflow.compile()

# Main execution function
def process_complaint(audio_file_path: str) -> Dict[str, Any]:
    """Process a customer complaint from audio file"""
    
    # Initialize state
    initial_state = ComplaintState(
        audio_file_path=audio_file_path,
        processing_timestamp=datetime.now().isoformat()
    )
    
    # Create and run the graph
    app = create_complaint_processing_graph()
    final_state = app.invoke(initial_state)
    
    return final_state.structured_output

# Example usage
if __name__ == "__main__":
    # Environment variables are loaded from .env file via load_dotenv()
    # Make sure to create a .env file with:
    # ASSEMBLYAI_API_KEY=a84d783a19304237a48db0004774b22a
    # GOOGLE_API_KEY=your_google_api_key_here (preferred)
    # OR OPENAI_API_KEY=your_openai_api_key_here
    
    # Check if API keys are loaded
    if not os.getenv("ASSEMBLYAI_API_KEY"):
        print("Error: ASSEMBLYAI_API_KEY not found in environment variables")
        print("Please create a .env file with your API key")
        exit(1)
    
    # Check for LLM API keys
    google_api_key = os.getenv("GOOGLE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if google_api_key:
        print("Using Google Gemini API for text analysis")
    elif openai_api_key:
        print("Using OpenAI API for text analysis")
    else:
        print("Error: No LLM API key found. Please set GOOGLE_API_KEY or OPENAI_API_KEY in your .env file")
        exit(1)
    
    # Record audio from microphone
    try:
        print("=== Customer Complaint Audio Recording System ===")
        print("\nChoose recording method:")
        print("1. Fixed duration recording (10 seconds)")
        print("2. Auto-stop on silence (recommended)")
        print("3. Use existing audio file")
        
        choice = input("\nEnter your choice (1/2/3): ").strip()
        
        audio_path = None
        
        if choice == "1":
            # Fixed duration recording
            duration = input("Enter recording duration in seconds (default 10): ").strip()
            duration = int(duration) if duration.isdigit() else 10
            
            recorder = AudioRecorder()
            audio_path = recorder.record_audio(duration, "customer_complaint.wav")
            
        elif choice == "2":
            # Auto-stop on silence
            recorder = AudioRecorder()
            audio_path = recorder.record_until_silence("customer_complaint.wav")
            
        elif choice == "3":
            # Use existing file
            audio_path = input("Enter path to audio file: ").strip()
            if not os.path.exists(audio_path):
                print(f"File not found: {audio_path}")
                exit(1)
        else:
            print("Invalid choice. Using auto-stop recording...")
            recorder = AudioRecorder()
            audio_path = recorder.record_until_silence("customer_complaint.wav")
        
        if not audio_path:
            print("Failed to record audio")
            exit(1)
        
        print(f"\n=== Processing Audio File: {audio_path} ===")
        
        # Process the complaint
        result = process_complaint(audio_path)
        
        if result:
            print("\n=== Processing Completed Successfully! ===")
            
            # Save result to JSON file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"complaint_output_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"Results saved to: {output_file}")
            print("\n=== Summary ===")
            print(json.dumps(result, indent=2))
        else:
            print("Processing failed.")
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {str(e)}")
