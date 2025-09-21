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
import re
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
        
        # Define comprehensive solution capabilities based on RAG knowledge
        self.ai_capabilities = {
            "universal_tools": [
                "real_time_order_tracking", "package_location_services", "delivery_partner_communication",
                "billing_history_access", "payment_processing", "refund_authorization_up_to_500",
                "account_management", "security_updates", "inventory_lookup", "replacement_processing",
                "shipping_expediting", "address_updates", "promotional_credits", "compensation_authorization",
                "customer_history_analysis", "dispute_resolution", "priority_escalation"
            ],
            "amazon_specific": [
                "prime_benefits_management", "aws_account_integration", "kindle_book_management",
                "alexa_device_support", "marketplace_seller_coordination", "fulfillment_center_communication"
            ],
            "facebook_specific": [
                "content_policy_review", "community_standards_guidance", "business_page_management", 
                "advertising_account_support", "privacy_settings_assistance", "data_download_processing"
            ],
            "flipkart_specific": [
                "flipkart_plus_benefits", "seller_marketplace_support", "regional_delivery_coordination",
                "payment_gateway_integration", "festival_sale_support", "customer_loyalty_programs"
            ]
        }
        
        # Updated solution protocols emphasizing AI tool usage
        self.solution_protocols = {
            "amazon": {
                "shipping_delays": {
                    "ai_actions": ["track_package_realtime", "contact_delivery_partner", "expedite_shipping", "provide_replacement"],
                    "compensation": ["shipping_refund", "prime_extension", "promotional_credit", "expedited_shipping_upgrade"],
                    "authorization_limit": 500
                },
                "refunds_returns": {
                    "ai_actions": ["process_immediate_refund", "generate_return_label", "schedule_pickup", "apply_store_credit"],
                    "compensation": ["full_refund", "bonus_credit", "return_shipping_waiver"],
                    "authorization_limit": 500
                },
                "account_issues": {
                    "ai_actions": ["reset_password_instantly", "update_security_settings", "verify_identity", "restore_account_access"],
                    "compensation": ["account_security_enhancement", "priority_support_status"],
                    "authorization_limit": 100
                }
            },
            "facebook": {
                "content_moderation": {
                    "ai_actions": ["review_content_policy", "restore_content", "provide_policy_guidance", "appeal_processing"],
                    "compensation": ["content_restoration", "policy_education_materials"],
                    "authorization_limit": 0  # No monetary compensation typically
                },
                "account_suspension": {
                    "ai_actions": ["review_account_status", "process_appeal", "restore_account", "provide_compliance_guidance"],
                    "compensation": ["account_restoration", "priority_review_status"],
                    "authorization_limit": 0
                }
            },
            "flipkart": {
                "shipping_delays": {
                    "ai_actions": ["track_shipment", "coordinate_local_delivery", "expedite_processing", "arrange_replacement"],
                    "compensation": ["shipping_refund", "flipkart_plus_benefits", "cashback_credit"],
                    "authorization_limit": 500
                },
                "refunds_returns": {
                    "ai_actions": ["process_refund", "arrange_pickup", "quality_assurance_review", "replacement_processing"],
                    "compensation": ["full_refund", "return_shipping_waiver", "loyalty_points"],
                    "authorization_limit": 500
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
        """Check if the issue can be solved - now much more optimistic with comprehensive tool access"""
        
        company = analysis["company"]
        customer_verified = analysis["customer_verified"]
        fraud_detected = analysis["fraud_detected"]
        
        # Start optimistic - assume we can solve most issues with our comprehensive tools
        results = {"solvable": True, "failed_conditions": [], "met_conditions": [], "reasoning": ""}
        
        # Only escalate for very specific scenarios
        escalation_triggers = []
        
        # Critical escalation conditions (very rare)
        if fraud_detected:
            escalation_triggers.append("fraud_detected")
            results["reasoning"] = "Fraud detection requires specialized security review"
        
        # Legal/compliance issues that require human intervention
        legal_keywords = ["lawsuit", "legal action", "attorney", "lawyer", "court", "sue", "litigation"]
        complaint = analysis["complaint_info"].get("description", "").lower()
        
        if any(keyword in complaint for keyword in legal_keywords):
            escalation_triggers.append("legal_matters")
            results["reasoning"] = "Legal matters require human legal department review"
        
        # High-value disputes (over our authorization limit)
        high_value_keywords = ["$1000", "$2000", "$5000", "expensive", "thousands"]
        if any(keyword in complaint for keyword in high_value_keywords):
            # Check if we can handle it within our $500 authorization
            try:
                # Extract potential dollar amounts
                dollar_amounts = re.findall(r'\$(\d+)', complaint)
                if dollar_amounts and max(int(amount) for amount in dollar_amounts) > 500:
                    escalation_triggers.append("high_value_dispute")
                    results["reasoning"] = "Dispute exceeds AI authorization limit of $500"
            except:
                pass
        
        # Safety/health issues that require immediate human attention
        safety_keywords = ["injury", "hurt", "hospital", "allergic reaction", "medical", "dangerous", "unsafe"]
        if any(keyword in complaint for keyword in safety_keywords):
            escalation_triggers.append("safety_concern")
            results["reasoning"] = "Safety and health concerns require immediate human attention"
        
        # Update solvability based on escalation triggers
        if escalation_triggers:
            results["solvable"] = False
            results["failed_conditions"] = escalation_triggers
        else:
            # We can solve this with our comprehensive tools!
            results["solvable"] = True
            results["met_conditions"] = [
                "ai_tools_available",
                "within_authorization_scope", 
                "standard_customer_service_issue",
                "comprehensive_system_access"
            ]
            results["reasoning"] = "Issue can be resolved using available AI tools and systems"
        
        return results
    
    def generate_solution_response(self, analysis: Dict[str, Any], customer_data: Optional[Dict], 
                                 issue_category: str, solvability: Dict[str, Any]) -> str:
        """Generate a human-like solution response using AI with full tool access"""
        
        company = analysis["company"]
        customer_name = analysis["customer_info"].get("name", "valued customer")
        complaint = analysis["complaint_info"].get("description", "")
        customer_phone = analysis["customer_info"].get("phone", "")
        order_id = analysis["complaint_info"].get("order_id", "")
        
        # Always try to solve the problem first using available tools and capabilities
        solution_prompt = f"""
        You are an advanced AI customer service agent for {company.title()} with comprehensive access to tools and systems. A customer named {customer_name} has contacted us with this issue:
        
        CUSTOMER DETAILS:
        - Name: {customer_name}
        - Phone: {customer_phone}
        - Issue: "{complaint}"
        - Order ID: {order_id if order_id else "Not provided"}
        - Category: {issue_category}
        
        IMPORTANT: You have access to ALL company tools and systems including:
        ✅ Package tracking and location services
        ✅ Billing history and payment processing
        ✅ Order management and modification systems
        ✅ Inventory and replacement processing
        ✅ Refund and credit authorization (up to $500)
        ✅ Account management and security updates
        ✅ Shipping expediting and rerouting
        ✅ Customer database with full history
        ✅ Real-time delivery partner communication
        ✅ Payment dispute resolution tools
        ✅ Promotional credit and compensation systems
        
        YOUR GOAL: Resolve this customer's issue completely using your available tools rather than escalating to humans. You are empowered to:
        - Process refunds up to $500 immediately
        - Expedite shipping at no cost
        - Provide replacement items
        - Apply account credits and promotional codes
        - Update delivery addresses and methods
        - Resolve billing discrepancies
        - Reset account access and security
        - Coordinate with shipping partners for package recovery
        
        RESPONSE REQUIREMENTS:
        1. Start directly with "Dear {customer_name}," - NO additional headers or titles
        2. Do NOT include phrases like "I'm your dedicated AI agent" or similar introductions
        3. Focus immediately on acknowledging the issue and taking action
        4. Be specific about what you're doing right now (e.g., "I'm processing your refund now")
        5. Provide concrete next steps and timelines
        6. Offer appropriate compensation for the inconvenience
        7. Give tracking/reference numbers for follow-up
        8. Only escalate if the issue requires legal intervention or exceeds your authorization limits
        
        Generate a professional response that shows you are actively solving their problem using your advanced capabilities. Be confident and solution-focused. Start immediately with the greeting and problem resolution.
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
        
        # Step 4: Check solvability with comprehensive AI tools
        print("\\n⚖️ Evaluating resolution approach...")
        solvability = self.check_solvability(analysis, customer_data, issue_category)
        
        if solvability["solvable"]:
            print("✅ Issue can be resolved using AI tools and systems")
            print(f"�️ Available capabilities: {', '.join(solvability['met_conditions'])}")
            resolution_type = "AI_RESOLVED"
        else:
            print("🔄 Issue requires human specialist intervention")
            print(f"⚠️ Escalation reasons: {', '.join(solvability['failed_conditions'])}")
            print(f"📝 Reasoning: {solvability.get('reasoning', 'Requires human expertise')}")
            resolution_type = "ESCALATED"
        
        # Step 5: Generate comprehensive solution
        print("\\n💬 Generating intelligent solution...")
        solution_response = self.generate_solution_response(analysis, customer_data, issue_category, solvability)
        
        # Prepare comprehensive result
        result = {
            "analysis": analysis,
            "customer_data_found": customer_data is not None,
            "issue_category": issue_category,
            "resolution_approach": resolution_type,
            "solvability_assessment": solvability,
            "ai_capabilities_used": self.ai_capabilities.get("universal_tools", [])[:5],  # Show first 5 capabilities
            "solution_response": solution_response,
            "department_head": self.get_department_head(company, issue_category) if not solvability["solvable"] else None,
            "authorization_level": "AI_AGENT_FULL_ACCESS",
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