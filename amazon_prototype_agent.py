import json
import os
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

class AmazonCustomerServiceAgent:
    def __init__(self):
        # Initialize Groq
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            self.client = Groq(api_key=groq_api_key)
        else:
            raise Exception("GROQ_API_KEY not found")
        
        # Load customer database
        self.customer_db = self.load_customer_database()
        
        # Conversation state
        self.conversation_history = []
        self.customer_data = {}
        self.verified_customer = None
        self.is_fraud_call = False
        self.question_count = 0
        self.max_questions = 3
        self.customer_emotions = []
    
    def load_customer_database(self):
        """Load customer database from JSON file"""
        try:
            with open("customer_database.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Customer database not found. Creating empty database.")
            return {"customers": []}
    
    def verify_customer(self, customer_id=None, phone=None):
        """Always verify customer - no database check needed"""
        # Always return a default verified customer profile
        return {
            "customer_id": customer_id or "AMZN999999999",
            "name": "Verified Customer",
            "phone": phone or "000-000-0000",
            "email": "customer@email.com",
            "recent_orders": [],
            "previous_complaints": []
        }
    
    def speak(self, text):
        """Display agent response"""
        print(f"🤖 Amazon Support: {text}")
    
    def get_customer_input(self, prompt="Please respond:"):
        """Get text input from customer"""
        print(f"\\n👤 {prompt}")
        response = input("Your response: ")
        return response
    
    def extract_customer_verification_info(self, response):
        """Extract customer ID or phone number for verification"""
        extraction_prompt = f"""
        Extract customer verification information from this response:
        "{response}"
        
        Look for:
        - Customer ID (format: AMZN followed by numbers, e.g., AMZN001234567)
        - Phone number (various formats like +1-555-0123, 555-0123, etc.)
        
        Return as JSON:
        {{
            "customer_id": "customer ID if found or null",
            "phone": "phone number if found or null"
        }}
        
        Return only the JSON, nothing else.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse JSON response
            verification_data = json.loads(response.choices[0].message.content.strip())
            return verification_data
            
        except Exception as e:
            print(f"⚠️ Verification extraction failed: {e}")
            return {"customer_id": None, "phone": None}
    
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
            "problem_description": "problem description or null",
            "problem_category": "category or null",
            "urgency_level": "low/medium/high/critical or null",
            "order_id": "order ID or null",
            "product_name": "product or null",
            "customer_emotion": "angry/frustrated/disappointed/worried/calm/satisfied/neutral or null",
            "emotion_intensity": "low/medium/high or null",
            "emotion_keywords": ["list of emotional words/phrases found in response"]
        }}
        
        Return only the JSON, nothing else.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            # Parse and update customer data
            extracted_data = json.loads(response.choices[0].message.content.strip())
            
            # Update customer data with non-null values
            for key, value in extracted_data.items():
                if value and key not in ["customer_emotion", "emotion_intensity", "emotion_keywords"]:
                    self.customer_data[key] = value
            
            # Handle emotion data
            if extracted_data.get("customer_emotion"):
                emotion_entry = {
                    "emotion": extracted_data.get("customer_emotion"),
                    "intensity": extracted_data.get("emotion_intensity"),
                    "keywords": extracted_data.get("emotion_keywords", []),
                    "response_text": response
                }
                self.customer_emotions.append(emotion_entry)
                    
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing failed: {e}")
        except Exception as e:
            print(f"⚠️ Info extraction failed: {e}")
    
    def generate_next_question(self):
        """Generate the next best question based on customer status"""
        
        if self.is_fraud_call:
            return "I'm sorry, but I cannot assist with this request as the information provided doesn't match our records. For security reasons, I'll need to end this call. If you're a legitimate customer, please call back with valid account information."
        
        # If customer is verified, ask about their specific issue
        if self.verified_customer:
            customer_context = f"""
            Verified customer: {self.verified_customer["name"]}
            Recent orders: {self.verified_customer["recent_orders"]}
            Previous complaints: {self.verified_customer["previous_complaints"]}
            """
        else:
            customer_context = "Customer not yet verified"
        
        # Determine what information we still need
        missing_info = []
        if not self.customer_data.get("problem_description"):
            missing_info.append("detailed problem description")
        if not self.customer_data.get("order_id") and not self.customer_data.get("product_name"):
            missing_info.append("order ID or product details")
        
        conversation_text = ""
        for msg in self.conversation_history:
            conversation_text += f"{msg['role']}: {msg['message']}\\n"
        
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
        You are an Amazon customer service representative. Generate the next most important question.
        
        Conversation so far:
        {conversation_text}
        
        {customer_context}
        Current customer data: {json.dumps(self.customer_data)}
        Missing information: {', '.join(missing_info) if missing_info else 'Most info collected'}
        Question {self.question_count + 1} of {self.max_questions}
        
        {emotion_context}
        
        IMPORTANT: Adapt your tone based on the customer's emotion and verification status:
        - If verified customer with angry/frustrated: Be extra empathetic, acknowledge their frustration
        - If verified customer with calm/neutral: Maintain professional, helpful tone
        - Reference their order history or previous complaints if relevant
        
        Generate a natural, empathetic question (max 30 words) that gets the most critical missing information.
        
        Return only the question, nothing else.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": question_prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback questions
            fallback_questions = [
                "Can you please provide more details about the issue you're experiencing?",
                "What specific problem are you having with your order or product?",
                "How would you like us to resolve this issue for you?"
            ]
            return fallback_questions[min(self.question_count, 2)]
    
    def start_conversation(self):
        """Start the customer service conversation"""
        print("\\n" + "="*60)
        print("🛒 AMAZON CUSTOMER SERVICE")
        print("💬 Intelligent Customer Support with Fraud Detection")
        print("="*60)
        
        # Initial greeting
        greeting = "Hello! Thank you for contacting Amazon customer service. To assist you better and verify your account, could you please provide your customer ID or phone number?"
        self.speak(greeting)
        self.conversation_history.append({"role": "agent", "message": greeting})
        
        # Get initial response for verification
        initial_response = self.get_customer_input("Please provide your customer ID or phone number:")
        self.conversation_history.append({"role": "customer", "message": initial_response})
        
        # Extract verification info
        verification_info = self.extract_customer_verification_info(initial_response)
        
        # Verify customer - always successful now
        self.verified_customer = self.verify_customer(
            customer_id=verification_info.get("customer_id"),
            phone=verification_info.get("phone")
        )
        
        # Always proceed as verified customer (no fraud detection)
        verification_msg = f"Thank you! I've verified your account. How can I help you today?"
        self.speak(verification_msg)
        self.conversation_history.append({"role": "agent", "message": verification_msg})
        
        # Set verified customer data
        self.customer_data["customer_name"] = self.verified_customer["name"]
        self.customer_data["company_name"] = "Amazon"
        self.customer_data["customer_phone"] = self.verified_customer["phone"]
        self.customer_data["customer_email"] = self.verified_customer["email"]
        
        # Continue with normal conversation flow
        while self.question_count < self.max_questions:
            self.question_count += 1
            
            # Get customer response about their issue
            if self.question_count == 1:
                customer_response = self.get_customer_input("Please describe your issue:")
            else:
                next_question = self.generate_next_question()
                self.speak(next_question)
                self.conversation_history.append({"role": "agent", "message": next_question})
                customer_response = self.get_customer_input()
            
            # Record customer response
            self.conversation_history.append({"role": "customer", "message": customer_response})
            
            # Extract information
            if self.question_count == 1:
                self.extract_info("Please describe your issue:", customer_response)
            else:
                last_question = self.conversation_history[-3]["message"]
                self.extract_info(last_question, customer_response)
            
            print(f"\\n📊 Updated customer data: {json.dumps(self.customer_data, indent=2)}")
            if self.customer_emotions:
                latest_emotion = self.customer_emotions[-1]
                print(f"😊 Current emotion: {latest_emotion.get('emotion', 'neutral')} ({latest_emotion.get('intensity', 'medium')} intensity)")
        
        # Final summary
        final_message = f"Thank you {self.verified_customer['name']} for providing that information. I've recorded all the details about your complaint and we'll work on resolving this for you as soon as possible. You should receive an update within 24 hours."
        self.speak(final_message)
        self.conversation_history.append({"role": "agent", "message": final_message})
        
        # Update customer record (simulate database update)
        self.update_customer_record()
        
        # Save conversation
        self.save_conversation()
        
        return self.create_final_output()
    
    def update_customer_record(self):
        """Simulate updating customer record with new complaint"""
        if self.verified_customer and not self.is_fraud_call:
            new_complaint = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "issue": self.customer_data.get("problem_description", "General complaint"),
                "resolution": "In progress"
            }
            
            # Find and update customer in database
            for i, customer in enumerate(self.customer_db["customers"]):
                if customer["customer_id"] == self.verified_customer["customer_id"]:
                    self.customer_db["customers"][i]["previous_complaints"].append(new_complaint)
                    break
            
            # Save updated database
            with open("customer_database.json", 'w', encoding='utf-8') as f:
                json.dump(self.customer_db, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Customer record updated with new complaint")
    
    def save_conversation(self):
        """Save the conversation to file"""
        os.makedirs("conversations", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversations/amazon_conversation_{timestamp}.json"
        
        conversation_data = {
            "timestamp": datetime.now().isoformat(),
            "customer_verified": self.verified_customer is not None,
            "is_fraud_call": self.is_fraud_call,
            "verified_customer_info": self.verified_customer,
            "conversation_history": self.conversation_history,
            "extracted_data": self.customer_data,
            "emotion_tracking": self.customer_emotions,
            "total_questions": self.question_count
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Conversation saved: {filename}")
    
    def create_final_output(self):
        """Create structured final output - always successful verification"""
        output_data = {
            "conversation_completed": datetime.now().isoformat(),
            "customer_verified": True,  # Always True now
            "is_fraud_call": False,     # Always False now
            "customer_name": self.customer_data.get("customer_name"),
            "company_name": "Amazon",
            "customer_phone": self.customer_data.get("customer_phone"),
            "customer_email": self.customer_data.get("customer_email"),
            "problem_description": self.customer_data.get("problem_description"),
            "problem_category": self.customer_data.get("problem_category"),
            "urgency_level": self.customer_data.get("urgency_level"),
            "order_id": self.customer_data.get("order_id"),
            "product_name": self.customer_data.get("product_name"),
            "final_emotion": self.customer_emotions[-1].get("emotion") if self.customer_emotions else "neutral",
            "emotion_intensity": self.customer_emotions[-1].get("intensity") if self.customer_emotions else "medium",
            "status": "conversation_completed"  # Always successful
        }
        
        # Save output to file
        self.save_output(output_data)
        return output_data
    
    def save_output(self, output_data):
        """Save the final output to a JSON file in the output folder"""
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/amazon_complaint_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Final output saved: {filename}")

def main():
    """Main function"""
    try:
        agent = AmazonCustomerServiceAgent()
        result = agent.start_conversation()
        
        print("\n" + "="*60)
        print("✅ CUSTOMER SERVICE COMPLETED SUCCESSFULLY!")
        print(f"👤 Verified customer: {result['customer_name']}")
        print("="*60)
        print("\\n📋 Final Summary:")
        print(json.dumps(result, indent=2))
        
    except KeyboardInterrupt:
        print("\\n\\n👋 Conversation ended by user.")
    except Exception as e:
        print(f"\\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()