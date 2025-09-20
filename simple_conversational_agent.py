import json
import os
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

class SimpleConversationalAgent:
    def __init__(self):
        # Initialize Gemini (no TTS needed for text-only mode)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            genai.configure(api_key=google_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            raise Exception("GOOGLE_API_KEY not found")
        
        # Conversation state
        self.conversation_history = []
        self.customer_data = {}
        self.question_count = 0
        self.max_questions = 3
        self.customer_emotions = []  # Track emotional state throughout conversation
    
    def speak(self, text):
        """Display agent response (text only, no TTS)"""
        print(f"🤖 Agent: {text}")
    
    def get_customer_input(self, prompt="Please respond:"):
        """Get text input from customer (simulating voice input)"""
        print(f"\n👤 {prompt}")
        response = input("Your response: ")
        return response
    
    def extract_info(self, question, response):
        """Extract information and emotion from customer response"""
        extraction_prompt = f"""
        Extract customer information and emotional state from this conversation exchange:
        
        Agent Question: {question}
        Customer Response: {response}
        
        Current customer data: {json.dumps(self.customer_data)}
        
        Extract any new/updated information and return as JSON:
        {{
            "customer_name": "name or null",
            "customer_phone": "phone or null",
            "customer_email": "email or null",
            "problem_description": "problem description or null",
            "problem_category": "category or null",
            "urgency_level": "low/medium/high/critical or null",
            "order_id": "order ID or null",
            "product_name": "product or null",
            "company_name": "amazon/flipkart/other or null",
            "customer_emotion": "angry/frustrated/disappointed/worried/calm/satisfied/neutral or null",
            "emotion_intensity": "low/medium/high or null",
            "emotion_keywords": ["list of emotional words/phrases found in response"]
        }}
        
        Return only the JSON, nothing else.
        """
        
        try:
            result = self.model.generate_content(
                extraction_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=300
                )
            )
            
            # Clean up the response text
            response_text = result.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            print(f"🔍 Extraction response: {response_text}")
            
            extracted = json.loads(response_text)
            
            # Update customer data with non-null values
            emotion_data = {}
            for key, value in extracted.items():
                if value and value != "null" and value != "":
                    if key in ["customer_emotion", "emotion_intensity", "emotion_keywords"]:
                        emotion_data[key] = value
                        print(f"😊 Detected {key}: {value}")
                    else:
                        self.customer_data[key] = value
                        print(f"✅ Extracted {key}: {value}")
            
            # Track emotions throughout conversation
            if emotion_data:
                emotion_entry = {
                    "question_number": self.question_count,
                    "emotion": emotion_data.get("customer_emotion"),
                    "intensity": emotion_data.get("emotion_intensity"),
                    "keywords": emotion_data.get("emotion_keywords", []),
                    "response_text": response
                }
                self.customer_emotions.append(emotion_entry)
                    
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing failed: {e}")
            print(f"Raw response: {result.text}")
        except Exception as e:
            print(f"⚠️ Info extraction failed: {e}")
    
    def generate_next_question(self):
        """Generate the next best question considering emotional state"""
        
        # Determine what information we still need
        missing_info = []
        if not self.customer_data.get("customer_name"):
            missing_info.append("customer name")
        if not self.customer_data.get("problem_description"):
            missing_info.append("detailed problem description")
        if not self.customer_data.get("order_id") and not self.customer_data.get("product_name"):
            missing_info.append("order ID or product details")
        if not self.customer_data.get("customer_phone") and not self.customer_data.get("customer_email"):
            missing_info.append("contact information")
        
        conversation_text = ""
        for msg in self.conversation_history:
            conversation_text += f"{msg['role']}: {msg['message']}\n"
        
        # Analyze current emotional state
        current_emotion = "neutral"
        emotion_context = ""
        if self.customer_emotions:
            latest_emotion = self.customer_emotions[-1]
            current_emotion = latest_emotion.get("emotion", "neutral")
            emotion_intensity = latest_emotion.get("intensity", "medium")
            emotion_keywords = latest_emotion.get("keywords", [])
            
            emotion_context = f"""
            Current customer emotional state: {current_emotion} (intensity: {emotion_intensity})
            Emotional keywords detected: {', '.join(emotion_keywords) if emotion_keywords else 'none'}
            """
        
        question_prompt = f"""
        You are an excellent customer service agent. Generate the next most important question considering the customer's emotional state.
        
        Conversation so far:
        {conversation_text}
        
        Current customer data: {json.dumps(self.customer_data)}
        Missing information: {', '.join(missing_info) if missing_info else 'Most info collected'}
        Question {self.question_count + 1} of {self.max_questions}
        
        {emotion_context}
        
        IMPORTANT: Adapt your tone based on the customer's emotion:
        - If angry/frustrated: Be extra empathetic, acknowledge their frustration, use calming language
        - If worried/disappointed: Be reassuring and supportive
        - If calm/neutral: Maintain professional, friendly tone
        - If satisfied: Continue with positive reinforcement
        
        Generate a natural, empathetic question (max 30 words) that:
        1. Gets the most critical missing information
        2. Addresses their emotional state appropriately
        3. Shows understanding of their feelings
        
        Return only the question, nothing else.
        """
        
        try:
            response = self.model.generate_content(
                question_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=100
                )
            )
            return response.text.strip()
        except Exception as e:
            # Fallback questions
            fallback_questions = [
                "Could you please tell me your name and describe your main concern?",
                "Can you provide more details about what happened and when?",
                "What would be the best way to resolve this issue for you?"
            ]
            return fallback_questions[min(self.question_count, 2)]
    
    def start_conversation(self):
        """Start the conversation"""
        print("\n" + "="*60)
        print("🤖 INTELLIGENT CUSTOMER SERVICE AGENT")
        print("💬 Text-Only Conversational Complaint Processing")
        print("="*60)
        
        # Initial greeting
        greeting = "Hello! I'm here to help you with your complaint today. To get started, could you please tell me your name and briefly describe the issue you're experiencing?"
        self.speak(greeting)
        self.conversation_history.append({"role": "agent", "message": greeting})
        
        # Conversation loop
        while self.question_count < self.max_questions:
            self.question_count += 1
            
            # Get customer response
            if self.question_count == 1:
                # First response to greeting
                customer_response = self.get_customer_input("Please tell me your name and describe your issue:")
            else:
                # Generate next question
                next_question = self.generate_next_question()
                self.speak(next_question)
                self.conversation_history.append({"role": "agent", "message": next_question})
                customer_response = self.get_customer_input()
            
            # Record customer response
            self.conversation_history.append({"role": "customer", "message": customer_response})
            
            # Extract information
            if self.question_count == 1:
                self.extract_info(greeting, customer_response)
            else:
                last_question = self.conversation_history[-3]["message"]  # Agent's last question
                self.extract_info(last_question, customer_response)
            
            print(f"\n📊 Updated customer data: {json.dumps(self.customer_data, indent=2)}")
            if self.customer_emotions:
                latest_emotion = self.customer_emotions[-1]
                print(f"😊 Current emotion: {latest_emotion.get('emotion', 'neutral')} ({latest_emotion.get('intensity', 'medium')} intensity)")
        
        # Final summary
        final_message = "Thank you for providing that information. I've recorded all the details about your complaint and we'll work on resolving this for you as soon as possible."
        self.speak(final_message)
        self.conversation_history.append({"role": "agent", "message": final_message})
        
        # Save conversation
        self.save_conversation()
        
        return self.create_final_output()
    
    def save_conversation(self):
        """Save the conversation to file"""
        os.makedirs("conversations", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversations/conversation_{timestamp}.json"
        
        conversation_data = {
            "timestamp": datetime.now().isoformat(),
            "conversation_history": self.conversation_history,
            "extracted_data": self.customer_data,
            "emotion_tracking": self.customer_emotions,
            "total_questions": self.question_count
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Conversation saved: {filename}")
    
    def _analyze_overall_emotion_intensity(self):
        """Analyze the overall emotional intensity throughout the conversation"""
        if not self.customer_emotions:
            return "neutral"
        
        intensities = [emotion.get("intensity", "medium") for emotion in self.customer_emotions if emotion.get("intensity")]
        
        # Count intensity levels
        high_count = intensities.count("high")
        medium_count = intensities.count("medium")
        low_count = intensities.count("low")
        
        if high_count > 0:
            return "high"
        elif medium_count > low_count:
            return "medium"
        else:
            return "low"
    
    def create_final_output(self):
        """Create structured final output"""
        return {
            "metadata": {
                "conversation_completed": datetime.now().isoformat(),
                "total_questions": self.question_count,
                "total_exchanges": len([msg for msg in self.conversation_history if msg["role"] == "customer"])
            },
            "conversation": {
                "full_history": self.conversation_history,
                "emotion_journey": self.customer_emotions
            },
            "customer_info": {
                "name": self.customer_data.get("customer_name"),
                "phone": self.customer_data.get("customer_phone"),
                "email": self.customer_data.get("customer_email")
            },
            "complaint_details": {
                "description": self.customer_data.get("problem_description"),
                "category": self.customer_data.get("problem_category"),
                "urgency_level": self.customer_data.get("urgency_level"),
                "order_id": self.customer_data.get("order_id"),
                "product_name": self.customer_data.get("product_name")
            },
            "company_info": {
                "company_name": self.customer_data.get("company_name")
            },
            "emotional_analysis": {
                "emotions_detected": [emotion.get("emotion") for emotion in self.customer_emotions if emotion.get("emotion")],
                "overall_intensity": self._analyze_overall_emotion_intensity(),
                "emotion_progression": self.customer_emotions
            },
            "status": "conversation_completed"
        }

def main():
    """Main function"""
    try:
        agent = SimpleConversationalAgent()
        result = agent.start_conversation()
        
        print("\n" + "="*60)
        print("✅ CONVERSATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📋 Final Summary:")
        print(json.dumps(result, indent=2))
        
    except KeyboardInterrupt:
        print("\n\n👋 Conversation ended by user.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()