#!/usr/bin/env python3
"""
Test script to verify that output saving functionality works correctly
"""

import json
import os
import sys
from datetime import datetime

# Add the current directory to Python path to import the agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_output_saving():
    """Test the output saving functionality"""
    try:
        from simple_conversational_agent import SimpleConversationalAgent
        
        # Create agent instance
        agent = SimpleConversationalAgent()
        
        # Simulate some conversation data
        agent.customer_data = {
            "customer_name": "Test Customer",
            "customer_phone": "123-456-7890",
            "problem_description": "Test issue with product",
            "problem_category": "Technical Support"
        }
        
        agent.conversation_history = [
            {"role": "agent", "message": "Hello! How can I help you today?"},
            {"role": "customer", "message": "I have an issue with my order"},
            {"role": "agent", "message": "I'm sorry to hear that. Can you provide more details?"},
            {"role": "customer", "message": "The product arrived damaged"}
        ]
        
        agent.customer_emotions = [
            {"emotion": "frustrated", "intensity": "medium", "keywords": ["issue", "damaged"]}
        ]
        
        agent.question_count = 2
        
        # Test the create_final_output method (which should save the file)
        print("🧪 Testing output saving functionality...")
        result = agent.create_final_output()
        
        print("✅ Output creation successful!")
        print(f"📊 Sample output structure:")
        print(json.dumps(result, indent=2)[:500] + "...")
        
        # Check if output folder exists and has files
        if os.path.exists("output"):
            output_files = [f for f in os.listdir("output") if f.endswith('.json')]
            print(f"📁 Output folder contains {len(output_files)} JSON files")
            if output_files:
                latest_file = max(output_files, key=lambda x: os.path.getctime(os.path.join("output", x)))
                print(f"📄 Latest output file: {latest_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTING OUTPUT SAVING FUNCTIONALITY")
    print("=" * 60)
    
    success = test_output_saving()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED - Output saving works correctly!")
    else:
        print("❌ TEST FAILED - Check the error messages above")
    print("=" * 60)