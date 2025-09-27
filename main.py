#!/usr/bin/env python3
"""
TIC Minimal - Clean Customer Service System
==========================================

A streamlined implementation of AI-powered customer service automation.
Core workflow: Audio Input → Conversation → Company Agent Response

Usage:
    python main.py
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

from dotenv import load_dotenv

from conversation import ConversationalAgent
from amazon_agent import AmazonAgent

# Load environment variables from current directory
load_dotenv('.env')

class CustomerServiceSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = []
        
        # Initialize components
        try:
            from conversation import ConversationalAgent
            from amazon_agent import AmazonAgent
            from apple_agent import AppleAgent
            
            self.conversation_agent = ConversationalAgent()
            self.amazon_agent = AmazonAgent() 
            self.apple_agent = AppleAgent()
            
            print("✅ All system components initialized successfully")
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            raise
    
    def log_step(self, step: str, status: str, message: str):
        """Log workflow step"""
        self.results.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,
            "message": message
        })
        
        status_emoji = "✅" if status == "success" else "⚠️" if status == "warning" else "❌"
        print(f"{status_emoji} {step}: {message}")
    
    def execute_workflow(self) -> Dict[str, Any]:
        """Execute the complete customer service workflow"""
        
        print("\n" + "="*60)
        print("🚀 TIC MINIMAL - CUSTOMER SERVICE SYSTEM")
        print("="*60)
        
        workflow_result = {
            "session_id": self.session_id,
            "success": False,
            "conversation_data": None,
            "company_detected": None,
            "agent_response": None,
            "final_solution": None,
            "error": None
        }
        
        try:
            # Step 1: Conduct conversation with customer
            self.log_step("conversation", "progress", "Starting customer conversation...")
            
            conversation_result = self.conversation_agent.start_conversation()
            if not conversation_result or not conversation_result.get("success"):
                raise Exception("Conversation failed or was cancelled")
            
            conversation_data = conversation_result["data"]
            workflow_result["conversation_data"] = conversation_data
            
            # Save comprehensive conversation JSON
            if "conversation_json" in conversation_result:
                saved_path = self.conversation_agent.save_conversation_json(
                    conversation_result["conversation_json"]
                )
                if saved_path:
                    self.log_step("conversation", "success", 
                                 f"Conversation JSON saved to {saved_path}")
            
            self.log_step("conversation", "success", 
                         f"Conversation completed - Customer: {conversation_data['customer_name']}")
            
            # Step 2: Route to appropriate company agent
            detected_company = conversation_data.get("company") or ""
            detected_company = detected_company.lower() if detected_company else "unknown"
            workflow_result["company_detected"] = detected_company
            
            self.log_step("routing", "progress", f"Routing to {detected_company} agent...")
            
            if "amazon" in detected_company:
                agent_result = self.amazon_agent.process_customer_issue(conversation_data)
            elif "apple" in detected_company:
                agent_result = self.apple_agent.process_customer_issue(conversation_data)
            elif "facebook" in detected_company or "meta" in detected_company:
                # TODO: Add Facebook/Meta agent when needed
                self.log_step("routing", "warning", f"Facebook agent not implemented yet, using Amazon agent")
                agent_result = self.amazon_agent.process_customer_issue(conversation_data)
            else:
                # Default to Amazon agent for unknown companies
                self.log_step("routing", "warning", f"Company '{detected_company}' not supported, using Amazon agent")
                agent_result = self.amazon_agent.process_customer_issue(conversation_data)
            
            if not agent_result.get("success"):
                raise Exception(f"Agent processing failed: {agent_result.get('error')}")
            
            self.log_step("routing", "success", "Company agent processing completed")
            
            # Step 3: Get final solution directly from company agent
            final_solution = agent_result["data"]["response"]["response_text"]
            workflow_result["agent_response"] = agent_result["data"]
            workflow_result["final_solution"] = final_solution
            
            self.log_step("solution", "success", "Solution received from company agent")
            
            # Step 4: Deliver solution via TTS
            if final_solution:
                self.log_step("delivery", "progress", "Delivering solution via audio...")
                self.conversation_agent.speak_solution(final_solution)
                self.log_step("delivery", "success", "Solution delivered successfully")
            
            workflow_result["success"] = True
            
        except Exception as e:
            error_msg = str(e)
            workflow_result["error"] = error_msg
            self.log_step("error", "error", f"Workflow failed: {error_msg}")
        
        # Save results
        self.save_results(workflow_result)
        return workflow_result
    
    def save_results(self, workflow_result: Dict[str, Any]):
        """Save workflow results to file"""
        os.makedirs("results", exist_ok=True)
        
        # Save detailed results
        result_file = f"results/workflow_{self.session_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(workflow_result, f, indent=2, ensure_ascii=False)
        
        # Save workflow log
        log_file = f"results/log_{self.session_id}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Results saved: {result_file}")
        print(f"📁 Log saved: {log_file}")
    
    def print_summary(self, workflow_result: Dict[str, Any]):
        """Print workflow summary"""
        print("\n" + "="*60)
        print("📋 WORKFLOW SUMMARY")
        print("="*60)
        
        if workflow_result["success"]:
            print("🎉 Status: SUCCESS")
            
            if workflow_result["conversation_data"]:
                data = workflow_result["conversation_data"]
                print(f"👤 Customer: {data.get('customer_name', 'N/A')}")
                print(f"🏢 Company: {data.get('company', 'N/A')}")
                print(f"📋 Issue: {data.get('issue_description', 'N/A')}")
            
            if workflow_result["final_solution"]:
                print(f"💡 Response: {workflow_result['final_solution'][:100]}...")
        else:
            print("❌ Status: FAILED")
            if workflow_result["error"]:
                print(f"💔 Error: {workflow_result['error']}")
        
        print("="*60)


def main():
    """Main entry point"""
    
    # Check required environment variables
    required_keys = ["GROQ_API_KEY", "MURF_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"❌ Missing environment variables: {', '.join(missing_keys)}")
        print("Please check your .env file")
        return
    
    try:
        # Initialize and run system
        system = CustomerServiceSystem()
        result = system.execute_workflow()
        system.print_summary(result)
        
    except KeyboardInterrupt:
        print("\n\n👋 System stopped by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")


if __name__ == "__main__":
    main()
