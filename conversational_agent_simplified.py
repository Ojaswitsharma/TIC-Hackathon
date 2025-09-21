"""
Conversational Agent - Core Conversation Processing
=================================================

This module handles the conversational interface for customer service:
1. Audio recording and transcription
2. Intelligent conversation flow
3. Data collection and structuring
4. JSON output generation

The agent creates structured JSON output that is then processed by langgraph_workflow.py
for company-specific routing and prototype execution.
"""

import json
import whisper
from typing import Dict, Any, Optional, List
from groq import Groq
import os
from datetime import datetime
from dotenv import load_dotenv
import wave
import sounddevice as sd
import numpy as np
import requests
import threading
import time

# Load environment variables from .env file
load_dotenv()

# Utility functions
def ensure_folders_exist():
    """Create necessary folders if they don't exist"""
    os.makedirs("audio_recordings", exist_ok=True)
    os.makedirs("conversations", exist_ok=True)

def get_timestamped_filename(prefix: str, extension: str, folder: str) -> str:
    """Generate timestamped filename in specified folder"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"{prefix}_{timestamp}.{extension}")

# Text-to-Speech System using Murf
class TTSManager:
    def __init__(self):
        # Initialize Murf TTS with API key from environment
        self.murf_api_key = os.getenv("MURF_API_KEY")
        if not self.murf_api_key:
            print("⚠️ Warning: MURF_API_KEY not found. TTS will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            
        # Murf TTS configuration  
        self.voice_id = "en-US-natalie"  # Valid Murf voice ID
        self.api_url = "https://api.murf.ai/v1/speech/generate"
        self.sample_rate = 44100  # Valid Murf sample rate
        
    def speak(self, text: str):
        """Convert text to speech using Murf and play it"""
        print(f"🤖 Agent: {text}")
        
        if not self.enabled:
            return
            
        try:
            # Generate speech using Murf API
            audio_data = self._generate_speech(text)
            if audio_data:
                self._play_audio(audio_data)
        except Exception as e:
            print(f"⚠️ TTS Error: {e}")
    
    def _generate_speech(self, text: str) -> bytes:
        """Generate speech using Murf API"""
        headers = {
            "api-key": self.murf_api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "voiceId": self.voice_id,
            "text": text,
            "rate": 0,  # Normal speed as integer
            "pitch": 0,  # Normal pitch as integer  
            "sampleRate": 44100,  # Valid sample rate for Murf
            "format": "wav"  # Back to WAV format
        }
        
        response = requests.post(self.api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            # Murf returns JSON with audio URL
            response_data = response.json()
            if 'audioFile' in response_data:
                audio_url = response_data['audioFile']
                
                # Download the actual audio file
                audio_response = requests.get(audio_url, timeout=30)
                audio_response.raise_for_status()
                
                print(f"🔊 Audio file size: {len(audio_response.content)} bytes")
                return audio_response.content
            else:
                print(f"❌ No audioFile in response: {response_data}")
                return None
        else:
            print(f"⚠️ Murf API Error: {response.status_code} - {response.text}")
            return None
    
    def _play_audio(self, audio_data: bytes):
        """Play audio data with improved format handling"""
        try:
            # Save to temporary file
            temp_file = "temp_tts_output.wav"  # Use WAV extension
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            print(f"🔊 Audio file size: {len(audio_data)} bytes")
            
            # Try pygame for better audio playback
            try:
                import pygame
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                
                # Wait for audio to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                pygame.mixer.quit()
                print("✅ Audio played successfully with pygame")
                
            except ImportError:
                # Fallback to system commands
                try:
                    import platform
                    system = platform.system().lower()
                    print(f"🔊 Using system audio player for {system}")
                    
                    if system == "linux":
                        # Try multiple players
                        players = ["aplay", "paplay", "pulseaudio"]
                        for player in players:
                            result = os.system(f"which {player} > /dev/null 2>&1")
                            if result == 0:  # Player found
                                os.system(f"{player} {temp_file}")
                                break
                    elif system == "darwin":  # macOS
                        os.system(f"afplay {temp_file}")
                    elif system == "windows":
                        os.system(f"start /wait {temp_file}")
                    else:
                        print("🔊 Audio file saved as temp_tts_output.wav")
                        
                except Exception as e:
                    print(f"⚠️ System audio playback failed: {e}")
            
            except Exception as e:
                print(f"⚠️ Pygame audio playback failed: {e}")
                # Keep the temp file for debugging
                print(f"🔍 Debug: Audio file saved as {temp_file} for inspection")
                return
            
            # Clean up temp file
            try:
                os.remove(temp_file)
            except:
                pass
            
        except Exception as e:
            print(f"⚠️ Audio playback error: {e}")
    
    def speak_async(self, text: str):
        """Convert text to speech asynchronously"""
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
        """Record customer response with press any key to stop"""
        filename = get_timestamped_filename("customer_response", "wav", "audio_recordings")
        
        print(f"\n🎤 {prompt_text}")
        print("🔴 Recording... Speak now! Press ENTER when finished.")
        
        chunk_duration = 0.1  # 100ms chunks
        chunk_size = int(self.sample_rate * chunk_duration)
        audio_chunks = []
        
        import threading
        import sys
        import select
        
        # Flag to stop recording
        stop_recording = threading.Event()
        
        def wait_for_key():
            """Wait for user to press Enter"""
            input()  # Wait for Enter key
            stop_recording.set()
        
        # Start key listener thread
        key_thread = threading.Thread(target=wait_for_key, daemon=True)
        key_thread.start()
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16,
                blocksize=chunk_size
            ) as stream:
                while not stop_recording.is_set():
                    chunk, overflowed = stream.read(chunk_size)
                    if overflowed:
                        print("⚠️ Audio buffer overflowed")
                    
                    audio_chunks.append(chunk)
                    
                    # Maximum recording time (60 seconds safety limit)
                    if len(audio_chunks) > 6000:  # 60 seconds at 100ms chunks
                        print("⏰ Maximum recording time reached")
                        break
                        
        except KeyboardInterrupt:
            print("\n🛑 Recording stopped by user")
        except Exception as e:
            print(f"❌ Recording error: {str(e)}")
            return None
        
        if not audio_chunks:
            print("❌ No audio recorded")
            return None
        
        # Combine and save audio
        audio_data = np.concatenate(audio_chunks)
        self._save_audio(audio_data, filename)
        
        print(f"✅ Recording completed: {filename}")
        return filename

# Core Conversational Agent
class IntelligentConversationalAgent:
    def __init__(self):
        # Initialize services
        self._initialize_services()
        
        # Conversation state
        self.conversation_history = []
        self.customer_data = {}
        self.question_count = 0
        self.max_questions = 6
        
        # Initialize tools
        self.tts = TTSManager()
        self.recorder = ConversationAudioRecorder()
    
    def _initialize_services(self):
        """Initialize AI services"""
        # Whisper for transcription
        try:
            self.transcriber = whisper.load_model("base")
            print("✅ Whisper model loaded successfully")
        except Exception as e:
            raise Exception(f"Failed to load Whisper model: {str(e)}")
        
        # Groq for conversation intelligence
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            self.model = Groq(api_key=groq_api_key)
        else:
            raise Exception("GROQ_API_KEY not found")
    
    def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio file and return text with confidence"""
        try:
            print(f"🎧 Transcribing audio: {audio_file_path}")
            result = self.transcriber.transcribe(audio_file_path)
            
            return {
                "text": result["text"],
                "confidence": 0.9,  # Whisper doesn't provide confidence scores, using default high confidence
                "success": True
            }
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }
    
    def analyze_conversation_intelligent(self, transcript: str, current_data: Dict) -> Dict[str, Any]:
        """Use Gemini to intelligently analyze customer response and decide next action"""
        
        current_data_str = json.dumps(current_data, indent=2) if current_data else "None collected yet"
        
        analysis_prompt = f"""
        You are an expert at extracting customer information from conversations. 
        Analyze the customer's response and extract all relevant information.
        
        Customer Response: "{transcript}"
        
        Previously Collected Data: {current_data_str}
        
        IMPORTANT: You must respond with ONLY a valid JSON object, no other text.
        
        Extract and return a JSON object with these exact fields:
        
        {{
            "extracted_info": {{
                "name": "customer name if mentioned or null",
                "phone": "phone number if provided or null", 
                "email": "email address if provided or null",
                "address": "address if mentioned or null",
                "order_id": "order/tracking/transaction number if provided or null",
                "product_name": "product or service name if mentioned or null",
                "purchase_date": "date of purchase/transaction if mentioned or null"
            }},
            "problem_info": {{
                "description": "detailed problem description or null",
                "category": "delivery/product_quality/payment/refund/account_issues/content_moderation/other or null",
                "urgency_level": "low/medium/high/critical or null"
            }},
            "company_detection": {{
                "company": "amazon/flipkart/facebook/meta/unknown",
                "confidence": 0.95
            }},
            "customer_emotion": "calm/frustrated/angry/satisfied/confused",
            "summary": "brief summary of this response"
        }}
        
        COMPANY DETECTION RULES:
        - If customer mentions "Amazon", "amazon.com", "Amazon website", "Amazon delivery", set company to "amazon" with confidence 0.9-1.0
        - If customer mentions "Flipkart", "flipkart.com", "FlipCard", "Flipkart delivery", set company to "flipkart" with confidence 0.9-1.0  
        - If customer mentions "Facebook", "Meta", "FB", "facebook.com", set company to "facebook" with confidence 0.9-1.0
        - If customer mentions package delivery without specific company, set company to "amazon" with confidence 0.7
        - If company is unclear, set company to "unknown" with confidence 0.0
        
        IMPORTANT: Return ONLY the JSON object, no other text before or after.
        """
        
        try:
            response = self.model.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Clean and parse JSON response
            response_text = response.choices[0].message.content.strip()
            print(f"🔍 Raw Groq response: {response_text}")  # Debug line
            
            # Clean up common JSON formatting issues
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            # Try to find JSON within the response if it's embedded in text
            if not response_text.startswith('{'):
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group()
            
            analysis = json.loads(response_text)
            return analysis
            
        except Exception as e:
            print(f"❌ Analysis error: {str(e)}")
            return {
                "extracted_info": {},
                "problem_info": {},
                "company_detection": {"company": "unknown", "confidence": 0.0},
                "customer_emotion": "unknown",
                "summary": "Analysis failed"
            }

    def perform_final_analysis(self):
        """Perform comprehensive analysis of the entire conversation to extract all information"""
        
        # Extract all customer responses from the conversation
        customer_responses = [msg["message"] for msg in self.conversation_history if msg["role"] == "customer"]
        full_conversation = "\n".join(customer_responses)
        
        print(f"🔍 Performing final comprehensive analysis...")
        
        final_analysis_prompt = f"""
        You are an expert at extracting customer information from complete conversations.
        Analyze this COMPLETE customer service conversation and extract ALL relevant information.
        
        COMPLETE CUSTOMER CONVERSATION:
        {full_conversation}
        
        CONVERSATION CONTEXT:
        The customer was asked these questions in order:
        1. Name and issue description
        2. Which company/service (Amazon, Facebook, Flipkart, etc.)
        3. Phone number and email address
        4. Order/transaction/tracking number
        5. Product/service and purchase date
        6. Additional information
        
        IMPORTANT: You must respond with ONLY a valid JSON object, no other text.
        
        Analyze the ENTIRE conversation and extract ALL information mentioned anywhere:
        
        {{
            "customer_info": {{
                "name": "full customer name if mentioned anywhere or null",
                "phone": "phone number if provided anywhere or null", 
                "email": "email address if provided anywhere or null",
                "address": "address if mentioned anywhere or null"
            }},
            "complaint_info": {{
                "description": "complete problem description from all responses",
                "category": "delivery/product_quality/payment/refund/account_issues/content_moderation/other",
                "urgency_level": "low/medium/high/critical",
                "order_id": "order/tracking/transaction number from anywhere in conversation or null",
                "product_name": "product or service name mentioned anywhere or null",
                "purchase_date": "date of purchase/transaction mentioned anywhere or null"
            }},
            "company_info": {{
                "company_name": "amazon/flipkart/facebook/meta/unknown",
                "confidence": 0.95
            }},
            "additional_info": {{
                "customer_emotion": "calm/frustrated/angry/satisfied/confused",
                "premium_member": true,
                "summary": "comprehensive summary of the entire issue and conversation"
            }}
        }}
        
        COMPANY DETECTION RULES:
        - If customer mentions "Amazon", "amazon.com", "Amazon website", "Hamzun", set company_name to "amazon" with confidence 0.9-1.0
        - If customer mentions "Flipkart", "flipkart.com", "FlipCard", "flip-cut", set company_name to "flipkart" with confidence 0.9-1.0  
        - If customer mentions "Facebook", "Meta", "FB", "facebook.com", set company_name to "facebook" with confidence 0.9-1.0
        - If package delivery is mentioned without specific company, set company_name to "amazon" with confidence 0.7
        - If unclear, set company_name to "unknown" with confidence 0.0
        
        IMPORTANT: 
        - Extract ALL information mentioned ANYWHERE in the conversation
        - Look across ALL customer responses, not just individual ones
        - Return ONLY the JSON object, no other text
        - Be thorough and comprehensive
        """
        
        try:
            response = self.model.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": final_analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            # Clean and parse JSON response
            response_text = response.choices[0].message.content.strip()
            print(f"🔍 Final analysis response: {response_text}")
            
            # Clean up common JSON formatting issues
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            # Try to find JSON within the response if it's embedded in text
            if not response_text.startswith('{'):
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group()
            
            final_analysis = json.loads(response_text)
            
            # Update customer_data with comprehensive analysis
            self.customer_data.update(final_analysis.get("customer_info", {}))
            self.customer_data.update(final_analysis.get("complaint_info", {}))
            
            # Update company info
            company_info = final_analysis.get("company_info", {})
            self.customer_data["company_name"] = company_info.get("company_name", "unknown")
            self.customer_data["company_confidence"] = company_info.get("confidence", 0.0)
            
            # Store additional info
            self.customer_data.update(final_analysis.get("additional_info", {}))
            
            print(f"✅ Final analysis completed - Company: {self.customer_data.get('company_name')} (confidence: {self.customer_data.get('company_confidence', 0.0):.2f})")
            
        except Exception as e:
            print(f"❌ Final analysis error: {str(e)}")
            # Fallback to unknown company if analysis fails
            self.customer_data["company_name"] = "unknown"
            self.customer_data["company_confidence"] = 0.0
    
    def conduct_conversation(self) -> Dict[str, Any]:
        """Conduct conversation with hardcoded questions to gather all necessary information"""
        
        print("\n" + "="*60)
        print("🤖 INTELLIGENT CUSTOMER SERVICE CONVERSATION")
        print("="*60)
        
        # Welcome message
        welcome_msg = "Hello! I'm your AI customer service assistant. I'll help you with your issue by asking a few questions. Let's start!"
        self.tts.speak(welcome_msg)
        self.conversation_history.append({"role": "agent", "message": welcome_msg})
        
        # Hardcoded questions to gather all necessary information
        questions = [
            "Could you please tell me your name and describe the issue you're experiencing?",
            "Which company or service is this complaint about? For example, Amazon, Facebook, Flipkart, or another company?",
            "Could you please provide your phone number and email address for our records?",
            "If this involves an order or transaction, please provide the order number, tracking number, or transaction ID.",
            "What product or service is involved, and when did you purchase or use it?",
            "Is there any additional information you'd like to add about this issue?"
        ]
        
        # Ask each question and collect responses
        for i, question in enumerate(questions, 1):
            self.question_count = i
            
            print(f"\n--- Question {i}/{len(questions)} ---")
            
            # Ask the question
            self.tts.speak(question)
            self.conversation_history.append({"role": "agent", "message": question})
            
            # Record customer response
            audio_file = self.recorder.record_response(f"🎤 Question {i}: Please respond")
            
            if not audio_file:
                print("❌ Failed to record audio. Ending conversation.")
                break
            
            # Transcribe response
            transcription_result = self.transcribe_audio(audio_file)
            if not transcription_result["success"]:
                print("❌ Failed to transcribe audio. Ending conversation.")
                break
            
            transcript = transcription_result["text"]
            print(f"👤 Customer: {transcript}")
            self.conversation_history.append({"role": "customer", "message": transcript})
            
            # Store the transcript for final analysis (no incremental analysis)
            # We'll analyze everything at the end for better accuracy
        
        # Final completion message
        final_msg = "Thank you for providing all the information. Let me process what we've discussed."
        self.tts.speak(final_msg)
        self.conversation_history.append({"role": "agent", "message": final_msg})
        
        # NOW do the comprehensive final analysis
        self.perform_final_analysis()
        
        return self.create_structured_output()
    
    def create_structured_output(self) -> Dict[str, Any]:
        """Create structured JSON output for workflow processing"""
        
        # Perform comprehensive analysis of the complete conversation
        self.perform_final_analysis()
        
        structured_data = {
            "conversation_metadata": {
                "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "timestamp": datetime.now().isoformat(),
                "total_questions": self.question_count,
                "conversation_length": len(self.conversation_history)
            },
            "customer_info": {
                "name": self.customer_data.get("name"),
                "phone": self.customer_data.get("phone"),
                "email": self.customer_data.get("email"),
                "address": self.customer_data.get("address")
            },
            "complaint_info": {
                "description": self.customer_data.get("description"),
                "category": self.customer_data.get("category"),
                "urgency_level": self.customer_data.get("urgency_level"),
                "order_id": self.customer_data.get("order_id"),
                "product_name": self.customer_data.get("product_name"),
                "purchase_date": self.customer_data.get("purchase_date")
            },
            "company_info": {
                "company_name": self.customer_data.get("company_name", "unknown"),
                "confidence": self.customer_data.get("company_confidence", 0.0)
            },
            "processing_info": {
                "status": "conversation_completed",
                "ready_for_routing": True,
                "created_timestamp": datetime.now().isoformat()
            }
        }
        
        # Save conversation JSON
        ensure_folders_exist()
        conversation_file = get_timestamped_filename("conversation", "json", "conversations")
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Conversation JSON saved: {conversation_file}")
        print(f"🏢 Detected Company: {structured_data['company_info']['company_name']}")
        print(f"📊 Confidence: {structured_data['company_info']['confidence']:.2f}")
        
        return {
            "conversation_data": structured_data,
            "conversation_file": conversation_file
        }

# ====================================
# MAIN EXECUTION FUNCTIONS
# ====================================

def start_conversation_session(max_questions: int = 6) -> Optional[Dict[str, Any]]:
    """Start a complete conversation session and return structured output"""
    
    try:
        # Initialize agent
        agent = IntelligentConversationalAgent()
        agent.max_questions = max_questions
        
        # Conduct conversation
        result = agent.conduct_conversation()
        
        return result
        
    except Exception as e:
        print(f"❌ Conversation session error: {str(e)}")
        return None

def main():
    """Main entry point for standalone conversational agent testing"""
    
    # Check API keys
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY not found in environment variables")
        return
    
    print("✅ Using Groq API for conversation intelligence")
    print("✅ Using Whisper for speech recognition")
    
    try:
        print("\n" + "="*70)
        print("🤖 CONVERSATIONAL AGENT - STANDALONE MODE")
        print("🗣️  Intelligent Customer Service Conversation")
        print("="*70)
        
        print("\nℹ️  Instructions:")
        print("   • The agent will ask up to 3 intelligent questions")
        print("   • Speak clearly after each question")  
        print("   • Recording starts when you speak")
        print("   • Press ENTER to stop recording when you're done speaking")
        print("   • Conversation data will be saved as JSON")
        print("   • Press Ctrl+C anytime to exit")
        
        input("\nPress Enter to start the conversation...")
        
        # Start the conversation
        result = start_conversation_session(max_questions=6)
        
        if result:
            print("\n" + "="*70)
            print("✅ CONVERSATION COMPLETED SUCCESSFULLY!")
            print("="*70)
            print(f"\n📄 Conversation file: {result['conversation_file']}")
            print("\n🎯 Next Step: Use langgraph_workflow.py to process this conversation")
            print("\n📋 Conversation Summary:")
            conversation_data = result['conversation_data']
            print(f"   • Customer: {conversation_data['customer_info']['name'] or 'Unknown'}")
            print(f"   • Company: {conversation_data['company_info']['company_name']}")
            print(f"   • Issue: {conversation_data['complaint_info']['description'] or 'Not specified'}")
        else:
            print("\n❌ Conversation failed. Please check the error messages above.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Conversation ended by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()