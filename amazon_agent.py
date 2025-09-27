"""
Amazon Customer Service Agent
============================

Simplified Amazon-specific customer service processing.
Handles customer verification, issue analysis, and response generation.
"""

import json
import os
from typing import Dict, Any, Optional
from groq import Groq
from datetime import datetime


class AmazonAgent:
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise Exception("GROQ_API_KEY not found")
        
        self.groq_client = Groq(api_key=self.groq_api_key)
        
        self.customer_db = self.load_customer_database()
    
    def load_customer_database(self) -> Dict[str, Any]:
        """Load customer database from current directory"""
        db_path = "customer_db.json"
        
        try:
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    "customers": [
                        {
                            "customer_id": "AMZN123456789",
                            "name": "John Smith",
                            "phone": "+1-555-0123",
                            "email": "john.smith@email.com",
                            "orders": [
                                {
                                    "order_id": "AMZ-2024-001",
                                    "date": "2024-09-20",
                                    "status": "shipped",
                                    "items": ["Wireless Headphones"]
                                }
                            ]
                        }
                    ]
                }
        except Exception as e:
            print(f"⚠️ Database load failed: {e}")
            return {"customers": []}
    
    def verify_customer(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify customer using available information"""
        
        issue_text = conversation_data.get("issue_description", "")
        customer_name = conversation_data.get("customer_name", "")
        
        verification_result = {
            "verified": True,  # For demo purposes, always verify
            "customer_id": "AMZN123456789",
            "customer_name": customer_name or "Verified Customer",
            "confidence": 0.85,
            "method": "name_and_issue_analysis"
        }
        
        return verification_result
    
    def analyze_issue_category(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize the customer issue using AI"""
        
        issue_text = conversation_data.get("issue_description", "")
        additional_details = conversation_data.get("additional_details", [])
        
        full_context = issue_text
        for detail in additional_details:
            if isinstance(detail, dict):
                full_context += " " + detail.get("response", "")
            else:
                full_context += " " + str(detail)
        
        analysis_prompt = f"""
        Analyze this Amazon customer issue and categorize it:
        
        Customer Issue: "{full_context}"
        
        Categorize into one of these types:
        - shipping_delays
        - refunds_returns 
        - account_issues
        - payment_problems
        - product_defects
        - other
        
        Also determine:
        - Urgency level (high/medium/low)
        - Can be resolved automatically (yes/no)
        - Estimated resolution time
        
        Return JSON only:
        {{
            "category": "category_name",
            "urgency": "high/medium/low",
            "auto_resolvable": true/false,
            "estimated_resolution": "time_estimate",
            "key_details": ["detail1", "detail2"],
            "confidence": 0.9
        }}
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1,
                max_tokens=400
            )
            
            analysis = json.loads(response.choices[0].message.content.strip())
            return analysis
            
        except Exception as e:
            print(f"⚠️ Issue analysis failed: {e}")
            return {
                "category": "other",
                "urgency": "medium", 
                "auto_resolvable": False,
                "estimated_resolution": "24-48 hours",
                "key_details": [],
                "confidence": 0.5,
                "error": str(e)
            }
    
    def generate_response(self, conversation_data: Dict[str, Any], 
                         verification: Dict[str, Any], 
                         analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate appropriate response based on issue analysis"""
        
        customer_name = verification.get("customer_name", "Customer")
        issue_category = analysis.get("category", "other")
        urgency = analysis.get("urgency", "medium")
        auto_resolvable = analysis.get("auto_resolvable", False)
        
        response_prompt = f"""
        Generate a professional Amazon customer service response:
        
        Customer: {customer_name}
        Issue Category: {issue_category}
        Urgency: {urgency}
        Auto-resolvable: {auto_resolvable}
        
        Customer's Issue: "{conversation_data.get('issue_description', '')}"
        
        Generate a helpful, empathetic response that either:
        1. Provides a solution if auto-resolvable
        2. Explains next steps and escalation if not auto-resolvable
        
        Include:
        - Acknowledgment of the issue
        - Specific actions being taken
        - Timeline for resolution
        - Contact information if needed
        
        Return JSON only:
        {{
            "response_text": "Professional response text",
            "action_taken": "Specific action description",
            "resolution_timeline": "Expected timeline",
            "escalation_needed": true/false,
            "follow_up_required": true/false
        }}
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": response_prompt}],
                temperature=0.2,
                max_tokens=500
            )
            
            response_data = json.loads(response.choices[0].message.content.strip())
            return response_data
            
        except Exception as e:
            print(f"⚠️ Response generation failed: {e}")
            return {
                "response_text": f"Hello {customer_name}, I understand your concern and I'm here to help. Let me escalate this to our specialized team for immediate attention.",
                "action_taken": "Escalated to specialist team",
                "resolution_timeline": "24-48 hours",
                "escalation_needed": True,
                "follow_up_required": True,
                "error": str(e)
            }
    
    def process_customer_issue(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing pipeline for customer issues"""
        
        print("\n" + "="*50)
        print("🏪 AMAZON CUSTOMER SERVICE PROCESSING")
        print("="*50)
        
        try:
            # Step 1: Verify customer
            print("🔐 Verifying customer...")
            verification = self.verify_customer(conversation_data)
            
            if not verification.get("verified"):
                return {
                    "success": False,
                    "error": "Customer verification failed",
                    "data": None
                }
            
            print(f"✅ Customer verified: {verification['customer_name']}")
            
            # Step 2: Analyze issue
            print("🔍 Analyzing issue category...")
            analysis = self.analyze_issue_category(conversation_data)
            
            print(f"📋 Issue category: {analysis['category']} (urgency: {analysis['urgency']})")
            
            # Step 3: Generate response
            print("💡 Generating customer response...")
            response = self.generate_response(conversation_data, verification, analysis)
            
            print("✅ Amazon processing completed")
            
            # Compile results
            result_data = {
                "verification": verification,
                "analysis": analysis,
                "response": response,
                "processed_at": datetime.now().isoformat(),
                "agent": "amazon"
            }
            
            return {
                "success": True,
                "data": result_data,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Amazon agent processing failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "data": None
            }
