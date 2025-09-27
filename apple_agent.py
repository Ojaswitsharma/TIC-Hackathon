"""
Apple Customer Service Agent
============================

Apple-specific customer service processing.
Handles customer verification, issue analysis, and response generation.
"""

import json
import os
from typing import Dict, Any, Optional
from groq import Groq
from datetime import datetime


class AppleAgent:
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise Exception("GROQ_API_KEY not found")
        
        self.groq_client = Groq(api_key=self.groq_api_key)
        
        self.customer_db = self.load_customer_database()
    
    def load_customer_database(self) -> Dict[str, Any]:
        """Load Apple customer database"""
        return {
            "customers": [
                {
                    "customer_id": "APPL123456789",
                    "name": "Jane Doe",
                    "phone": "+1-555-0124",
                    "email": "jane.doe@email.com",
                    "devices": [
                        {
                            "serial": "F2LLD0HFJK",
                            "model": "MacBook Pro 13-inch",
                            "purchase_date": "2024-09-15",
                            "warranty_status": "active"
                        }
                    ]
                }
            ]
        }
    
    def verify_customer(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify Apple customer"""
        # Simple implementation - in reality would check Apple ID, device serial, etc.
        return {
            "verified": True,
            "customer_name": conversation_data.get("customer_name", "Customer"),
            "customer_id": "APPL123456789"
        }
    
    def analyze_issue_category(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Apple-specific issue categories"""
        issue_text = conversation_data.get("issue_description", "").lower()
        
        # Apple-specific categories
        if any(word in issue_text for word in ["screen", "display", "broken", "cracked"]):
            category = "hardware_repair"
            urgency = "high"
        elif any(word in issue_text for word in ["battery", "charging", "power"]):
            category = "battery_issue" 
            urgency = "medium"
        elif any(word in issue_text for word in ["ios", "update", "software", "app"]):
            category = "software_issue"
            urgency = "low"
        elif any(word in issue_text for word in ["warranty", "applecare", "repair"]):
            category = "warranty_service"
            urgency = "medium"
        else:
            category = "general_support"
            urgency = "medium"
            
        return {
            "category": category,
            "urgency": urgency,
            "auto_resolvable": category in ["software_issue", "general_support"]
        }
    
    def generate_response(self, conversation_data: Dict[str, Any], 
                         verification: Dict[str, Any], 
                         analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Apple-specific response"""
        
        customer_name = verification.get("customer_name", "Customer")
        category = analysis.get("category", "general")
        
        # Apple-specific responses
        if category == "hardware_repair":
            response_text = f"Hi {customer_name}, I understand your Apple device needs repair. I can schedule a Genius Bar appointment or arrange mail-in repair service. Your device may be covered under warranty or AppleCare."
            proposed_actions = ["Schedule Genius Bar appointment", "Arrange mail-in repair", "Check warranty coverage"]
            
        elif category == "battery_issue":
            response_text = f"Hi {customer_name}, battery issues can often be resolved. I can run diagnostics and if needed, schedule a battery replacement. Battery service is available for most Apple devices."
            proposed_actions = ["Run battery diagnostics", "Schedule battery replacement", "Provide battery tips"]
            
        elif category == "software_issue":
            response_text = f"Hi {customer_name}, software issues can usually be resolved with troubleshooting steps. I can guide you through iOS/macOS fixes or help with app-related problems."
            proposed_actions = ["iOS troubleshooting", "App reinstallation", "Software update guidance"]
            
        else:
            response_text = f"Hi {customer_name}, thank you for contacting Apple Support. I'm here to help with your Apple device or service inquiry."
            proposed_actions = ["General troubleshooting", "Product information", "Service options"]
        
        return {
            "response_text": response_text,
            "proposed_actions": proposed_actions,
            "confidence_score": 0.85,
            "estimated_resolution_time": "15-30 minutes"
        }
    
    def process_customer_issue(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing pipeline for Apple customer issues"""
        
        print("\n" + "="*50)
        print("🍎 APPLE CUSTOMER SERVICE PROCESSING")
        print("="*50)
        
        try:
            # Step 1: Verify customer
            print("🔐 Verifying Apple customer...")
            verification = self.verify_customer(conversation_data)
            
            if not verification.get("verified"):
                return {
                    "success": False,
                    "error": "Customer verification failed",
                    "data": None
                }
            
            print(f"✅ Customer verified: {verification['customer_name']}")
            
            # Step 2: Analyze issue
            print("🔍 Analyzing Apple issue category...")
            analysis = self.analyze_issue_category(conversation_data)
            
            print(f"📋 Issue category: {analysis['category']} (urgency: {analysis['urgency']})")
            
            # Step 3: Generate response
            print("💡 Generating Apple customer response...")
            response = self.generate_response(conversation_data, verification, analysis)
            
            print(f"✅ Response generated (confidence: {response['confidence_score']:.1%})")
            
            return {
                "success": True,
                "data": {
                    "verification": verification,
                    "analysis": analysis,
                    "response": response
                }
            }
            
        except Exception as e:
            print(f"❌ Apple agent processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
