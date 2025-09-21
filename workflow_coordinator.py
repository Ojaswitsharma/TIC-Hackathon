"""
Workflow Coordinator - Complete Customer Service Pipeline
========================================================

This module coordinates the complete customer service workflow:
1. Conversational Agent: Handles conversation and creates JSON
2. LangGraph Workflow: Routes to company-specific prototypes
3. End-to-End Orchestration: Manages the complete pipeline

Professional workflow management for enterprise customer service automation.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Import our modules
try:
    from conversational_agent_simplified import start_conversation_session
    from langgraph_workflow import execute_routing_workflow
    from intelligent_solution_agent import IntelligentSolutionAgent
    print("✅ Workflow modules imported successfully")
except ImportError as e:
    print(f"❌ Error importing workflow modules: {e}")
    start_conversation_session = None
    execute_routing_workflow = None
    IntelligentSolutionAgent = None

# Load environment variables
load_dotenv()

class CustomerServiceWorkflowCoordinator:
    """
    Coordinates the complete customer service workflow from conversation to resolution
    """
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.workflow_log = []
        
        # Ensure output directories exist
        os.makedirs("workflow_results", exist_ok=True)
        os.makedirs("workflow_logs", exist_ok=True)
    
    def log_workflow_step(self, step: str, status: str, message: str, data: Dict = None):
        """Log workflow progress"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "step": step,
            "status": status,
            "message": message,
            "data": data or {}
        }
        
        self.workflow_log.append(log_entry)
        
        # Print status
        status_icon = "✅" if status == "success" else "❌" if status == "error" else "🔄" 
        print(f"{status_icon} {step}: {message}")
    
    def save_workflow_summary(self, final_result: Dict):
        """Save complete workflow summary"""
        workflow_summary = {
            "session_info": {
                "session_id": self.session_id,
                "start_time": self.workflow_log[0]["timestamp"] if self.workflow_log else None,
                "end_time": datetime.now().isoformat(),
                "total_steps": len(self.workflow_log)
            },
            "workflow_log": self.workflow_log,
            "final_result": final_result,
            "status": "completed" if final_result.get("success") else "failed"
        }
        
        # Save summary file
        summary_file = os.path.join("workflow_results", f"workflow_summary_{self.session_id}.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(workflow_summary, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Workflow summary saved: {summary_file}")
        return summary_file
    
    def execute_complete_workflow(self, max_questions: int = 3) -> Dict[str, Any]:
        """
        Execute the complete customer service workflow
        
        Returns:
            Dict containing workflow results and status
        """
        
        print("\n" + "="*80)
        print("🚀 CUSTOMER SERVICE WORKFLOW COORDINATOR")
        print("📋 Complete Pipeline: Conversation → Company Detection → Prototype Routing")
        print("="*80)
        
        final_result = {
            "success": False,
            "session_id": self.session_id,
            "conversation_result": None,
            "routing_result": None,
            "error_message": None
        }
        
        try:
            # Step 1: Conversational Agent
            self.log_workflow_step(
                "conversational_agent", 
                "progress", 
                "Starting intelligent conversation with customer"
            )
            
            if not start_conversation_session:
                raise Exception("Conversational agent not available")
            
            conversation_result = start_conversation_session(max_questions=max_questions)
            
            if not conversation_result:
                raise Exception("Conversation failed or was cancelled")
            
            final_result["conversation_result"] = conversation_result
            conversation_data = conversation_result["conversation_data"]
            
            self.log_workflow_step(
                "conversational_agent", 
                "success", 
                f"Conversation completed - Company: {conversation_data['company_info']['company_name']}",
                {
                    "customer": conversation_data["customer_info"]["name"],
                    "company": conversation_data["company_info"]["company_name"],
                    "confidence": conversation_data["company_info"]["confidence"]
                }
            )
            
            # Step 2: LangGraph Workflow Routing
            self.log_workflow_step(
                "langgraph_routing", 
                "progress", 
                "Starting company-specific routing workflow"
            )
            
            if not execute_routing_workflow:
                raise Exception("LangGraph workflow not available")
            
            routing_result = execute_routing_workflow(
                conversation_json=conversation_data
            )
            
            if not routing_result:
                raise Exception("Routing workflow failed")
            
            final_result["routing_result"] = routing_result
            
            # Check routing success
            workflow_status = routing_result.get("workflow_status", "unknown")
            if workflow_status == "completed":
                detected_company = routing_result.get("detected_company", "unknown")
                prototype_file = routing_result.get("prototype_output_file", "unknown")
                
                self.log_workflow_step(
                    "langgraph_routing", 
                    "success", 
                    f"Successfully routed to {detected_company.title()} prototype",
                    {
                        "routed_company": detected_company,
                        "output_file": prototype_file,
                        "customer_verified": routing_result.get("prototype_result", {}).get("customer_verification", {}).get("verified", False)
                    }
                )
                
                # Step 3: Intelligent Solution Agent
                self.log_workflow_step(
                    "solution_agent", 
                    "progress", 
                    "Analyzing prototype output and generating intelligent solution"
                )
                
                if not IntelligentSolutionAgent:
                    print("⚠️ Warning: Solution agent not available, skipping intelligent resolution")
                    solution_result = {"status": "skipped", "reason": "Solution agent not available"}
                else:
                    try:
                        # Initialize solution agent
                        solution_agent = IntelligentSolutionAgent()
                        
                        # Process the prototype output file
                        solution_result = solution_agent.process_customer_issue(prototype_file)
                        
                        if "error" not in solution_result:
                            self.log_workflow_step(
                                "solution_agent", 
                                "success", 
                                f"Solution generated: {'Resolved' if solution_result['solvability']['solvable'] else 'Escalated'}",
                                {
                                    "issue_category": solution_result["issue_category"],
                                    "solvable": solution_result["solvability"]["solvable"],
                                    "customer_found": solution_result["customer_data_found"]
                                }
                            )
                        else:
                            self.log_workflow_step(
                                "solution_agent", 
                                "error", 
                                f"Solution agent failed: {solution_result['error']}"
                            )
                            
                    except Exception as e:
                        solution_result = {"status": "error", "error": str(e)}
                        self.log_workflow_step(
                            "solution_agent", 
                            "error", 
                            f"Solution agent error: {str(e)}"
                        )
                
                final_result["solution_result"] = solution_result
                final_result["success"] = True
                
            else:
                routing_errors = routing_result.get("errors", ["Unknown routing error"])
                raise Exception(f"Routing failed: {'; '.join(routing_errors)}")
            
            # Step 4: Workflow Completion
            self.log_workflow_step(
                "workflow_completion", 
                "success", 
                "Complete customer service workflow executed successfully"
            )
            
        except Exception as e:
            error_message = str(e)
            final_result["error_message"] = error_message
            
            self.log_workflow_step(
                "workflow_error", 
                "error", 
                f"Workflow failed: {error_message}"
            )
        
        # Save workflow summary
        summary_file = self.save_workflow_summary(final_result)
        final_result["summary_file"] = summary_file
        
        return final_result
    
    def print_workflow_results(self, result: Dict[str, Any]):
        """Print formatted workflow results"""
        
        print("\n" + "="*80)
        if result["success"]:
            print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        else:
            print("❌ WORKFLOW FAILED")
        print("="*80)
        
        # Conversation Results
        conversation_result = result.get("conversation_result")
        if conversation_result:
            conv_data = conversation_result["conversation_data"]
            print("\n📞 CONVERSATION RESULTS:")
            print(f"   • Customer: {conv_data['customer_info']['name'] or 'Unknown'}")
            print(f"   • Phone: {conv_data['customer_info']['phone'] or 'Not provided'}")
            print(f"   • Company: {conv_data['company_info']['company_name']}")
            print(f"   • Confidence: {conv_data['company_info']['confidence']:.2f}")
            print(f"   • Issue: {conv_data['complaint_info']['description'] or 'Not specified'}")
            print(f"   • Conversation File: {conversation_result['conversation_file']}")
        
        # Routing Results
        routing_result = result.get("routing_result")
        if routing_result and result["success"]:
            print("\n🎯 ROUTING RESULTS:")
            print(f"   • Routed to: {routing_result.get('detected_company', 'Unknown').title()} Prototype")
            print(f"   • Customer Verified: {'✅ Yes' if routing_result.get('prototype_result', {}).get('customer_verification', {}).get('verified') else '❌ No (Potential Fraud)'}")
            print(f"   • Prototype Output: {routing_result.get('prototype_output_file', 'Unknown')}")
        
        # Solution Agent Results
        solution_result = result.get("solution_result")
        if solution_result and result["success"]:
            print("\n🤖 INTELLIGENT SOLUTION:")
            if solution_result.get("status") == "skipped":
                print(f"   • Status: ⚠️ Skipped - {solution_result.get('reason', 'Unknown')}")
            elif solution_result.get("status") == "error":
                print(f"   • Status: ❌ Error - {solution_result.get('error', 'Unknown')}")
            elif "solvability" in solution_result:
                solvable = solution_result["solvability"]["solvable"]
                print(f"   • Issue Category: {solution_result['issue_category'].replace('_', ' ').title()}")
                print(f"   • Customer in Database: {'✅ Yes' if solution_result['customer_data_found'] else '❌ No'}")
                print(f"   • Resolution: {'✅ Solved by Agent' if solvable else '🔄 Escalated to Department Head'}")
                
                if not solvable and solution_result.get("department_head"):
                    dept = solution_result["department_head"]
                    print(f"   • Department Head: {dept.get('head', 'Unknown')}")
                    print(f"   • Contact: {dept.get('email', 'Unknown')}")
                
                print("\n💬 AGENT RESPONSE:")
                print("─" * 70)
                solution_response = solution_result.get("solution_response", "No response generated")
                # Truncate very long responses for display
                if len(solution_response) > 500:
                    print(solution_response[:500] + "...")
                    print("(Full response saved in output files)")
                else:
                    print(solution_response)
                print("─" * 70)
        
        # Error Information
        if not result["success"] and result.get("error_message"):
            print(f"\n💔 ERROR: {result['error_message']}")
        
        # Summary File
        if result.get("summary_file"):
            print(f"\n📋 Workflow Summary: {result['summary_file']}")
        
        print("="*80)

# ====================================
# TESTING AND DEMONSTRATION
# ====================================

def test_complete_workflow():
    """Test the complete workflow with sample data"""
    
    print("🧪 Testing complete customer service workflow...")
    
    coordinator = CustomerServiceWorkflowCoordinator()
    result = coordinator.execute_complete_workflow(max_questions=3)
    coordinator.print_workflow_results(result)
    
    return result

def demo_workflow_with_mock_data():
    """Demonstrate workflow with mock conversation data"""
    
    print("\n🎭 DEMO MODE - Using Mock Conversation Data")
    print("="*60)
    
    # Mock conversation data
    mock_conversation = {
        "conversation_metadata": {
            "session_id": "demo_20250921_120000",
            "timestamp": datetime.now().isoformat(),
            "total_questions": 3,
            "conversation_length": 6
        },
        "customer_info": {
            "name": "Alex Johnson",
            "phone": "+1-555-0101",
            "email": "alex.johnson@email.com",
            "username": "@alexjohnson2024"
        },
        "complaint_info": {
            "description": "My post was removed by mistake and I want it restored",
            "category": "content",
            "urgency_level": "high",
            "content_id": "POST_112233445566",
            "post_date": "2025-09-18"
        },
        "company_info": {
            "company_name": "Facebook",
            "confidence": 0.88
        },
        "conversation_history": [
            {"role": "agent", "message": "Hello! How can I help you with your Facebook account today?"},
            {"role": "customer", "message": "Hi, my post was removed and I think it was a mistake"},
            {"role": "agent", "message": "I can help you with that. What's your username?"},
            {"role": "customer", "message": "@alexjohnson2024"},
            {"role": "agent", "message": "Thank you. What's your phone number for verification?"},
            {"role": "customer", "message": "+1-555-0101"}
        ],
        "processing_info": {
            "status": "conversation_completed",
            "ready_for_routing": True,
            "created_timestamp": datetime.now().isoformat()
        }
    }
    
    # Execute routing workflow directly
    if execute_routing_workflow:
        print("🎯 Executing routing workflow with mock data...")
        routing_result = execute_routing_workflow(conversation_json=mock_conversation)
        
        if routing_result:
            prototype_file = routing_result.get('prototype_output_file')
            print("\\n✅ Mock routing workflow completed successfully!")
            print(f"🏢 Company: {routing_result.get('detected_company', 'Unknown').title()}")
            print(f"📁 Output: {prototype_file}")
            
            # Execute solution agent on the prototype output
            if IntelligentSolutionAgent and prototype_file:
                print("\\n🤖 Executing intelligent solution agent...")
                try:
                    solution_agent = IntelligentSolutionAgent()
                    solution_result = solution_agent.process_customer_issue(prototype_file)
                    
                    if "error" not in solution_result:
                        print("\\n" + "="*70)
                        print("🎯 INTELLIGENT SOLUTION AGENT RESPONSE")
                        print("="*70)
                        print(solution_result["solution_response"])
                        print("="*70)
                    else:
                        print(f"\\n❌ Solution agent error: {solution_result['error']}")
                        
                except Exception as e:
                    print(f"\\n❌ Solution agent failed: {str(e)}")
            else:
                print("\\n⚠️ Solution agent not available or no prototype file")
        else:
            print("\\n❌ Mock workflow failed")
    else:
        print("❌ Routing workflow not available")

# ====================================
# MAIN EXECUTION
# ====================================

def main():
    """Main entry point for workflow coordinator"""
    
    print("🏢 CUSTOMER SERVICE WORKFLOW COORDINATOR")
    print("="*50)
    
    # Check API keys
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY not found")
        return
    
    print("\nSelect execution mode:")
    print("1. Complete Workflow (Conversation + Routing)")
    print("2. Demo with Mock Data")
    print("3. Test Routing Only")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            coordinator = CustomerServiceWorkflowCoordinator()
            result = coordinator.execute_complete_workflow()
            coordinator.print_workflow_results(result)
            
        elif choice == "2":
            demo_workflow_with_mock_data()
            
        elif choice == "3":
            from langgraph_workflow import test_workflow_with_sample_data
            test_workflow_with_sample_data()
            
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\n👋 Workflow coordinator stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()