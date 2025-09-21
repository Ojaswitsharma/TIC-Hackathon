import json
import assemblyai as aai
from typing import Dict, Any, Optional, List, TypedDict
from langgraph.graph import StateGraph, END
import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv
import wave
import sounddevice as sd
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Proper TypedDict for LangGraph compatibility
class ComplaintState(TypedDict):
    # Audio Processing
    audio_file_path: Optional[str]
    transcribed_text: Optional[str]
    transcription_confidence: Optional[float]
    
    # Customer Information
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_email: Optional[str]
    customer_address: Optional[str]
    
    # Complaint Details
    problem_description: Optional[str]
    problem_category: Optional[str]
    urgency_level: Optional[str]
    order_id: Optional[str]
    product_name: Optional[str]
    purchase_date: Optional[str]
    
    # Company Information
    company_name: Optional[str]
    company_confidence: Optional[float]
    
    # Processing Metadata
    processing_timestamp: Optional[str]
    processing_stage: str
    errors: List[str]
    
    # Final Output
    structured_output: Optional[Dict[str, Any]]

# Utility functions for folder management
def ensure_folders_exist():
    """Create necessary folders if they don't exist"""
    os.makedirs("audio_recordings", exist_ok=True)
    os.makedirs("output", exist_ok=True)

def get_timestamped_filename(prefix: str, extension: str, folder: str) -> str:
    """Generate timestamped filename in specified folder"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"{prefix}_{timestamp}.{extension}")

# Improved Audio Recording Class
class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
    
    def _save_audio(self, audio_data: np.ndarray, filename: str) -> str:
        """Save audio data to WAV file"""
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 2 bytes for int16
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
        return filename
    
    def record_audio(self, duration=10) -> str:
        """Record audio from microphone for specified duration"""
        filename = get_timestamped_filename("complaint", "wav", "audio_recordings")
        
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
            
            # Check if we actually recorded something
            max_amplitude = np.max(np.abs(audio_data))
            avg_amplitude = np.mean(np.abs(audio_data))
            print(f"Audio recording stats: Max amplitude: {max_amplitude}, Avg amplitude: {avg_amplitude:.2f}")
            
            if max_amplitude < 100:  # Very quiet recording
                print("WARNING: Recording seems very quiet. Applying audio boost...")
                # Boost the audio by a factor (be careful not to clip)
                boost_factor = min(10.0, 1000.0 / max(max_amplitude, 1))
                audio_data = (audio_data * boost_factor).astype(np.int16)
                print(f"Applied {boost_factor:.1f}x boost to audio")
            
            self._save_audio(audio_data, filename)
            print(f"Recording saved to: {filename}")
            return filename
            
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
            if 'audio_data' in locals():
                self._save_audio(audio_data, filename)
            return filename
        except Exception as e:
            raise Exception(f"Recording error: {str(e)}")
    
    def record_until_silence(self, silence_threshold=0.01, silence_duration=2) -> str:
        """Record audio until silence is detected - properly implemented"""
        filename = get_timestamped_filename("complaint", "wav", "audio_recordings")
        
        print("Recording... Speak now! (Will stop after 2 seconds of silence)")
        
        chunk_duration = 0.1  # 100ms chunks
        chunk_size = int(self.sample_rate * chunk_duration)
        audio_chunks = []
        silence_chunks = 0
        max_silence_chunks = int(silence_duration / chunk_duration)
        
        try:
            # Properly use InputStream
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16,
                blocksize=chunk_size
            ) as stream:
                print("Recording started...")
                while True:
                    chunk, overflowed = stream.read(chunk_size)
                    if overflowed:
                        print("Warning: Audio buffer overflowed")
                    
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
            
            # Combine all chunks and save
            if audio_chunks:
                audio_data = np.concatenate(audio_chunks, axis=0)
                self._save_audio(audio_data, filename)
                print(f"Recording saved to: {filename}")
                return filename
            
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
            if audio_chunks:
                audio_data = np.concatenate(audio_chunks, axis=0)
                self._save_audio(audio_data, filename)
                return filename
        except Exception as e:
            raise Exception(f"Recording error: {str(e)}")

# Speech-to-Text Processor
class SpeechToTextProcessor:
    def __init__(self, api_key: str):
        aai.settings.api_key = api_key
        self.config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.universal,
            language_code="en"  # Use specific language instead of detection
        )
        self.transcriber = aai.Transcriber()
    
    def transcribe_audio(self, file_path: str) -> Dict[str, Any]:
        """Transcribe audio using AssemblyAI SDK"""
        try:
            # Check if file exists and has content
            if not os.path.exists(file_path):
                raise Exception(f"Audio file not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size < 1000:  # Less than 1KB likely means no audio
                raise Exception(f"Audio file appears to be empty or too small: {file_size} bytes")
            
            print(f"Transcribing audio file: {file_path} ({file_size} bytes)")
            
            # Use the config when transcribing
            transcript = self.transcriber.transcribe(file_path, config=self.config)
            
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")
            
            # Check if we got any text (but be forgiving)
            text_result = transcript.text if transcript.text else "[No speech detected - continuing with empty transcription]"
            
            return {
                "text": text_result,
                "confidence": transcript.confidence if hasattr(transcript, 'confidence') else 0.95
            }
        except Exception as e:
            raise Exception(f"Transcription error: {str(e)}")

# LLM Client - simplified and focused
def analyze_with_gemini(api_key: str, prompt: str, text: str) -> str:
    """Direct function to analyze text with Google Gemini"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    full_prompt = f"{prompt}\n\nText to analyze:\n{text}"
    
    response = model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=2048,
        )
    )
    return response.text

# Functional Node Functions (return only state updates)
def speech_to_text_node(state: ComplaintState) -> Dict[str, Any]:
    """Node 1: Convert speech to text - returns only updates"""
    print("DEBUG: Entering speech_to_text_node")
    updates = {
        "processing_stage": "speech_to_text",
        "processing_timestamp": datetime.now().isoformat()
    }
    
    try:
        if not state.get("audio_file_path"):
            updates["errors"] = state.get("errors", []) + ["No audio file path provided"]
            updates["processing_stage"] = "failed"
            return updates
        
        # Initialize AssemblyAI client
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            updates["errors"] = state.get("errors", []) + ["ASSEMBLYAI_API_KEY not found"]
            updates["processing_stage"] = "failed"
            return updates
            
        stt_processor = SpeechToTextProcessor(api_key)
        result = stt_processor.transcribe_audio(state["audio_file_path"])
        
        # Update state with successful results
        updates.update({
            "transcribed_text": result["text"],
            "transcription_confidence": result["confidence"],
            "processing_stage": "speech_to_text_completed"
        })
        
        # Print the transcribed text for verification
        print(f"\n=== Speech-to-Text Result ===")
        print(f"Transcribed Text: {result['text']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print("=" * 50)
        
    except Exception as e:
        error_msg = f"Speech-to-text error: {str(e)}"
        print(f"ERROR in speech_to_text_node: {error_msg}")
        updates["errors"] = state.get("errors", []) + [error_msg]
        updates["processing_stage"] = "failed"
    
    return updates

def semantic_analysis_node(state: ComplaintState) -> Dict[str, Any]:
    """Node 2: Extract customer data and problem details - returns only updates"""
    print("DEBUG: Entering semantic_analysis_node")
    updates = {"processing_stage": "semantic_analysis"}
    
    try:
        # Get API key
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            updates["errors"] = state.get("errors", []) + ["GOOGLE_API_KEY not found"]
            updates["processing_stage"] = "failed"
            return updates
        
        # Handle case where transcription is empty or placeholder
        transcribed_text = state.get("transcribed_text", "")
        if not transcribed_text or "No speech detected" in transcribed_text:
            print("No valid transcription available. Creating default analysis...")
            parsed_data = {
                "customer_name": None,
                "customer_phone": None,
                "customer_email": None,
                "customer_address": None,
                "problem_description": "No complaint text detected in audio",
                "problem_category": "unknown",
                "urgency_level": "low",
                "order_id": None,
                "product_name": None,
                "purchase_date": None,
                "company_name": "unknown",
                "company_confidence": 0.0
            }
        else:
            # Semantic analysis prompt
            analysis_prompt = """
            You are an expert at extracting customer information from complaint text. 
            Extract the following information from the customer complaint and return it as valid JSON:
            
            {
                "customer_name": "extracted name or null",
                "customer_phone": "extracted phone or null", 
                "customer_email": "extracted email or null",
                "customer_address": "extracted address or null",
                "problem_description": "concise problem summary",
                "problem_category": "delivery/product_quality/payment/refund/customer_service/other",
                "urgency_level": "low/medium/high/critical",
                "order_id": "extracted order ID or null",
                "product_name": "extracted product name or null",
                "purchase_date": "extracted date or null",
                "company_name": "amazon/flipkart/other/unknown",
                "company_confidence": 0.0-1.0
            }
            
            Return ONLY the JSON object, no additional text.
            """
            
            # Analyze with Gemini
            print("Analyzing text with Google Gemini...")
            analysis_result = analyze_with_gemini(google_api_key, analysis_prompt, transcribed_text)
            
            # Parse JSON response
            try:
                parsed_data = json.loads(analysis_result.strip())
            except json.JSONDecodeError as e:
                updates["errors"] = state.get("errors", []) + [f"Failed to parse analysis result as JSON: {str(e)}"]
                updates["processing_stage"] = "failed"
                return updates
        
        # Update state with extracted information
        updates.update({
            "customer_name": parsed_data.get("customer_name"),
            "customer_phone": parsed_data.get("customer_phone"),
            "customer_email": parsed_data.get("customer_email"),
            "customer_address": parsed_data.get("customer_address"),
            "problem_description": parsed_data.get("problem_description"),
            "problem_category": parsed_data.get("problem_category"),
            "urgency_level": parsed_data.get("urgency_level"),
            "order_id": parsed_data.get("order_id"),
            "product_name": parsed_data.get("product_name"),
            "purchase_date": parsed_data.get("purchase_date"),
            "company_name": parsed_data.get("company_name"),
            "company_confidence": parsed_data.get("company_confidence"),
            "processing_stage": "semantic_analysis_completed"
        })
            
    except Exception as e:
        error_msg = f"Semantic analysis error: {str(e)}"
        print(f"ERROR in semantic_analysis_node: {error_msg}")
        updates["errors"] = state.get("errors", []) + [error_msg]
        updates["processing_stage"] = "failed"
    
    return updates

def structured_output_node(state: ComplaintState) -> Dict[str, Any]:
    """Node 3: Create final structured output - returns only updates"""
    print("DEBUG: Entering structured_output_node")
    updates = {"processing_stage": "creating_output"}
    
    try:
        # Create structured output
        structured_data = {
            "metadata": {
                "processing_timestamp": state.get("processing_timestamp"),
                "transcription_confidence": state.get("transcription_confidence"),
                "audio_file": state.get("audio_file_path"),
                "errors": state.get("errors", [])
            },
            "transcription": {
                "text": state.get("transcribed_text")
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
                "confidence": state.get("company_confidence")
            },
            "status": "processed" if not state.get("errors") else "processed_with_errors"
        }
        
        updates.update({
            "structured_output": structured_data,
            "processing_stage": "completed"
        })
        
    except Exception as e:
        error_msg = f"Structured output error: {str(e)}"
        print(f"ERROR in structured_output_node: {error_msg}")
        updates["errors"] = state.get("errors", []) + [error_msg]
        updates["processing_stage"] = "failed"
    
    return updates

# Conditional function to determine next step
def should_continue(state: ComplaintState) -> str:
    """Determine next step based on current state"""
    current_stage = state.get("processing_stage", "")
    errors = state.get("errors", [])
    
    if current_stage == "failed" or errors:
        return "end"
    elif current_stage == "speech_to_text_completed":
        return "semantic_analysis"
    elif current_stage == "semantic_analysis_completed":
        return "structured_output"
    elif current_stage == "completed":
        return "end"
    else:
        return "end"

# Build the LangGraph workflow with proper error handling
def create_complaint_processing_graph():
    # Create the graph
    workflow = StateGraph(ComplaintState)
    
    # Add nodes
    workflow.add_node("speech_to_text", speech_to_text_node)
    workflow.add_node("semantic_analysis", semantic_analysis_node)
    workflow.add_node("structured_output", structured_output_node)
    
    # Set entry point
    workflow.set_entry_point("speech_to_text")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "speech_to_text",
        should_continue,
        {
            "semantic_analysis": "semantic_analysis",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "semantic_analysis", 
        should_continue,
        {
            "structured_output": "structured_output",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "structured_output",
        should_continue,
        {
            "end": END
        }
    )
    
    return workflow.compile()

# Main execution function
def process_complaint(audio_file_path: str) -> Optional[Dict[str, Any]]:
    """Process a customer complaint from audio file"""
    
    # Initialize state properly for TypedDict
    initial_state: ComplaintState = {
        "audio_file_path": audio_file_path,
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
        "processing_timestamp": datetime.now().isoformat(),
        "processing_stage": "initialized",
        "errors": [],
        "structured_output": None
    }
    
    # Create and run the graph
    app = create_complaint_processing_graph()
    final_state = app.invoke(initial_state)
    
    # Save result to output folder only if processing was successful
    if final_state.get("structured_output"):
        output_file = get_timestamped_filename("complaint_output", "json", "output")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_state["structured_output"], f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_file}")
    
    return final_state.get("structured_output")

def main():
    """Main execution function"""
    # Ensure folders exist
    ensure_folders_exist()
    
    # Check if API keys are loaded (remove security vulnerability)
    if not os.getenv("ASSEMBLYAI_API_KEY"):
        print("Error: ASSEMBLYAI_API_KEY not found in environment variables")
        print("Please create a .env file with your API key")
        return
    
    # Check for LLM API keys
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        print("Error: GOOGLE_API_KEY not found. Please set it in your .env file")
        return
    
    print("Using Google Gemini API for text analysis")
    
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
            audio_path = recorder.record_audio(duration)
            
        elif choice == "2":
            # Auto-stop on silence
            recorder = AudioRecorder()
            audio_path = recorder.record_until_silence()
            
        elif choice == "3":
            # Use existing file
            audio_path = input("Enter path to audio file: ").strip()
            if not os.path.exists(audio_path):
                print(f"File not found: {audio_path}")
                return
        else:
            print("Invalid choice. Using auto-stop recording...")
            recorder = AudioRecorder()
            audio_path = recorder.record_until_silence()
        
        if not audio_path:
            print("Failed to record audio")
            return
        
        print(f"\n=== Processing Audio File: {audio_path} ===")
        
        # Process the complaint
        result = process_complaint(audio_path)
        
        if result:
            print("\n=== Processing Completed Successfully! ===")
            print("\n=== Summary ===")
            print(json.dumps(result, indent=2))
        else:
            print("Processing failed. Check error messages above.")
            
            # Let's also run the process again with detailed error reporting
            print("\n=== Debugging: Running with detailed error reporting ===")
            try:
                app = create_complaint_processing_graph()
                initial_state = {
                    "audio_file_path": audio_path,
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
                    "processing_timestamp": datetime.now().isoformat(),
                    "processing_stage": "initialized",
                    "errors": [],
                    "structured_output": None
                }
                
                final_state = app.invoke(initial_state)
                print(f"Final state errors: {final_state.get('errors', 'No errors recorded')}")
                print(f"Final processing stage: {final_state.get('processing_stage', 'Unknown')}")
                
            except Exception as debug_e:
                print(f"Debug error: {str(debug_e)}")
                import traceback
                traceback.print_exc()
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()