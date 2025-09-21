import json
import os
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

# Import all prototype agents
from amazon_prototype_agent import AmazonCustomerServiceAgent
from flipkart_prototype_agent import FlipkartCustomerServiceAgent
from facebook_prototype_agent import FacebookCustomerServiceAgent

# Load environment variables
load_dotenv()

class UniversalCustomerServiceDispatcher:
    def __init__(self):
        # Initialize Groq for initial company detection
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            self.model = Groq(api_key=groq_api_key)
        else:
            raise Exception("GROQ_API_KEY not found")
        
        # Available company prototypes
        self.company_agents = {
            "amazon": AmazonCustomerServiceAgent,
            "flipkart": FlipkartCustomerServiceAgent,
            "facebook": FacebookCustomerServiceAgent
        }
        
        # Conversation state for initial routing
        self.initial_conversation = []
        self.detected_company = None
    
    def speak(self, text):
        """Display universal dispatcher response"""
        print(f"🎯 Universal Support: {text}")
    
    def get_customer_input(self, prompt="Please respond:"):
        """Get text input from customer"""
        print(f"\\n👤 {prompt}")
        response = input("Your response: ")
        return response
    
    def detect_company(self, customer_input):
        """Detect which company the customer is calling about"""
        detection_prompt = f"""
        Analyze this customer input to determine which company they are calling about:
        "{customer_input}"
        
        Look for indicators of:
        - Amazon: mentions of Amazon, Prime, Echo, Alexa, AWS, order numbers like 112-XXXXXXXXX, customer IDs like AMZN########
        - Flipkart: mentions of Flipkart, Flipkart Plus, Indian context, order numbers like OD##################, customer IDs like FKT#######
        - Facebook: mentions of Facebook, Meta, Instagram, WhatsApp, posts, accounts, usernames with @, customer IDs like FB###############
        
        Return as JSON:
        {{
            "company": "amazon" or "flipkart" or "facebook" or "unknown",
            "confidence": "high" or "medium" or "low",
            "indicators": ["list of indicators found"]
        }}
        
        Return only the JSON, nothing else.
        """
        
        try:
            result = self.model.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": detection_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse JSON response
            detection_data = json.loads(result.choices[0].message.content.strip())
            return detection_data
            
        except Exception as e:
            print(f"⚠️ Company detection failed: {e}")
            return {"company": "unknown", "confidence": "low", "indicators": []}
    
    def start_universal_conversation(self):
        """Start the universal customer service dispatcher"""
        print("\\n" + "="*70)
        print("🌟 UNIVERSAL CUSTOMER SERVICE DISPATCHER")
        print("💼 Supporting Amazon, Flipkart, and Facebook")
        print("🎯 Intelligent Company Detection & Routing")
        print("="*70)
        
        # Initial universal greeting
        greeting = "Hello! Welcome to Universal Customer Service. I can help you with issues related to Amazon, Flipkart, or Facebook. Please tell me which company you're calling about and describe your issue."
        self.speak(greeting)
        self.initial_conversation.append({"role": "agent", "message": greeting})
        
        # Get initial customer input
        initial_input = self.get_customer_input("Which company are you calling about and what's your issue?")
        self.initial_conversation.append({"role": "customer", "message": initial_input})
        
        # Detect company
        detection_result = self.detect_company(initial_input)
        self.detected_company = detection_result.get("company", "unknown")
        confidence = detection_result.get("confidence", "low")
        indicators = detection_result.get("indicators", [])
        
        print(f"\\n🔍 Company Detection Results:")
        print(f"   Detected: {self.detected_company.upper()}")
        print(f"   Confidence: {confidence}")
        print(f"   Indicators: {', '.join(indicators) if indicators else 'None'}")
        
        # Route to appropriate agent or ask for clarification
        if self.detected_company in self.company_agents and confidence in ["high", "medium"]:
            # Route to specific company agent
            routing_msg = f"Great! I've identified that you're calling about {self.detected_company.upper()}. Let me connect you to our specialized {self.detected_company.title()} support team."
            self.speak(routing_msg)
            self.initial_conversation.append({"role": "agent", "message": routing_msg})
            
            # Create and run the specific agent
            agent_class = self.company_agents[self.detected_company]
            agent = agent_class()
            
            # Transfer the initial conversation context to the agent
            agent.conversation_history = self.initial_conversation.copy()
            
            # Set initial company context
            agent.customer_data["company_name"] = self.detected_company.title()
            
            print(f"\\n🔄 Transferring to {self.detected_company.upper()} Support Team...")
            print("=" * 70)
            
            # Start the company-specific conversation
            return agent.start_conversation()
            
        else:
            # Company not detected or low confidence - ask for clarification
            clarification_msg = "I'm not sure which company you're calling about. Could you please clearly specify: Are you calling about Amazon, Flipkart, or Facebook?"
            self.speak(clarification_msg)
            self.initial_conversation.append({"role": "agent", "message": clarification_msg})
            
            # Get clarification
            clarification_input = self.get_customer_input("Please specify: Amazon, Flipkart, or Facebook?")
            self.initial_conversation.append({"role": "customer", "message": clarification_input})
            
            # Re-detect with clarification
            detection_result = self.detect_company(clarification_input)
            self.detected_company = detection_result.get("company", "unknown")
            
            if self.detected_company in self.company_agents:
                # Route after clarification
                routing_msg = f"Perfect! Connecting you to {self.detected_company.upper()} customer service."
                self.speak(routing_msg)
                self.initial_conversation.append({"role": "agent", "message": routing_msg})
                
                # Create and run the specific agent
                agent_class = self.company_agents[self.detected_company]
                agent = agent_class()
                
                # Transfer conversation context
                agent.conversation_history = self.initial_conversation.copy()
                agent.customer_data["company_name"] = self.detected_company.title()
                
                print(f"\\n🔄 Transferring to {self.detected_company.upper()} Support Team...")
                print("=" * 70)
                
                return agent.start_conversation()
            else:
                # Still couldn't detect - end with error
                error_msg = "I apologize, but we currently only support Amazon, Flipkart, and Facebook customer service. Please contact the company directly through their official channels."
                self.speak(error_msg)
                self.initial_conversation.append({"role": "agent", "message": error_msg})
                
                # Save the failed routing attempt
                self.save_failed_routing()
                
                return {
                    "conversation_completed": datetime.now().isoformat(),
                    "routing_status": "failed",
                    "detected_company": "unknown",
                    "customer_input": initial_input + " | " + clarification_input,
                    "status": "unsupported_company"
                }
    
    def save_failed_routing(self):
        """Save failed routing attempts for analysis"""
        os.makedirs("routing_logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"routing_logs/failed_routing_{timestamp}.json"
        
        routing_data = {
            "timestamp": datetime.now().isoformat(),
            "detected_company": self.detected_company,
            "conversation_history": self.initial_conversation,
            "status": "routing_failed"
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(routing_data, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Failed routing attempt logged: {filename}")

def main():
    """Main function to run the universal dispatcher"""
    try:
        dispatcher = UniversalCustomerServiceDispatcher()
        result = dispatcher.start_universal_conversation()
        
        print("\\n" + "="*70)
        if result.get("routing_status") == "failed":
            print("❌ ROUTING FAILED - UNSUPPORTED COMPANY")
        elif result.get("is_fraud_call"):
            print("🚨 FRAUD CALL DETECTED!")
            print("⚠️ Call terminated for security reasons")
        else:
            print("✅ CUSTOMER SERVICE COMPLETED SUCCESSFULLY!")
            company = result.get("company_name", "Unknown")
            customer = result.get("customer_name", "Customer")
            print(f"🏢 Company: {company}")
            print(f"👤 Customer: {customer}")
        print("="*70)
        
        print("\\n📋 Final Summary:")
        print(json.dumps(result, indent=2))
        
    except KeyboardInterrupt:
        print("\\n\\n👋 Universal customer service ended by user.")
    except Exception as e:
        print(f"\\n❌ Error in universal dispatcher: {str(e)}")

if __name__ == "__main__":
    main()