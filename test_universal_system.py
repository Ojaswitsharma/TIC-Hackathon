#!/usr/bin/env python3
"""
Test script for the Universal Customer Service Dispatcher
Demonstrates automatic company detection and routing
"""

import json
from datetime import datetime

def print_test_scenario(company, scenario_name, test_inputs):
    """Print test scenario information"""
    print("\\n" + "="*60)
    print(f"🧪 TESTING {company.upper()} - {scenario_name}")
    print("="*60)
    print(f"📝 Test Inputs: {test_inputs}")
    print(f"⏰ Expected Route: {company.title()} Support")
    print("-" * 60)

def main():
    """Test the universal dispatcher with sample scenarios"""
    print("\\n" + "="*70)
    print("🧪 UNIVERSAL DISPATCHER TEST SCENARIOS")
    print("💡 Sample test cases for company detection and routing")
    print("="*70)
    
    # Test scenarios for each company
    test_scenarios = {
        "amazon": [
            {
                "name": "Order Issue with ID",
                "input": "I have an issue with my Amazon order 112-1234567-8901234, it never arrived",
                "expected_indicators": ["Amazon", "order", "112-", "never arrived"]
            },
            {
                "name": "Prime Member Complaint", 
                "input": "My customer ID is AMZN001234567 and I'm having trouble with Prime delivery",
                "expected_indicators": ["AMZN", "Prime", "delivery"]
            },
            {
                "name": "Echo Device Issue",
                "input": "My Alexa Echo Dot is not responding, I bought it from Amazon last week",
                "expected_indicators": ["Alexa", "Echo", "Amazon"]
            }
        ],
        "flipkart": [
            {
                "name": "Flipkart Plus Member",
                "input": "I am calling about my Flipkart order OD112233445566778899, I'm a Plus member",
                "expected_indicators": ["Flipkart", "OD", "Plus member"]
            },
            {
                "name": "Customer ID Issue",
                "input": "My Flipkart customer ID FKT001234567, the product quality is very poor",
                "expected_indicators": ["Flipkart", "FKT", "quality"]
            },
            {
                "name": "Delivery Problem",
                "input": "Flipkart delivery was delayed, order still not received in Bangalore",
                "expected_indicators": ["Flipkart", "delivery", "delayed", "Bangalore"]
            }
        ],
        "facebook": [
            {
                "name": "Account Suspended",
                "input": "My Facebook account FB001234567890123 has been suspended wrongly",
                "expected_indicators": ["Facebook", "FB", "account", "suspended"]
            },
            {
                "name": "Username Issue",
                "input": "I can't access my Facebook account @alexjohnson2024, please help",
                "expected_indicators": ["Facebook", "@", "account", "access"]
            },
            {
                "name": "Content Removed",
                "input": "Facebook removed my post incorrectly, I need to appeal this decision",
                "expected_indicators": ["Facebook", "post", "removed", "appeal"]
            }
        ]
    }
    
    # Test valid customer examples for each company
    valid_customers = {
        "amazon": {
            "customer_id": "AMZN001234567",
            "phone": "+1-555-0123",
            "name": "John Smith"
        },
        "flipkart": {
            "customer_id": "FKT001234567", 
            "phone": "+91-98765-43210",
            "name": "Rajesh Kumar"
        },
        "facebook": {
            "customer_id": "FB001234567890123",
            "phone": "+1-555-0101", 
            "username": "@alexjohnson2024",
            "name": "Alex Johnson"
        }
    }
    
    # Test fraud detection examples
    fraud_examples = {
        "amazon": {
            "customer_id": "AMZN999999999",
            "phone": "+1-555-9999"
        },
        "flipkart": {
            "customer_id": "FKT999999999",
            "phone": "+91-99999-99999"
        },
        "facebook": {
            "customer_id": "FB999999999999999",
            "phone": "+1-555-9999"
        }
    }
    
    # Display test scenarios
    for company, scenarios in test_scenarios.items():
        print(f"\\n🏢 {company.upper()} TEST SCENARIOS:")
        print("-" * 50)
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\\n  {i}. {scenario['name']}")
            print(f"     Input: \"{scenario['input']}\"")
            print(f"     Expected Indicators: {', '.join(scenario['expected_indicators'])}")
        
        # Valid customer example
        valid = valid_customers[company]
        print(f"\\n  ✅ Valid Customer Example:")
        print(f"     ID: {valid.get('customer_id', 'N/A')}")
        print(f"     Phone: {valid.get('phone', 'N/A')}")
        if 'username' in valid:
            print(f"     Username: {valid['username']}")
        print(f"     Name: {valid['name']}")
        
        # Fraud example
        fraud = fraud_examples[company]
        print(f"\\n  🚨 Fraud Detection Example:")
        print(f"     Invalid ID: {fraud.get('customer_id', 'N/A')}")
        print(f"     Invalid Phone: {fraud.get('phone', 'N/A')}")
    
    # Usage instructions
    print("\\n" + "="*70)
    print("🚀 HOW TO TEST THE UNIVERSAL DISPATCHER")
    print("="*70)
    print("\\n1. Run the universal dispatcher:")
    print("   python universal_dispatcher.py")
    print("\\n2. Try any of the test inputs above")
    print("\\n3. Provide valid customer credentials to see full flow")
    print("\\n4. Try invalid credentials to test fraud detection")
    
    print("\\n🔧 SYSTEM COMPONENTS:")
    print("-" * 30)
    print("📁 customer_database.json     - Amazon customer data")
    print("📁 flipkart_database.json    - Flipkart customer data") 
    print("📁 facebook_database.json    - Facebook customer data")
    print("🤖 amazon_prototype_agent.py - Amazon support agent")
    print("🤖 flipkart_prototype_agent.py - Flipkart support agent")
    print("🤖 facebook_prototype_agent.py - Facebook support agent")
    print("🎯 universal_dispatcher.py   - Main routing system")
    
    print("\\n📊 OUTPUT LOCATIONS:")
    print("-" * 20)
    print("📂 output/ - Final complaint JSON files")
    print("📂 conversations/ - Full conversation logs")  
    print("📂 routing_logs/ - Failed routing attempts")
    
    print("\\n" + "="*70)
    print("✨ READY TO TEST! Run: python universal_dispatcher.py")
    print("="*70)

if __name__ == "__main__":
    main()