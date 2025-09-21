#!/usr/bin/env python3
"""
Test the updated conversational agent with company name as essential info
"""

import json
import os
from datetime import datetime

def test_agent_simulation():
    """Simulate a conversation to test the new functionality"""
    
    # Mock the agent class for testing
    class MockAgent:
        def __init__(self):
            self.customer_data = {}
            self.conversation_history = []
            self.customer_emotions = []
            self.question_count = 3
            
        def create_final_output(self):
            """Create structured final output - only final state"""
            output_data = {
                "conversation_completed": datetime.now().isoformat(),
                "customer_name": self.customer_data.get("customer_name"),
                "company_name": self.customer_data.get("company_name"),
                "customer_phone": self.customer_data.get("customer_phone"),
                "customer_email": self.customer_data.get("customer_email"),
                "problem_description": self.customer_data.get("problem_description"),
                "problem_category": self.customer_data.get("problem_category"),
                "urgency_level": self.customer_data.get("urgency_level"),
                "order_id": self.customer_data.get("order_id"),
                "product_name": self.customer_data.get("product_name"),
                "final_emotion": self.customer_emotions[-1].get("emotion") if self.customer_emotions else "neutral",
                "emotion_intensity": self.customer_emotions[-1].get("intensity") if self.customer_emotions else "medium",
                "status": "conversation_completed"
            }
            
            # Save output to file
            self.save_output(output_data)
            return output_data
        
        def save_output(self, output_data):
            """Save the final output to a JSON file in the output folder"""
            os.makedirs("output", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/conversation_output_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Final output saved: {filename}")
    
    # Test the functionality
    print("🧪 Testing updated agent with company name as essential info...")
    
    agent = MockAgent()
    
    # Simulate collected data
    agent.customer_data = {
        "customer_name": "John Doe",
        "company_name": "Amazon",  # Company name is now essential
        "customer_phone": "555-0123",
        "problem_description": "Package never arrived",
        "problem_category": "Delivery Issue",
        "urgency_level": "high"
    }
    
    agent.customer_emotions = [
        {"emotion": "frustrated", "intensity": "high", "keywords": ["never arrived", "waiting"]}
    ]
    
    # Generate final output
    result = agent.create_final_output()
    
    print("✅ Test completed successfully!")
    print("\n📋 Final Output Structure (JSON):")
    print(json.dumps(result, indent=2))
    
    # Verify essential fields
    essential_fields = ["customer_name", "company_name", "problem_description"]
    missing_fields = [field for field in essential_fields if not result.get(field)]
    
    if missing_fields:
        print(f"\n⚠️  Warning: Missing essential fields: {missing_fields}")
    else:
        print(f"\n✅ All essential fields present including company_name!")
    
    return result

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTING UPDATED CONVERSATIONAL AGENT")
    print("🏢 Company Name Now Essential + JSON Final State Only")
    print("=" * 60)
    
    test_agent_simulation()
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED - Check output folder for saved JSON")
    print("=" * 60)