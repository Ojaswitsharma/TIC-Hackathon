"""
Conversational Agent - Audio Input & Conversation Processing
===========================    def __init__(self, max_questions: int = 6):
        # Whisper model setup
        self.whisper_model = whisper.load_model("tiny")
        
        # Groq setup
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise Exception("GROQ_API_KEY not found")
        
        self.groq_client = Groq(api_key=self.groq_api_key)
        self.tts = TTSManager()
        self.max_questions = max_questions
        
        # Conversation tracking
        self.conversation_history = []
        self.emotion_tracking = []
        
        # Predefined questions for structured data collection
        self.questions = [
            "Hello! I'm here to help you with your complaint today. To get started, could you please tell me your name and briefly describe the issue you're experiencing?",
            "I understand your frustration. Could you please provide your phone number or email address so we can contact you about the resolution?",
            "Can you tell me more details about what exactly happened with your product or service?",
            "What is the name or model of the product you're having issues with?",
            "When did you purchase this product or when did this issue start occurring?",
            "Is there anything else you'd like to add about this issue that might help us resolve it better?"
        ]===========

Handles:
1. Audio recording from microphone
2. Speech-to-text using Whisper
3. Intelligent conversation with Groq LLM
4. Text-to-Speech output using system audio
"""

import json
import os
import sys
import whisper
import sounddevice as sd
import numpy as np
import wave
import requests
from typing import Dict, Any, Optional
from groq import Groq
from datetime import datetime

# Import audio utils from current directory
from tic_audio import play_audio_from_bytes


class TTSManager:
    """Minimal TTS manager using Murf API"""
    
    def __init__(self):
        self.murf_api_key = os.getenv("MURF_API_KEY")
        self.enabled = bool(self.murf_api_key)
        
        if not self.enabled:
            print("⚠️ TTS disabled: MURF_API_KEY not found")
        
        self.voice_id = "en-US-natalie"
        self.api_url = "https://api.murf.ai/v1/speech/generate"
    
    def speak(self, text: str):
        """Convert text to speech and play it"""
        print(f"🤖 Agent: {text}")
        
        if not self.enabled:
            return
        
        try:
            audio_data = self._generate_speech(text)
            if audio_data:
                play_audio_from_bytes(audio_data, "temp_tts.wav")
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
            "rate": 0,
            "pitch": 0,
            "sampleRate": 44100,
            "format": "wav"
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                if 'audioFile' in response_data:
                    audio_url = response_data['audioFile']
                    audio_response = requests.get(audio_url, timeout=30)
                    audio_response.raise_for_status()
                    return audio_response.content
            
            print(f"⚠️ TTS API error: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"⚠️ TTS generation failed: {e}")
            return None


class ConversationalAgent:
    """Main conversational agent for customer service"""
    
    def __init__(self):
        # Initialize Groq client
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise Exception("GROQ_API_KEY not found in environment")
        
        self.groq_client = Groq(api_key=self.groq_api_key)
        
        # Initialize Whisper model
        print("🔄 Loading Whisper model...")
        self.whisper_model = whisper.load_model("tiny")  # Fast, small model
        print("✅ Whisper model loaded")
        
        # Initialize TTS
        self.tts = TTSManager()
        
        # Conversation settings
        self.max_questions = 6
        self.sample_rate = 44100
        self.channels = 1
        
        # Conversation tracking
        self.conversation_history = []
        self.emotion_tracking = []
        
        # Predefined questions for structured data collection
        self.questions = [
            "Hello! I'm here to help you with your complaint today. To get started, could you please tell me your name and briefly describe the issue you're experiencing?",
            "I understand your frustration. Could you please provide your phone number or email address so we can contact you about the resolution?",
            "Can you tell me more details about what exactly happened with your product or service?",
            "What is the name or model of the product you're having issues with?",
            "When did you purchase this product or when did this issue start occurring?",
            "Is there anything else you'd like to add about this issue that might help us resolve it better?"
        ]
    
    def record_audio(self, duration: int = 5) -> Optional[np.ndarray]:
        """Record audio from microphone"""
        try:
            print(f"🎤 Recording audio for {duration} seconds...")
            print("   Speak clearly about your issue...")
            
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16
            )
            sd.wait()  # Wait until recording is finished
            
            print("✅ Audio recording completed")
            return audio_data
            
        except Exception as e:
            print(f"❌ Audio recording failed: {e}")
            return None
    
    def transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio using Whisper"""
        try:
            # Save temporary WAV file
            temp_wav = "temp_recording.wav"
            with wave.open(temp_wav, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            # Transcribe with Whisper
            print("🔄 Transcribing audio...")
            result = self.whisper_model.transcribe(temp_wav)
            
            # Clean up
            os.remove(temp_wav)
            
            transcription = result["text"].strip()
            print(f"📝 Transcription: {transcription}")
            
            return transcription if transcription else None
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return None
    
    def analyze_with_groq(self, transcription: str, question_num: int) -> Dict[str, Any]:
        """Extract structured information based on question number"""
        
        extraction_prompts = {
            1: """Extract customer name and basic issue description:
            Customer response: "{}"
            
            Look for company names or product mentions that indicate the company:
            - Amazon: amazon, prime, aws
            - Apple: apple, iphone, macbook, ipad, mac, ios
            - Facebook/Meta: facebook, meta, instagram, whatsapp  
            - Google: google, pixel, android, gmail
            - Microsoft: microsoft, windows, xbox, office
            - Samsung: samsung, galaxy
            - Dell: dell, latitude, inspiron
            - HP: hp, pavilion, envy
            - Lenovo: lenovo, thinkpad
            
            Return JSON:
            {{
                "customer_name": "extracted name or null",
                "company_name": "detected company name or null", 
                "issue_description": "brief issue summary",
                "urgency_keywords": ["urgent", "broken", "not working", etc]
            }}""",
            
            2: """Extract contact information:
            Customer response: "{}"
            
            Return JSON:
            {{
                "phone_number": "extracted phone or null",
                "email_address": "extracted email or null"
            }}""",
            
            3: """Extract detailed problem information:
            Customer response: "{}"
            
            Return JSON:
            {{
                "problem_details": "detailed description",
                "problem_category": "Product malfunction/Billing issue/Shipping problem/Account issue/Technical support/Other or null",
                "urgency_level": "low/medium/high/critical or null"
            }}""",
            
            4: """Extract product information:
            Customer response: "{}"
            
            Return JSON:
            {{
                "product_name": "extracted product name/model or null",
                "brand": "extracted brand or null"
            }}""",
            
            5: """Extract timing information:
            Customer response: "{}"
            
            Return JSON:
            {{
                "purchase_date": "when purchased or null",
                "issue_start_date": "when issue started or null",
                "timeline_info": "any time-related details"
            }}""",
            
            6: """Extract additional information:
            Customer response: "{}"
            
            Return JSON:
            {{
                "additional_details": "any extra information provided",
                "customer_requests": "what customer wants/expects"
            }}"""
        }
        
        prompt = extraction_prompts.get(question_num, extraction_prompts[6]).format(transcription)
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Handle empty response
            if not response_text:
                print("⚠️ Groq returned empty response")
                return self._get_fallback_extraction(question_num, transcription)
            
            # Try to parse JSON
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                print(f"⚠️ Groq returned invalid JSON: {response_text}")
                return self._get_fallback_extraction(question_num, transcription)
            
        except Exception as e:
            print(f"⚠️ Groq analysis failed: {e}")
            return self._get_fallback_extraction(question_num, transcription)
    
    def _detect_company_from_text(self, text: str) -> Optional[str]:
        """Detect company from text based on products and keywords"""
        company_detection = {
            "amazon": ["amazon", "prime", "aws"],
            "apple": ["apple", "iphone", "macbook", "ipad", "mac", "ios"],
            "facebook": ["facebook", "meta", "instagram", "whatsapp"],
            "flipkart": ["flipkart"],
            "google": ["google", "pixel", "android", "gmail"],
            "microsoft": ["microsoft", "windows", "xbox", "office"],
            "samsung": ["samsung", "galaxy"],
            "dell": ["dell", "latitude", "inspiron"],
            "hp": ["hp", "pavilion", "envy"],
            "lenovo": ["lenovo", "thinkpad"]
        }
        
        text_lower = text.lower()
        for company, keywords in company_detection.items():
            if any(keyword in text_lower for keyword in keywords):
                return company.title()
        return None

    def _get_fallback_extraction(self, question_num: int, transcription: str) -> Dict[str, Any]:
        """Fallback extraction when Groq fails"""
        import re
        
        fallback_data = {}
        
        if question_num == 1:
            # Extract name - look for "name is" or "I'm" patterns
            name_patterns = [
                r'(?:name is|my name is|i am|i\'m)\s+(\w+)',
                r'(\w+)(?:\s+is my name|\s+here)'
            ]
            for pattern in name_patterns:
                match = re.search(pattern, transcription.lower())
                if match:
                    fallback_data["customer_name"] = match.group(1).title()
                    break
            
            # Extract company - look for known companies and their products
            company = self._detect_company_from_text(transcription)
            if company:
                fallback_data["company_name"] = company
            
            fallback_data["issue_description"] = transcription
            
        elif question_num == 2:
            # Extract phone/email
            phone_match = re.search(r'[\d\s\-\+\(\)]{8,}', transcription)
            email_match = re.search(r'\S+@\S+\.\S+', transcription)
            if phone_match:
                fallback_data["phone_number"] = phone_match.group().strip()
            if email_match:
                fallback_data["email_address"] = email_match.group().strip()
                
        elif question_num == 3:
            fallback_data["problem_details"] = transcription
            # Simple urgency detection
            urgency_words = ["urgent", "broken", "not working", "failed", "critical"]
            if any(word in transcription.lower() for word in urgency_words):
                fallback_data["urgency_level"] = "high"
                
        elif question_num == 4:
            fallback_data["product_name"] = transcription
            
        elif question_num == 5:
            fallback_data["purchase_date"] = transcription
            
        elif question_num == 6:
            fallback_data["additional_details"] = transcription
        
        return fallback_data

    def get_text_input(self, prompt: str) -> Optional[str]:
        """Get text input as fallback"""
        print(f"\n💬 {prompt}")
        try:
            response = input("Your response: ").strip()
            return response if response else None
        except KeyboardInterrupt:
            return None
    
    def start_conversation(self) -> Dict[str, Any]:
        """Start the conversational flow"""
        
        print("\n" + "="*50)
        print("🎤 CUSTOMER SERVICE CONVERSATION")
        print("="*50)
        
        # Welcome message
        welcome_msg = self.questions[0]
        self.tts.speak(welcome_msg)
        
        # Track welcome message
        self.add_conversation_turn("agent", welcome_msg)
        
        collected_data = {
            "customer_name": None,
            "company": None,
            "issue_description": None,
            "phone_number": None,
            "email_address": None,
            "problem_details": None,
            "problem_category": None,
            "urgency_level": None,
            "product_name": None,
            "brand": None,
            "purchase_date": None,
            "issue_start_date": None,
            "additional_details": None,
            "customer_requests": None
        }
        
        try:
            for question_num in range(1, self.max_questions + 1):
                print(f"\n📋 Question {question_num}/{self.max_questions}")
                
                # Record audio
                audio_data = self.record_audio(duration=10)
                
                if audio_data is not None:
                    # Transcribe
                    transcription = self.transcribe_audio(audio_data)
                    
                    if transcription:
                        # Track customer response
                        self.add_conversation_turn("customer", transcription)
                        
                        # Track emotion (with null values)
                        emotion_data = self.analyze_emotion(transcription, question_num)
                        self.emotion_tracking.append(emotion_data)
                        
                        # Analyze with Groq
                        analysis = self.analyze_with_groq(transcription, question_num)
                        
                        # Extract and merge information based on question
                        if question_num == 1:
                            collected_data["customer_name"] = analysis.get("customer_name") or None
                            collected_data["company"] = analysis.get("company_name") or None
                            collected_data["issue_description"] = analysis.get("issue_description") or transcription
                        
                        # Additional company detection from any response (not just Q1)
                        if not collected_data.get("company"):  # Only if not already detected
                            detected_company = self._detect_company_from_text(transcription)
                            if detected_company:
                                collected_data["company"] = detected_company
                        elif question_num == 2:
                            collected_data["phone_number"] = analysis.get("phone_number") or None
                            collected_data["email_address"] = analysis.get("email_address") or None
                        elif question_num == 3:
                            collected_data["problem_details"] = analysis.get("problem_details") or transcription
                            collected_data["problem_category"] = analysis.get("problem_category") or None
                            collected_data["urgency_level"] = analysis.get("urgency_level") or None
                        elif question_num == 4:
                            collected_data["product_name"] = analysis.get("product_name") or None
                            collected_data["brand"] = analysis.get("brand") or None
                        elif question_num == 5:
                            collected_data["purchase_date"] = analysis.get("purchase_date") or None
                            collected_data["issue_start_date"] = analysis.get("issue_start_date") or None
                        elif question_num == 6:
                            collected_data["additional_details"] = analysis.get("additional_details") or transcription
                            collected_data["customer_requests"] = analysis.get("customer_requests") or None
                        
                        # Ask next question
                        if question_num < self.max_questions:
                            next_question = self.questions[question_num]  # Use predefined questions
                            self.tts.speak(next_question)
                            # Track agent response
                            self.add_conversation_turn("agent", next_question)
                    else:
                        # Fallback to text input
                        fallback_prompt = f"Audio unclear. Please type your response for question {question_num}:"
                        text_response = self.get_text_input(fallback_prompt)
                        
                        if text_response:
                            # Track customer response
                            self.add_conversation_turn("customer", text_response)
                            
                            # Track emotion (with null values)
                            emotion_data = self.analyze_emotion(text_response, question_num)
                            self.emotion_tracking.append(emotion_data)
                            
                            analysis = self.analyze_with_groq(text_response, question_num)
                            # Process similar to audio response - use same extraction logic
                            if question_num == 1:
                                collected_data["customer_name"] = analysis.get("customer_name") or None
                                collected_data["company"] = analysis.get("company_name") or None
                                collected_data["issue_description"] = analysis.get("issue_description") or text_response
                            elif question_num == 2:
                                collected_data["phone_number"] = analysis.get("phone_number") or None
                                collected_data["email_address"] = analysis.get("email_address") or None
                            elif question_num == 3:
                                collected_data["problem_details"] = analysis.get("problem_details") or text_response
                                collected_data["problem_category"] = analysis.get("problem_category") or None
                                collected_data["urgency_level"] = analysis.get("urgency_level") or None
                            elif question_num == 4:
                                collected_data["product_name"] = analysis.get("product_name") or None
                                collected_data["brand"] = analysis.get("brand") or None
                            elif question_num == 5:
                                collected_data["purchase_date"] = analysis.get("purchase_date") or None
                                collected_data["issue_start_date"] = analysis.get("issue_start_date") or None
                            elif question_num == 6:
                                collected_data["additional_details"] = analysis.get("additional_details") or text_response
                                collected_data["customer_requests"] = analysis.get("customer_requests") or None
                        else:
                            break
                else:
                    # Audio recording failed, use text input
                    text_prompt = f"Question {question_num}: Please describe your issue:"
                    text_response = self.get_text_input(text_prompt)
                    
                    if text_response:
                        # Track customer response
                        self.add_conversation_turn("customer", text_response)
                        
                        # Track emotion (with null values)
                        emotion_data = self.analyze_emotion(text_response, question_num)
                        self.emotion_tracking.append(emotion_data)
                        
                        # Simple extraction without Groq for fallback
                        if question_num == 1:
                            collected_data["issue_description"] = text_response
                            
                        # Company detection for any question (not just question 1)
                        if not collected_data.get("company"):  # Only if not already detected
                            detected_company = self._detect_company_from_text(text_response)
                            if detected_company:
                                collected_data["company"] = detected_company
                        elif question_num == 2:
                            # Extract phone/email with simple patterns
                            import re
                            phone_match = re.search(r'[\d\s\-\+\(\)]+', text_response)
                            email_match = re.search(r'\S+@\S+\.\S+', text_response)
                            if phone_match:
                                collected_data["phone_number"] = phone_match.group().strip()
                            if email_match:
                                collected_data["email_address"] = email_match.group().strip()
                        else:
                            # For other questions, just store as additional details
                            if not collected_data["additional_details"]:
                                collected_data["additional_details"] = text_response
                            else:
                                collected_data["additional_details"] += " | " + text_response
                    else:
                        break
            
            # Final summary
            if collected_data["issue_description"]:
                summary_msg = "Thank you for providing that information. I've recorded all the details about your complaint and we'll work on resolving this for you as soon as possible."
                self.tts.speak(summary_msg)
                
                # Track final agent message
                self.add_conversation_turn("agent", summary_msg)
                
                # Create comprehensive JSON
                comprehensive_json = self.create_comprehensive_json(collected_data)
                
                return {
                    "success": True,
                    "data": collected_data,
                    "conversation_json": comprehensive_json
                }
            else:
                return {"success": False, "error": "No issue information collected"}
                
        except KeyboardInterrupt:
            print("\n👋 Conversation cancelled by user")
            return {"success": False, "error": "Cancelled by user"}
        
        except Exception as e:
            print(f"❌ Conversation error: {e}")
            return {"success": False, "error": str(e)}
    
    def speak_solution(self, solution_text: str):
        """Speak the final solution to customer"""
        self.tts.speak(solution_text)
    
    def save_conversation_json(self, conversation_json: Dict[str, Any], filename: str = None):
        """Save conversation JSON to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        try:
            os.makedirs("conversations", exist_ok=True)
            filepath = os.path.join("conversations", filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_json, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Conversation saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Failed to save conversation: {e}")
            return None
    
    def add_conversation_turn(self, role: str, message: str):
        """Add a conversation turn to history"""
        self.conversation_history.append({
            "role": role,
            "message": message
        })
    
    def analyze_emotion(self, text: str, question_number: int) -> Dict[str, Any]:
        """Create emotion tracking entry with null values"""
        return {
            "question_number": question_number,
            "emotion": None,
            "intensity": None,
            "keywords": [],
            "response_text": text
        }
    
    def create_comprehensive_json(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create the comprehensive conversation JSON with all details"""
        
        # Use structured collected data
        extracted_data = {
            "customer_name": collected_data.get("customer_name"),
            "problem_description": collected_data.get("issue_description") or collected_data.get("problem_details"),
            "problem_category": collected_data.get("problem_category"),
            "urgency_level": collected_data.get("urgency_level"),
            "product_name": collected_data.get("product_name"),
            "company_name": collected_data.get("company"),
            "customer_phone": collected_data.get("phone_number"),
            "customer_email": collected_data.get("email_address")
        }
        
        # Create comprehensive JSON
        conversation_json = {
            "timestamp": datetime.now().isoformat(),
            "conversation_history": self.conversation_history,
            "extracted_data": extracted_data,
            "emotion_tracking": self.emotion_tracking,
            "total_questions": len([turn for turn in self.conversation_history if turn["role"] == "customer"])
        }
        
        return conversation_json
    

