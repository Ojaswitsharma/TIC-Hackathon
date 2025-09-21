"""
Intelligent Solution Agent
=========================

This module processes customer service outputs and determines if the problem can be solved
based on available data and protocols, or if escalation to department heads is needed.

Key Functions:
1. Analyze prototype output (Amazon/Facebook)
2. Cross-reference with customer database
3. Apply RAG-based protocols for problem resolution
4. Generate human-like solution responses
5. Route to appropriate department heads when needed
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class IntelligentSolutionAgent:
    """AI-powered solution agent that can resolve customer issues or escalate appropriately"""
    
    def __init__(self):
        """Initialize the solution agent with AI capabilities"""
        # Initialize Groq
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise Exception("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=groq_api_key)
        
        # Load customer databases
        self.amazon_database = self.load_database("customer_database.json")
        self.facebook_database = self.load_database("facebook_database.json")
        
        # Define department heads and their specialties
        self.department_heads = {
            "amazon": {
                "shipping_delays": {
                    "head": "Sarah Mitchell - Head of Logistics",
                    "email": "s.mitchell@amazon.com",
                    "phone": "+1-800-SHIP-AMZ"
                },
                "refunds_returns": {
                    "head": "Michael Chen - Head of Customer Refunds",
                    "email": "m.chen@amazon.com", 
                    "phone": "+1-800-REFUND-AMZ"
                },
                "account_issues": {
                    "head": "Jessica Williams - Head of Account Security",
                    "email": "j.williams@amazon.com",
                    "phone": "+1-800-ACCOUNT-AMZ"
                },
                "payment_issues": {
                    "head": "David Rodriguez - Head of Payment Services",
                    "email": "d.rodriguez@amazon.com",
                    "phone": "+1-800-PAY-AMZ"
                }
            },
            "facebook": {
                "account_suspension": {
                    "head": "Emily Davis - Head of Account Appeals",
                    "email": "e.davis@facebook.com",
                    "phone": "+1-800-FB-APPEAL"
                },
                "content_moderation": {
                    "head": "Robert Johnson - Head of Content Policy",
                    "email": "r.johnson@facebook.com",
                    "phone": "+1-800-FB-CONTENT"
                },
                "privacy_security": {
                    "head": "Lisa Thompson - Head of Privacy & Security",
                    "email": "l.thompson@facebook.com",
                    "phone": "+1-800-FB-PRIVACY"
                },
                "business_support": {
                    "head": "Mark Anderson - Head of Business Support",
                    "email": "m.anderson@facebook.com",
                    "phone": "+1-800-FB-BIZ"
                }
            }
        }
        
        # Define solution protocols based on RAG knowledge
        self.solution_protocols = {
            "amazon": {
                "shipping_delays": {
                    "solvable_conditions": ["order_exists", "delay_under_7_days", "customer_verified"],
                    "actions": ["issue_refund", "expedite_shipping", "provide_tracking"],
                    "compensation": ["partial_refund", "free_shipping_upgrade", "amazon_credit"]
                },
                "refunds_returns": {
                    "solvable_conditions": ["order_exists", "within_return_window", "customer_verified"],
                    "actions": ["process_refund", "generate_return_label", "schedule_pickup"],
                    "compensation": ["full_refund", "store_credit", "exchange_product"]
                },
                "account_issues": {
                    "solvable_conditions": ["account_exists", "phone_verified", "no_security_flags"],
                    "actions": ["reset_password", "update_security", "verify_identity"],
                    "compensation": ["account_restoration", "security_enhancement"]
                }
            },
            "facebook": {
                "content_moderation": {
                    "solvable_conditions": ["content_exists", "appeal_window_open", "user_verified"],
                    "actions": ["review_content", "restore_post", "provide_explanation"],
                    "compensation": ["content_restoration", "policy_clarification"]
                },
                "account_suspension": {
                    "solvable_conditions": ["account_exists", "suspension_reviewable", "user_verified"],
                    "actions": ["review_suspension", "restore_account", "provide_guidelines"],
                    "compensation": ["account_restoration", "policy_education"]
                }
            }
        }
    
    def load_database(self, filename: str) -> Dict[str, Any]:
        """Load customer database from JSON file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Warning: {filename} not found")
            return {"customers": []}
    
    def analyze_prototype_output(self, output_file: str) -> Dict[str, Any]:
        """Analyze the prototype output file and extract key information"""
        try:
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            # Extract key information
            analysis = {
                "company": data.get("original_conversation", {}).get("company_info", {}).get("company_name", "").lower(),
                "customer_verified": data.get("customer_verification", {}).get("verified", False),
                "fraud_detected": data.get("processing_status", {}).get("fraud_detected", False),
                "customer_info": data.get("original_conversation", {}).get("customer_info", {}),
                "complaint_info": data.get("original_conversation", {}).get("complaint_info", {}),
                "conversation_history": data.get("original_conversation", {}).get("conversation_history", [])
            }
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing prototype output: {str(e)}")
            return {}
    
    def find_customer_in_database(self, phone: str, company: str) -> Optional[Dict[str, Any]]:
        """Find customer in the appropriate database"""
        database = self.amazon_database if company == "amazon" else self.facebook_database
        
        for customer in database.get("customers", []):
            if customer.get("phone") == phone:
                return customer
        
        return None
    
    def determine_issue_category(self, complaint: Dict[str, Any], company: str) -> str:
        """Determine the issue category based on complaint information using AI"""
        
        complaint_text = complaint.get("description", "")
        category = complaint.get("category", "")
        
        # Use AI to categorize the issue more intelligently
        categorization_prompt = f"""
        Analyze this customer complaint and categorize it for {company.title()} customer service:
        
        Complaint: "{complaint_text}"
        Initial Category: "{category}"
        
        For Amazon, choose from: shipping_delays, refunds_returns, account_issues, payment_issues
        For Facebook, choose from: account_suspension, content_moderation, privacy_security, business_support
        
        Return only the category name, nothing else.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": categorization_prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            return response.choices[0].message.content.strip().lower()
        except:
            # Fallback to simple keyword matching
            if company == "amazon":
                if any(word in complaint_text.lower() for word in ["delay", "shipping", "delivery"]):
                    return "shipping_delays"
                elif any(word in complaint_text.lower() for word in ["refund", "return", "money"]):
                    return "refunds_returns"
                elif any(word in complaint_text.lower() for word in ["account", "login", "password"]):
                    return "account_issues"
                else:
                    return "refunds_returns"  # Default
            else:  # Facebook
                if any(word in complaint_text.lower() for word in ["suspended", "banned", "disabled"]):
                    return "account_suspension"
                elif any(word in complaint_text.lower() for word in ["post", "content", "removed"]):
                    return "content_moderation"
                else:
                    return "content_moderation"  # Default
    
    def check_solvability(self, analysis: Dict[str, Any], customer_data: Optional[Dict], issue_category: str) -> Dict[str, Any]:
        """Check if the issue can be solved based on available data and protocols"""
        
        company = analysis["company"]
        protocols = self.solution_protocols.get(company, {}).get(issue_category, {})
        
        if not protocols:
            return {"solvable": False, "reason": "No protocols defined for this issue category"}
        
        solvable_conditions = protocols.get("solvable_conditions", [])
        results = {"solvable": True, "failed_conditions": [], "met_conditions": []}
        
        # Check each condition
        for condition in solvable_conditions:
            if condition == "customer_verified":
                if analysis["customer_verified"] and not analysis["fraud_detected"]:
                    results["met_conditions"].append(condition)
                else:
                    results["failed_conditions"].append(condition)
                    
            elif condition == "order_exists" or condition == "account_exists" or condition == "content_exists":
                if customer_data:
                    results["met_conditions"].append(condition)
                else:
                    results["failed_conditions"].append(condition)
                    
            elif condition == "phone_verified":
                if customer_data and customer_data.get("phone") == analysis["customer_info"].get("phone"):
                    results["met_conditions"].append(condition)
                else:
                    results["failed_conditions"].append(condition)
                    
            elif condition in ["delay_under_7_days", "within_return_window", "appeal_window_open", "suspension_reviewable"]:
                # These would require more complex date calculations - for demo, assume true
                results["met_conditions"].append(condition)
                
            elif condition in ["no_security_flags", "user_verified"]:
                if customer_data and customer_data.get("account_status") == "active":
                    results["met_conditions"].append(condition)
                else:
                    results["failed_conditions"].append(condition)
        
        # Issue is solvable if all conditions are met
        results["solvable"] = len(results["failed_conditions"]) == 0
        
        return results
    
    def generate_solution_response(self, analysis: Dict[str, Any], customer_data: Optional[Dict], 
                                 issue_category: str, solvability: Dict[str, Any]) -> str:
        """Generate a human-like solution response using AI"""
        
        company = analysis["company"]
        customer_name = analysis["customer_info"].get("name", "valued customer")
        complaint = analysis["complaint_info"].get("description", "")
        
        if solvability["solvable"]:
            # Generate solution response
            protocols = self.solution_protocols.get(company, {}).get(issue_category, {})
            actions = protocols.get("actions", [])
            compensation = protocols.get("compensation", [])
            
            solution_prompt = f"""
            You are a professional customer service agent for {company.title()}. A customer named {customer_name} has contacted us with this issue:
            
            "{complaint}"
            
            Based on our protocols, you can take these actions: {', '.join(actions)}
            You can offer this compensation: {', '.join(compensation)}
            
            Generate a warm, professional response that:
            1. Acknowledges the customer's frustration
            2. Explains how you will solve the problem
            3. Specifies the actions you're taking
            4. Offers appropriate compensation
            5. Provides next steps and timeline
            
            Write as if you are personally solving their problem right now. Be specific and reassuring.
            """
            
        else:
            # Generate escalation response
            dept_info = self.get_department_head(company, issue_category)
            
            solution_prompt = f"""
            You are a professional customer service agent for {company.title()}. A customer named {customer_name} has contacted us with this issue:
            
            "{complaint}"
            
            Unfortunately, this issue requires specialized expertise that goes beyond standard protocols. You need to route them to:
            {dept_info['head']} - {dept_info['email']} - {dept_info['phone']}
            
            Generate a professional response that:
            1. Acknowledges the customer's concern
            2. Explains why this needs specialized attention
            3. Introduces the department head who will help them
            4. Provides the contact information
            5. Sets expectations for follow-up
            6. Apologizes for any inconvenience
            
            Be empathetic and ensure they feel their issue is being taken seriously.
            """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": solution_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"🚨 ERROR in generate_solution_response: {str(e)}")
            print(f"🔍 Error type: {type(e).__name__}")
            return f"I apologize, but I'm experiencing technical difficulties. Please contact our support team directly."
    
    def get_department_head(self, company: str, issue_category: str) -> Dict[str, str]:
        """Get the appropriate department head for escalation"""
        return self.department_heads.get(company, {}).get(issue_category, {
            "head": "Customer Service Manager",
            "email": "support@" + company + ".com",
            "phone": "+1-800-SUPPORT"
        })
    
    def process_customer_issue(self, output_file: str) -> Dict[str, Any]:
        """Main method to process customer issue and generate solution"""
        
        print("🤖 INTELLIGENT SOLUTION AGENT")
        print("="*50)
        
        # Step 1: Analyze prototype output
        print("📊 Analyzing customer service output...")
        analysis = self.analyze_prototype_output(output_file)
        
        if not analysis:
            return {"error": "Failed to analyze prototype output"}
        
        company = analysis["company"]
        customer_phone = analysis["customer_info"].get("phone", "")
        
        print(f"🏢 Company: {company.title()}")
        print(f"👤 Customer: {analysis['customer_info'].get('name', 'Unknown')}")
        print(f"📞 Phone: {customer_phone}")
        print(f"🔍 Fraud Detected: {'Yes' if analysis['fraud_detected'] else 'No'}")
        print(f"✅ Verified: {'Yes' if analysis['customer_verified'] else 'No'}")
        
        # Step 2: Find customer in database
        print("\\n🔍 Searching customer database...")
        customer_data = self.find_customer_in_database(customer_phone, company)
        
        if customer_data:
            print(f"✅ Customer found in {company} database")
            print(f"📧 Email: {customer_data.get('email', 'N/A')}")
            print(f"🏠 Account Status: {customer_data.get('account_status', 'N/A')}")
        else:
            print(f"❌ Customer not found in {company} database")
        
        # Step 3: Categorize the issue
        print("\\n🏷️ Categorizing customer issue...")
        issue_category = self.determine_issue_category(analysis["complaint_info"], company)
        print(f"📋 Issue Category: {issue_category.replace('_', ' ').title()}")
        
        # Step 4: Check solvability
        print("\\n⚖️ Checking issue solvability...")
        solvability = self.check_solvability(analysis, customer_data, issue_category)
        
        if solvability["solvable"]:
            print("✅ Issue can be resolved by our agent")
            print(f"📝 Met Conditions: {', '.join(solvability['met_conditions'])}")
        else:
            print("🔄 Issue requires escalation to department head")
            print(f"❌ Failed Conditions: {', '.join(solvability['failed_conditions'])}")
        
        # Step 5: Generate solution response
        print("\\n💬 Generating solution response...")
        solution_response = self.generate_solution_response(analysis, customer_data, issue_category, solvability)
        
        # Prepare result
        result = {
            "analysis": analysis,
            "customer_data_found": customer_data is not None,
            "issue_category": issue_category,
            "solvability": solvability,
            "solution_response": solution_response,
            "department_head": self.get_department_head(company, issue_category) if not solvability["solvable"] else None,
            "timestamp": datetime.now().isoformat()
        }
        
        return result


def main():
    """Main execution function"""
    
    # Check if we have any prototype output files
    output_dir = "output"
    if not os.path.exists(output_dir):
        print("❌ No output directory found. Please run the workflow coordinator first.")
        return
    
    # Find the most recent prototype output file
    output_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    
    if not output_files:
        print("❌ No prototype output files found. Please run the workflow coordinator first.")
        return
    
    # Use the Facebook content issue file for demonstration
    test_file = "facebook_content_issue_20250921_054700.json"
    if test_file in output_files:
        latest_file = test_file
    else:
        # Use the most recent file
        latest_file = max(output_files, key=lambda f: os.path.getctime(os.path.join(output_dir, f)))
    
    output_file = os.path.join(output_dir, latest_file)
    
    print(f"📁 Processing: {latest_file}")
    print("="*70)
    
    try:
        # Initialize solution agent
        agent = IntelligentSolutionAgent()
        
        # Process the customer issue
        result = agent.process_customer_issue(output_file)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        # Display the solution
        print("\\n" + "="*70)
        print("🎯 SOLUTION AGENT RESPONSE")
        print("="*70)
        print(result["solution_response"])
        print("="*70)
        
        # Save detailed result
        result_file = os.path.join(output_dir, f"solution_agent_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\\n💾 Detailed analysis saved: {result_file}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()