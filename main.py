#!/usr/bin/env python3
"""
TIC System - Main Entry Point

This is the primary interface for the TIC (Three-Intelligence Confluence) system.
Run this script to start an interactive session with the complete AI-powered
customer service system.

Usage:
    python main.py                 # Interactive mode
    python main.py --demo          # Run demonstration
    python main.py --case TYPE     # Process specific case type
"""

import argparse
import logging
import sys
import json
import os
import glob
from datetime import datetime
from pathlib import Path

from knowledge_base import CompanyKnowledgeBase
from decision_engine import DecisionEngine, CaseFingerprint
from execution_layer import ExecutionLayer

# Import conversational agent functionality
try:
    from conversational_agent import ConversationalCustomerServiceAgent
    CONVERSATIONAL_AVAILABLE = True
except ImportError:
    CONVERSATIONAL_AVAILABLE = False
    print("⚠️ Conversational agent not available. Install audio dependencies for full functionality.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TICSystem:
    """Main TIC System Controller"""
    
    def __init__(self):
        """Initialize the complete TIC system"""
        print("🚀 Initializing TIC System...")
        print("=" * 50)
        
        try:
            # Initialize components
            print("📚 Loading Knowledge Base...")
            self.knowledge_base = CompanyKnowledgeBase()
            doc_count = self.knowledge_base.get_document_count()
            chunk_count = self.knowledge_base.get_chunk_count()
            print(f"   ✅ {doc_count} documents, {chunk_count} chunks loaded")
            
            print("🧠 Initializing Decision Engine...")
            self.decision_engine = DecisionEngine(self.knowledge_base)
            print("   ✅ Google Gemini Flash 1.5 ready")
            
            print("⚡ Setting up Execution Layer...")
            self.execution_layer = ExecutionLayer(self.knowledge_base, self.decision_engine)
            print("   ✅ Conversational AI ready")
            
            print("\n🎉 TIC System Fully Operational!")
            print(f"📊 System loaded with {doc_count} company documents")
            
        except Exception as e:
            logger.error(f"Failed to initialize TIC system: {e}")
            sys.exit(1)
    
    def create_case_from_input(self) -> CaseFingerprint:
        """Interactive case creation"""
        print("\n📋 Case Information")
        print("-" * 30)
        
        # Get case type
        print("Case Types:")
        print("1. Billing_Dispute")
        print("2. Technical_Support") 
        print("3. Refund_Request")
        print("4. General_Inquiry")
        
        while True:
            try:
                choice = input("Select case type (1-4): ").strip()
                case_types = {
                    "1": "Billing_Dispute",
                    "2": "Technical_Support", 
                    "3": "Refund_Request",
                    "4": "General_Inquiry"
                }
                if choice in case_types:
                    case_type = case_types[choice]
                    break
                else:
                    print("Please enter 1, 2, 3, or 4")
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(0)
        
        # Get urgency
        print("\nUrgency Levels:")
        print("1. Low")
        print("2. Medium") 
        print("3. High")
        print("4. Critical")
        
        while True:
            try:
                choice = input("Select urgency (1-4): ").strip()
                urgencies = {"1": "Low", "2": "Medium", "3": "High", "4": "Critical"}
                if choice in urgencies:
                    urgency = urgencies[choice]
                    break
                else:
                    print("Please enter 1, 2, 3, or 4")
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(0)
        
        # Get customer details
        print("\nCustomer Details:")
        anger_levels = {"1": "Low", "2": "Moderate", "3": "High", "4": "Extreme"}
        account_types = {"1": "Standard", "2": "Premium", "3": "Enterprise"}
        
        anger_choice = input("Customer anger level (1=Low, 2=Moderate, 3=High, 4=Extreme): ").strip()
        customer_anger_level = anger_levels.get(anger_choice, "Moderate")
        
        account_choice = input("Account type (1=Standard, 2=Premium, 3=Enterprise): ").strip()
        account_type = account_types.get(account_choice, "Standard")
        
        refund_request = input("Contains refund request? (y/N): ").strip().lower() == 'y'
        
        try:
            previous_interactions = int(input("Previous interactions (0-10): ") or "0")
            case_age_days = int(input("Case age in days (0-30): ") or "0")
        except ValueError:
            previous_interactions = 0
            case_age_days = 0
        
        return CaseFingerprint(
            case_type=case_type,
            urgency=urgency,
            customer_anger_level=customer_anger_level,
            request_contains_refund=refund_request,
            account_type=account_type,
            previous_interactions=previous_interactions,
            case_age_days=case_age_days,
            additional_attributes=[]
        )
    
    def run_interactive_session(self):
        """Run an interactive customer service session"""
        print("\n💬 Interactive Customer Service Session")
        print("=" * 50)
        
        # Create case
        case_fingerprint = self.create_case_from_input()
        
        # Generate procedural plan
        print(f"\n🎯 Generating procedural plan for {case_fingerprint.case_type}...")
        context = self.execution_layer.create_execution_context(case_fingerprint)
        
        plan = context.procedural_plan
        print(f"\n📋 Generated Plan: {plan.plan_type}")
        print(f"🚨 Priority: {plan.priority}")
        print(f"⏱️ Estimated Time: {plan.estimated_resolution_time}")
        print(f"🔢 Total Steps: {len(plan.steps)}")
        
        if plan.escalation_required:
            print("⚠️ Escalation Required: Yes")
        
        # Start conversation
        print(f"\n🤖 AI Agent Ready - Type 'quit' to exit")
        print("-" * 40)
        
        conversation_count = 0
        max_conversations = 10
        
        while conversation_count < max_conversations:
            try:
                user_input = input(f"\n👤 Customer: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("🤖 Agent: Thank you for contacting us. Have a great day!")
                    break
                
                if not user_input:
                    continue
                
                # Process with execution layer
                response, should_continue = self.execution_layer.handle_conversation(context, user_input)
                print(f"🤖 Agent: {response}")
                
                conversation_count += 1
                
                if not should_continue:
                    print("\n🚨 Case has been escalated to a human agent.")
                    break
                    
            except KeyboardInterrupt:
                print("\n\n🤖 Agent: Session ended. Thank you!")
                break
            except Exception as e:
                logger.error(f"Error in conversation: {e}")
                print("🤖 Agent: I'm experiencing technical difficulties. Let me connect you with a human agent.")
                break
        
        # Show session summary
        print(f"\n📊 Session Summary")
        print("-" * 25)
        summary = self.execution_layer.get_execution_summary(context)
        print(f"Case Type: {summary['case_type']}")
        print(f"Conversation Turns: {summary['conversation_turns']}")
        print(f"Steps Completed: {summary['completed_steps']}/{summary['total_steps']}")
        print(f"Duration: {summary['execution_duration']:.1f} seconds")
        
        if summary['escalation_triggered']:
            print("Status: Escalated to human agent")
        else:
            print("Status: Completed successfully")
    
    def run_demo(self):
        """Run a demonstration of the system"""
        print("\n🎭 TIC System Demonstration")
        print("=" * 40)
        
        # Demo cases
        demo_cases = [
            {
                "name": "Premium Billing Dispute",
                "case": CaseFingerprint(
                    case_type="Billing_Dispute",
                    urgency="High",
                    customer_anger_level="Moderate", 
                    request_contains_refund=True,
                    account_type="Premium",
                    previous_interactions=1,
                    case_age_days=2
                ),
                "queries": [
                    "I was charged $29.99 but I cancelled my subscription",
                    "Can you process a refund right now?",
                    "This is unacceptable, I want to speak to a manager"
                ]
            },
            {
                "name": "Enterprise Technical Emergency", 
                "case": CaseFingerprint(
                    case_type="Technical_Support",
                    urgency="Critical",
                    customer_anger_level="High",
                    request_contains_refund=False,
                    account_type="Enterprise",
                    previous_interactions=0,
                    case_age_days=0
                ),
                "queries": [
                    "Our entire system is down and we're losing money",
                    "How quickly can you fix this?"
                ]
            }
        ]
        
        for i, demo in enumerate(demo_cases, 1):
            print(f"\n{i}. {demo['name']}")
            print("-" * len(f"{i}. {demo['name']}"))
            
            # Generate plan
            context = self.execution_layer.create_execution_context(demo['case'])
            plan = context.procedural_plan
            
            print(f"📋 Plan: {plan.plan_type}")
            print(f"🚨 Priority: {plan.priority}")
            print(f"📝 Steps: {len(plan.steps)}")
            
            # Simulate conversation
            print("\n💬 Sample Conversation:")
            for query in demo['queries']:
                print(f"👤 Customer: {query}")
                
                try:
                    response, should_continue = self.execution_layer.handle_conversation(context, query)
                    print(f"🤖 Agent: {response[:200]}...")
                    
                    if not should_continue:
                        print("🚨 [Escalated to human agent]")
                        break
                        
                except Exception as e:
                    print(f"🤖 Agent: [Error: {e}]")
                    break
    
    def process_specific_case(self, case_type: str):
        """Process a specific case type"""
        print(f"\n🎯 Processing {case_type} Case")
        print("=" * 40)
        
        # Create default case based on type
        case_configs = {
            "billing": CaseFingerprint(
                case_type="Billing_Dispute",
                urgency="High",
                customer_anger_level="Moderate",
                request_contains_refund=True,
                account_type="Premium"
            ),
            "technical": CaseFingerprint(
                case_type="Technical_Support", 
                urgency="Critical",
                customer_anger_level="High",
                request_contains_refund=False,
                account_type="Enterprise"
            ),
            "refund": CaseFingerprint(
                case_type="Refund_Request",
                urgency="Medium", 
                customer_anger_level="Low",
                request_contains_refund=True,
                account_type="Standard"
            )
        }
        
        case_fingerprint = case_configs.get(case_type.lower())
        if not case_fingerprint:
            print(f"❌ Unknown case type: {case_type}")
            print("Available types: billing, technical, refund")
            return
        
        # Generate and show plan
        context = self.execution_layer.create_execution_context(case_fingerprint)
        plan = context.procedural_plan
        
        print(f"📋 Generated Plan: {plan.plan_type}")
        print(f"🚨 Priority: {plan.priority}")
        print(f"⏱️ Estimated Time: {plan.estimated_resolution_time}")
        print(f"\n📝 Procedural Steps ({len(plan.steps)} steps):")
        
        for i, step in enumerate(plan.steps, 1):
            print(f"\n{i}. {step.action}")
            print(f"   Description: {step.description}")
            print(f"   Team: {step.responsible_team}")
            print(f"   Time: {step.estimated_time}")
            if step.conditions:
                print(f"   Conditions: {', '.join(step.conditions)}")
    
    def process_json_input(self, json_data):
        """Process structured JSON customer data and provide complete resolution"""
        print("🎯 Processing Customer Data")
        print("=" * 40)
        
        try:
            # Extract customer information
            customer_info = json_data.get("customer_info", {})
            complaint_details = json_data.get("complaint_details", {})
            company_info = json_data.get("company_info", {})
            
            print(f"👤 Customer: {customer_info.get('name', 'Unknown')}")
            print(f"📧 Email: {customer_info.get('email', 'Not provided')}")
            print(f"📞 Phone: {customer_info.get('phone', 'Not provided')}")
            print(f"🏢 Company: {company_info.get('company_name', 'Unknown')}")
            print(f"📋 Issue: {complaint_details.get('description', 'No description')}")
            print(f"🏷️ Category: {complaint_details.get('category', 'General')}")
            print(f"🚨 Urgency: {complaint_details.get('urgency_level', 'medium')}")
            
            # Map category to case type
            category_mapping = {
                "Delivery Issue": "Technical_Support",
                "Billing Issue": "Billing_Dispute", 
                "Product Issue": "Product_Complaint",
                "Refund Request": "Refund_Request",
                "Account Issue": "Account_Access"
            }
            
            case_type = category_mapping.get(
                complaint_details.get('category', ''), 
                'General_Inquiry'
            )
            
            # Map urgency level
            urgency_mapping = {
                "low": 0.3,
                "medium": 0.6, 
                "high": 0.9,
                "critical": 1.0
            }
            
            urgency = urgency_mapping.get(
                complaint_details.get('urgency_level', 'medium').lower(),
                0.6
            )
            
            # Create case fingerprint
            case_fingerprint = CaseFingerprint(
                case_type=case_type,
                urgency=urgency,
                customer_anger_level="High" if urgency >= 0.8 else "Moderate",
                request_contains_refund=("refund" in complaint_details.get('description', '').lower()),
                account_type="Standard",
                previous_interactions=0,
                case_age_days=0,
                additional_attributes=[
                    complaint_details.get('category', ''),
                    complaint_details.get('order_id', '') if complaint_details.get('order_id') else None
                ]
            )
            
            # Generate procedural plan
            print(f"\n🔄 Generating Resolution Plan...")
            context = self.execution_layer.create_execution_context(case_fingerprint)
            plan = context.procedural_plan
            
            print(f"\n📋 Generated Plan: {plan.plan_type}")
            print(f"🚨 Priority: {plan.priority}")
            print(f"⏱️ Estimated Time: {plan.estimated_resolution_time}")
            print(f"🔄 Escalation Required: {plan.escalation_required}")
            
            print(f"\n📝 Resolution Steps ({len(plan.steps)} steps):")
            for i, step in enumerate(plan.steps, 1):
                print(f"\n{i}. {step.action}")
                print(f"   → {step.description}")
                print(f"   → Team: {step.responsible_team}")
                print(f"   → Time: {step.estimated_time}")
                if step.conditions:
                    print(f"   → Conditions: {', '.join(step.conditions)}")
                if step.escalation_triggers:
                    print(f"   → Escalation Triggers: {', '.join(step.escalation_triggers)}")
            
            # Generate comprehensive resolution
            print(f"\n💬 Automated Resolution:")
            print("-" * 30)
            
            # Create a comprehensive response based on the case
            customer_name = customer_info.get('name', 'Customer')
            issue_description = complaint_details.get('description', 'your concern')
            order_id = complaint_details.get('order_id', '')
            category = complaint_details.get('category', '')
            
            resolution_message = self._generate_resolution_message(
                customer_name, issue_description, order_id, category, plan
            )
            
            print(f"🤖 Complete Resolution:\n{resolution_message}")
            
            # Add special notes if any
            if plan.special_notes:
                print(f"\n📌 Special Notes:")
                for note in plan.special_notes:
                    print(f"   → {note}")
            
            return {
                "status": "resolved",
                "case_id": plan.case_id,
                "priority": plan.priority,
                "estimated_time": plan.estimated_resolution_time,
                "escalation_required": plan.escalation_required,
                "resolution_message": resolution_message,
                "procedural_plan": plan.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error processing JSON input: {e}")
            print(f"❌ Error processing customer data: {e}")
            return {"status": "error", "message": str(e)}
    
    def _generate_resolution_message(self, customer_name, issue_description, order_id, category, plan):
        """Generate a comprehensive resolution message"""
        
        if category == "Delivery Issue":
            return f"""Hello {customer_name},

Thank you for contacting us regarding your delivery concern. I understand that you did not receive your parcel{f' (Order ID: {order_id})' if order_id else ''}, despite our tracking showing it was delivered.

Here's how we'll resolve this issue:

1. **Immediate Investigation**: I've initiated a delivery investigation with our shipping partner to trace the exact delivery location and obtain proof of delivery details.

2. **Tracking Review**: Our team is reviewing the complete delivery route and any delivery photos or signatures collected.

3. **Resolution Options**: Based on the investigation results (within 24-48 hours), we will either:
   - Locate your package if it was misdelivered to a nearby address
   - Process a full replacement shipment at no cost
   - Provide a complete refund if preferred

4. **Investigation Reference**: Your case has been assigned ID {plan.case_id} for tracking purposes.

5. **Next Steps**: You will receive an email update within 24 hours with investigation results and your preferred resolution option.

Priority Level: {plan.priority}
Estimated Resolution: {plan.estimated_resolution_time}

We sincerely apologize for this inconvenience and appreciate your patience as we work to resolve this matter promptly.

Best regards,
Customer Service Team"""

        elif category == "Billing Issue":
            return f"""Hello {customer_name},

Thank you for contacting us about your billing concern. I've reviewed your account and understand your situation regarding {issue_description}.

Resolution Plan:
1. **Account Review**: Complete review of your billing history and charges
2. **Dispute Investigation**: Thorough investigation of the disputed amount
3. **Resolution**: Appropriate refund or credit will be processed if warranted

Timeline: {plan.estimated_resolution_time}
Priority: {plan.priority}
Case ID: {plan.case_id}

You'll receive confirmation within 2 business days with the resolution details.

Best regards,
Billing Department"""

        elif category == "Product Issue":
            return f"""Hello {customer_name},

I've reviewed your product concern: {issue_description}{f' (Order ID: {order_id})' if order_id else ''}.

Resolution Plan:
1. **Product Assessment**: Detailed review of the product issue
2. **Quality Check**: Investigation with our quality assurance team
3. **Resolution**: Replacement, repair, or refund based on assessment

Priority: {plan.priority}
Estimated Time: {plan.estimated_resolution_time}
Case ID: {plan.case_id}

We'll contact you within 24 hours with next steps.

Best regards,
Product Support Team"""

        elif "refund" in issue_description.lower() or category == "Refund Request":
            return f"""Hello {customer_name},

I've processed your refund request for {issue_description}{f' (Order ID: {order_id})' if order_id else ''}.

Your refund has been approved and will be processed within 3-5 business days to your original payment method.

Refund Details:
- Priority: {plan.priority}
- Processing Time: {plan.estimated_resolution_time}
- Case ID: {plan.case_id}
- Confirmation: You'll receive an email confirmation shortly

Thank you for your business.

Best regards,
Customer Service Team"""

        else:
            return f"""Hello {customer_name},

Thank you for contacting us. I've reviewed your concern: {issue_description}

Our team has created a resolution plan with priority level {plan.priority} and estimated completion time of {plan.estimated_resolution_time}.

Case ID: {plan.case_id}
Category: {category}

We're committed to resolving this matter promptly and will keep you updated throughout the process.

Best regards,
Customer Service Team"""
    
    def process_input_directory(self, input_dir="input", output_dir="output"):
        """Process all JSON files from input directory and save results to output directory"""
        print("🎯 Processing Input Directory")
        print("=" * 40)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Created output directory: {output_dir}")
        
        # Find all JSON files in input directory
        json_files = glob.glob(os.path.join(input_dir, "*.json"))
        
        if not json_files:
            print(f"❌ No JSON files found in '{input_dir}' directory")
            print(f"💡 Please place your customer data JSON files in the '{input_dir}/' folder")
            return
        
        print(f"📂 Found {len(json_files)} JSON file(s) to process:")
        for file_path in json_files:
            print(f"   → {os.path.basename(file_path)}")
        
        processed_count = 0
        error_count = 0
        
        # Process each JSON file
        for json_file in json_files:
            filename = os.path.basename(json_file)
            print(f"\n🔄 Processing: {filename}")
            print("-" * 30)
            
            try:
                # Read JSON file
                with open(json_file, 'r') as f:
                    json_data = json.load(f)
                
                # Process the case
                result = self.process_json_input(json_data)
                
                # Create output filename
                base_name = os.path.splitext(filename)[0]
                output_file = os.path.join(output_dir, f"{base_name}_result.json")
                
                # Save result to output file
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                print(f"✅ Processed successfully → {os.path.basename(output_file)}")
                processed_count += 1
                
                # Move processed file to a processed subfolder
                processed_dir = os.path.join(input_dir, "processed")
                if not os.path.exists(processed_dir):
                    os.makedirs(processed_dir)
                
                processed_file = os.path.join(processed_dir, filename)
                os.rename(json_file, processed_file)
                print(f"📦 Moved to processed: {os.path.relpath(processed_file)}")
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
                error_count += 1
                
                # Save error info
                error_file = os.path.join(output_dir, f"{base_name}_error.json")
                error_info = {
                    "status": "error",
                    "filename": filename,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                with open(error_file, 'w') as f:
                    json.dump(error_info, f, indent=2)
        
        # Summary
        print(f"\n📊 Processing Summary:")
        print(f"   ✅ Successfully processed: {processed_count} files")
        print(f"   ❌ Errors encountered: {error_count} files")
        print(f"   📁 Results saved to: {output_dir}/")
        print(f"   📦 Processed files moved to: {input_dir}/processed/")
        
        return {
            "processed_count": processed_count,
            "error_count": error_count,
            "total_files": len(json_files)
        }
    
    def process_audio_to_json(self, audio_mode="live"):
        """Process audio input using conversational agent and convert to TIC JSON format"""
        if not CONVERSATIONAL_AVAILABLE:
            print("❌ Conversational agent not available. Please install audio dependencies:")
            print("   pip install assemblyai langgraph pydantic sounddevice pyaudio pyttsx3")
            return None
        
        print("🎤 Starting Audio Processing Mode")
        print("=" * 40)
        
        try:
            # Initialize conversational agent
            agent = ConversationalCustomerServiceAgent()
            
            if audio_mode == "live":
                print("🎙️ Starting live audio recording...")
                print("   Speak your complaint clearly")
                print("   Press Ctrl+C to stop recording")
                
                # Process live audio
                result = agent.run_conversation()
            else:
                # For file-based processing (if audio file exists)
                audio_files = glob.glob("*.wav") + glob.glob("*.mp3")
                if not audio_files:
                    print("❌ No audio files found. Starting live recording...")
                    result = agent.run_conversation()
                else:
                    print(f"🎵 Found audio file: {audio_files[0]}")
                    result = agent.process_audio_file(audio_files[0])
            
            if not result:
                print("❌ No valid audio processing result")
                return None
            
            # Convert conversational agent output to TIC JSON format
            tic_json = self._convert_agent_output_to_tic_format(result)
            
            # Save the converted JSON to input directory for processing
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"audio_input_{timestamp}.json"
            json_path = os.path.join("input", json_filename)
            
            # Ensure input directory exists
            os.makedirs("input", exist_ok=True)
            
            with open(json_path, 'w') as f:
                json.dump(tic_json, f, indent=2)
            
            print(f"✅ Audio converted to JSON: {json_filename}")
            print(f"📁 Saved to: {json_path}")
            
            # Now process this JSON with the TIC system
            print(f"\n🔄 Processing with TIC System...")
            result = self.process_json_input(tic_json)
            
            return result
            
        except KeyboardInterrupt:
            print("\n🛑 Audio recording stopped by user")
            return None
        except Exception as e:
            print(f"❌ Error in audio processing: {e}")
            return None
    
    def _convert_agent_output_to_tic_format(self, agent_output):
        """Convert conversational agent output to TIC JSON format"""
        try:
            # Extract information from agent output
            customer_name = agent_output.get("customer_info", {}).get("name", "Unknown")
            customer_phone = agent_output.get("customer_info", {}).get("phone", "")
            customer_email = agent_output.get("customer_info", {}).get("email", "")
            
            complaint_desc = agent_output.get("complaint_details", {}).get("description", "")
            order_id = agent_output.get("complaint_details", {}).get("order_id", "")
            product_name = agent_output.get("complaint_details", {}).get("product_name", "")
            category = agent_output.get("complaint_details", {}).get("category", "General_Inquiry")
            urgency = agent_output.get("complaint_details", {}).get("urgency_level", "medium")
            
            company_name = agent_output.get("company_info", {}).get("company_name", "Unknown")
            
            # Map categories from conversational agent to TIC categories
            category_mapping = {
                "delivery": "Delivery Issue",
                "billing": "Billing Issue", 
                "product": "Product Issue",
                "refund": "Refund Request",
                "account": "Account Issue",
                "unknown": "General Inquiry"
            }
            
            mapped_category = category_mapping.get(category.lower(), "General Inquiry")
            
            # Create TIC-compatible JSON
            tic_json = {
                "customer_info": {
                    "name": customer_name,
                    "phone": customer_phone,
                    "email": customer_email
                },
                "complaint_details": {
                    "description": complaint_desc,
                    "category": mapped_category,
                    "urgency_level": urgency,
                    "order_id": order_id,
                    "product_name": product_name
                },
                "company_info": {
                    "company_name": company_name
                },
                "status": "conversation_completed",
                "source": "audio_input",
                "processing_metadata": {
                    "transcription_confidence": agent_output.get("metadata", {}).get("transcription_confidence", 0.0),
                    "audio_file": agent_output.get("metadata", {}).get("audio_file", ""),
                    "processing_timestamp": datetime.now().isoformat()
                }
            }
            
            return tic_json
            
        except Exception as e:
            print(f"❌ Error converting agent output: {e}")
            # Return a minimal valid JSON structure
            return {
                "customer_info": {
                    "name": "Unknown",
                    "phone": "",
                    "email": ""
                },
                "complaint_details": {
                    "description": "Audio processing error",
                    "category": "General Inquiry",
                    "urgency_level": "medium",
                    "order_id": "",
                    "product_name": ""
                },
                "company_info": {
                    "company_name": "Unknown"
                },
                "status": "processing_error"
            }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="TIC System - AI-Powered Customer Service")
    parser.add_argument("--demo", action="store_true", help="Run demonstration mode")
    parser.add_argument("--case", type=str, help="Process specific case type (billing, technical, refund)")
    parser.add_argument("--json", type=str, help="Process JSON customer data (file path or JSON string)")
    parser.add_argument("--json-file", type=str, help="Process JSON customer data from file")
    parser.add_argument("--interactive", action="store_true", help="Run interactive mode")
    parser.add_argument("--audio", action="store_true", help="Process audio input (live recording)")
    parser.add_argument("--audio-file", action="store_true", help="Process audio files from current directory")
    parser.add_argument("--input-dir", type=str, default="input", help="Input directory for JSON files (default: input)")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory for results (default: output)")
    parser.add_argument("--version", action="version", version="TIC System v2.0")
    
    args = parser.parse_args()
    
    try:
        # Initialize system
        tic_system = TICSystem()
        
        if args.audio or args.audio_file:
            # Process audio input
            audio_mode = "file" if args.audio_file else "live"
            result = tic_system.process_audio_to_json(audio_mode)
            if result:
                print(f"\n📊 Audio Processing Result:")
                print(f"Status: {result.get('status', 'unknown')}")
                if result.get('case_id'):
                    print(f"Case ID: {result['case_id']}")
                    
        elif args.json or args.json_file:
            # Process single JSON input
            if args.json_file:
                # Read from file
                with open(args.json_file, 'r') as f:
                    json_data = json.load(f)
            else:
                # Parse JSON string or read from file
                if args.json.startswith('{'):
                    # Direct JSON string
                    json_data = json.loads(args.json)
                else:
                    # File path
                    with open(args.json, 'r') as f:
                        json_data = json.load(f)
            
            result = tic_system.process_json_input(json_data)
            
            # Output result as JSON if needed
            print(f"\n📊 Result Summary:")
            print(f"Status: {result.get('status', 'unknown')}")
            if result.get('case_id'):
                print(f"Case ID: {result['case_id']}")
                
        elif args.demo:
            tic_system.run_demo()
        elif args.case:
            tic_system.process_specific_case(args.case)
        elif args.interactive:
            tic_system.run_interactive_session()
        else:
            # Default mode: Process input directory
            tic_system.process_input_directory(args.input_dir, args.output_dir)
            
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
    except Exception as e:
        logger.error(f"System error: {e}")
        print(f"❌ System error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
