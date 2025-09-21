"""
LangGraph Workflow for Customer Service Routing
==============================================

This module handles the conditional routing workflow that:
1. Takes JSON output from conversational_agent.py
2. Analyzes company name from the JSON
3. Routes to appropriate company prototype (Amazon or Facebook)
4. Manages the complete workflow state and transitions

Professional separation of concerns for enterprise-grade customer service automation.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, TypedDict
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# Import prototype agents for routing
try:
    from amazon_prototype_agent import AmazonCustomerServiceAgent
    from facebook_prototype_agent import FacebookCustomerServiceAgent
    from flipkart_prototype_agent import FlipkartCustomerServiceAgent
    print("✅ Company prototype agents imported successfully")
except ImportError as e:
    print(f"⚠️ Warning: Could not import prototype agents: {e}")
    AmazonCustomerServiceAgent = None
    FacebookCustomerServiceAgent = None
    FlipkartCustomerServiceAgent = None

# Load environment variables
load_dotenv()

# Enhanced TypedDict for Workflow State
class WorkflowState(TypedDict):
    # Input data from conversational agent
    conversation_json: Optional[Dict[str, Any]]
    conversation_file_path: Optional[str]
    
    # Company routing information
    detected_company: Optional[str]
    company_confidence: Optional[float]
    routing_decision: Optional[str]
    
    # Prototype execution results
    prototype_result: Optional[Dict[str, Any]]
    prototype_output_file: Optional[str]
    
    # Workflow management
    processing_stage: str
    processing_timestamp: Optional[str]
    errors: List[str]
    workflow_status: str  # "pending", "routing", "processing", "completed", "failed"

# Utility functions
def ensure_folders_exist():
    """Create necessary folders if they don't exist"""
    os.makedirs("output", exist_ok=True)
    os.makedirs("workflow_logs", exist_ok=True)

def get_timestamped_filename(prefix: str, extension: str, folder: str) -> str:
    """Generate timestamped filename in specified folder"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"{prefix}_{timestamp}.{extension}")

def save_workflow_log(state: WorkflowState, stage: str, message: str):
    """Save workflow progress to log file"""
    ensure_folders_exist()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "stage": stage,
        "message": message,
        "detected_company": state.get("detected_company"),
        "workflow_status": state.get("workflow_status")
    }
    
    log_file = os.path.join("workflow_logs", "routing_workflow.log")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + "\n")

# ====================================
# WORKFLOW NODES
# ====================================

def conversation_input_node(state: WorkflowState) -> WorkflowState:
    """Load and validate conversation JSON from conversational agent"""
    updates = {}
    
    try:
        print("\n" + "="*60)
        print("🔄 LANGGRAPH WORKFLOW - CONVERSATION INPUT")
        print("="*60)
        
        conversation_json = state.get("conversation_json")
        conversation_file_path = state.get("conversation_file_path")
        
        # Load from file if path provided but no JSON
        if conversation_file_path and not conversation_json:
            print(f"📂 Loading conversation from: {conversation_file_path}")
            with open(conversation_file_path, 'r', encoding='utf-8') as f:
                conversation_json = json.load(f)
        
        if not conversation_json:
            raise Exception("No conversation JSON provided")
        
        # Validate required fields
        company_info = conversation_json.get("company_info", {})
        if not company_info.get("company_name"):
            raise Exception("No company name found in conversation JSON")
        
        print(f"✅ Conversation loaded successfully")
        print(f"📊 Customer: {conversation_json.get('customer_info', {}).get('name', 'Unknown')}")
        print(f"🏢 Company: {company_info.get('company_name', 'Unknown')}")
        print(f"📞 Confidence: {company_info.get('confidence', 0.0):.2f}")
        
        save_workflow_log(state, "conversation_input", "Conversation JSON loaded and validated")
        
        updates.update({
            "conversation_json": conversation_json,
            "processing_stage": "conversation_loaded",
            "workflow_status": "routing",
            "processing_timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        error_msg = f"Conversation input error: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        save_workflow_log(state, "conversation_input_error", error_msg)
        updates.update({
            "errors": state.get("errors", []) + [error_msg],
            "processing_stage": "input_failed",
            "workflow_status": "failed"
        })
    
    return updates

def company_routing_node(state: WorkflowState) -> WorkflowState:
    """Analyze company information and determine routing decision"""
    updates = {}
    
    try:
        print("\n" + "="*50)
        print("🎯 COMPANY ROUTING ANALYSIS")
        print("="*50)
        
        conversation_json = state.get("conversation_json", {})
        company_info = conversation_json.get("company_info", {})
        
        company_name = company_info.get("company_name", "").lower()
        company_confidence = company_info.get("confidence", 0.0)
        
        print(f"🔍 Analyzing company: '{company_name}' (confidence: {company_confidence:.2f})")
        
        # Determine routing decision
        routing_decision = None
        detected_company = None
        
        if "amazon" in company_name:
            if AmazonCustomerServiceAgent:
                routing_decision = "amazon_prototype"
                detected_company = "amazon"
                print("🟠 ➡️  Routing to Amazon Customer Service Prototype")
            else:
                raise Exception("Amazon prototype agent not available")
                
        elif "facebook" in company_name:
            if FacebookCustomerServiceAgent:
                routing_decision = "facebook_prototype"
                detected_company = "facebook"
                print("🔵 ➡️  Routing to Facebook Customer Service Prototype")
            else:
                raise Exception("Facebook prototype agent not available")
                
        elif "flipkart" in company_name:
            if FlipkartCustomerServiceAgent:
                routing_decision = "flipkart_prototype"
                detected_company = "flipkart"
                print("🟡 ➡️  Routing to Flipkart Customer Service Prototype")
            else:
                raise Exception("Flipkart prototype agent not available")
        else:
            raise Exception(f"No prototype available for company: {company_name}")
        
        # Confidence check
        if company_confidence < 0.7:
            print(f"⚠️ Low confidence ({company_confidence:.2f}) - proceeding with caution")
        
        save_workflow_log(state, "company_routing", f"Routing to {detected_company} prototype")
        
        updates.update({
            "detected_company": detected_company,
            "company_confidence": company_confidence,
            "routing_decision": routing_decision,
            "processing_stage": "routing_decided",
            "workflow_status": "processing"
        })
        
    except Exception as e:
        error_msg = f"Company routing error: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        save_workflow_log(state, "company_routing_error", error_msg)
        updates.update({
            "errors": state.get("errors", []) + [error_msg],
            "processing_stage": "routing_failed",
            "workflow_status": "failed"
        })
    
    return updates

def amazon_prototype_node(state: WorkflowState) -> WorkflowState:
    """Execute Amazon customer service prototype"""
    updates = {}
    
    try:
        print("\n" + "="*60)
        print("🟠 AMAZON CUSTOMER SERVICE PROTOTYPE EXECUTION")
        print("="*60)
        
        if not AmazonCustomerServiceAgent:
            raise Exception("Amazon prototype agent not available")
        
        # Initialize Amazon agent
        amazon_agent = AmazonCustomerServiceAgent()
        
        # Get conversation data
        conversation_json = state.get("conversation_json", {})
        customer_info = conversation_json.get("customer_info", {})
        complaint_info = conversation_json.get("complaint_info", {})
        
        print(f"👤 Processing customer: {customer_info.get('name', 'Unknown')}")
        print(f"📞 Phone: {customer_info.get('phone', 'Unknown')}")
        print(f"❓ Issue: {complaint_info.get('description', 'Unknown')}")
        
        # Customer verification
        customer_verified = amazon_agent.verify_customer(
            phone=customer_info.get('phone')
        ) is not None
        
        # Create comprehensive prototype result
        prototype_result = {
            "workflow_info": {
                "prototype_name": "Amazon Customer Service",
                "execution_timestamp": datetime.now().isoformat(),
                "routing_confidence": state.get("company_confidence", 0.0)
            },
            "customer_verification": {
                "verified": customer_verified,
                "verification_method": "phone_number"
            },
            "processing_status": {
                "status": "completed",
                "fraud_detected": not customer_verified
            },
            "original_conversation": conversation_json,
            "prototype_metadata": {
                "agent_type": "Amazon",
                "processing_stage": "prototype_completed",
                "workflow_version": "1.0"
            }
        }
        
        # Save Amazon prototype result
        ensure_folders_exist()
        amazon_file = get_timestamped_filename("amazon_prototype_result", "json", "output")
        with open(amazon_file, 'w', encoding='utf-8') as f:
            json.dump(prototype_result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Amazon prototype result saved: {amazon_file}")
        print(f"✅ Customer verification: {'PASSED' if customer_verified else 'FAILED (Potential Fraud)'}")
        
        save_workflow_log(state, "amazon_prototype", "Amazon prototype executed successfully")
        
        updates.update({
            "prototype_result": prototype_result,
            "prototype_output_file": amazon_file,
            "processing_stage": "prototype_completed",
            "workflow_status": "completed"
        })
        
    except Exception as e:
        error_msg = f"Amazon prototype error: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        save_workflow_log(state, "amazon_prototype_error", error_msg)
        updates.update({
            "errors": state.get("errors", []) + [error_msg],
            "processing_stage": "prototype_failed",
            "workflow_status": "failed"
        })
    
    return updates

def facebook_prototype_node(state: WorkflowState) -> WorkflowState:
    """Execute Facebook customer service prototype"""
    updates = {}
    
    try:
        print("\n" + "="*60)
        print("🔵 FACEBOOK CUSTOMER SERVICE PROTOTYPE EXECUTION")
        print("="*60)
        
        if not FacebookCustomerServiceAgent:
            raise Exception("Facebook prototype agent not available")
        
        # Initialize Facebook agent
        facebook_agent = FacebookCustomerServiceAgent()
        
        # Get conversation data
        conversation_json = state.get("conversation_json", {})
        customer_info = conversation_json.get("customer_info", {})
        complaint_info = conversation_json.get("complaint_info", {})
        
        print(f"👤 Processing customer: {customer_info.get('name', 'Unknown')}")
        print(f"📞 Phone: {customer_info.get('phone', 'Unknown')}")
        print(f"❓ Issue: {complaint_info.get('description', 'Unknown')}")
        
        # Customer verification
        customer_verified = facebook_agent.verify_customer(
            phone=customer_info.get('phone')
        ) is not None
        
        # Create comprehensive prototype result
        prototype_result = {
            "workflow_info": {
                "prototype_name": "Facebook Customer Service",
                "execution_timestamp": datetime.now().isoformat(),
                "routing_confidence": state.get("company_confidence", 0.0)
            },
            "customer_verification": {
                "verified": customer_verified,
                "verification_method": "phone_number"
            },
            "processing_status": {
                "status": "completed",
                "fraud_detected": not customer_verified
            },
            "original_conversation": conversation_json,
            "prototype_metadata": {
                "agent_type": "Facebook",
                "processing_stage": "prototype_completed",
                "workflow_version": "1.0"
            }
        }
        
        # Save Facebook prototype result
        ensure_folders_exist()
        facebook_file = get_timestamped_filename("facebook_prototype_result", "json", "output")
        with open(facebook_file, 'w', encoding='utf-8') as f:
            json.dump(prototype_result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Facebook prototype result saved: {facebook_file}")
        print(f"✅ Customer verification: {'PASSED' if customer_verified else 'FAILED (Potential Fraud)'}")
        
        save_workflow_log(state, "facebook_prototype", "Facebook prototype executed successfully")
        
        updates.update({
            "prototype_result": prototype_result,
            "prototype_output_file": facebook_file,
            "processing_stage": "prototype_completed",
            "workflow_status": "completed"
        })
        
    except Exception as e:
        error_msg = f"Facebook prototype error: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        save_workflow_log(state, "facebook_prototype_error", error_msg)
        updates.update({
            "errors": state.get("errors", []) + [error_msg],
            "processing_stage": "prototype_failed",
            "workflow_status": "failed"
        })
    
    return updates

def flipkart_prototype_node(state: WorkflowState) -> WorkflowState:
    """Execute Flipkart customer service prototype"""
    updates = {}
    
    try:
        print("\n" + "="*60)
        print("🟡 FLIPKART CUSTOMER SERVICE PROTOTYPE EXECUTION")
        print("="*60)
        
        if not FlipkartCustomerServiceAgent:
            raise Exception("Flipkart prototype agent not available")
        
        # Initialize Flipkart agent
        flipkart_agent = FlipkartCustomerServiceAgent()
        
        # Get conversation data
        conversation_json = state.get("conversation_json", {})
        customer_info = conversation_json.get("customer_info", {})
        complaint_info = conversation_json.get("complaint_info", {})
        
        print(f"👤 Processing customer: {customer_info.get('name', 'Unknown')}")
        print(f"📞 Phone: {customer_info.get('phone', 'Unknown')}")
        print(f"❓ Issue: {complaint_info.get('description', 'Unknown')}")
        
        # Customer verification
        customer_verified = flipkart_agent.verify_customer(
            phone=customer_info.get('phone')
        ) is not None
        
        # Create comprehensive prototype result
        prototype_result = {
            "workflow_info": {
                "prototype_name": "Flipkart Customer Service",
                "execution_timestamp": datetime.now().isoformat(),
                "routing_confidence": state.get("company_confidence", 0.0)
            },
            "customer_verification": {
                "verified": customer_verified,
                "verification_method": "phone_number"
            },
            "processing_status": {
                "status": "completed",
                "fraud_detected": not customer_verified
            },
            "original_conversation": conversation_json,
            "prototype_metadata": {
                "agent_type": "Flipkart",
                "processing_stage": "prototype_completed",
                "workflow_version": "1.0"
            }
        }
        
        # Save Flipkart prototype result
        ensure_folders_exist()
        flipkart_file = get_timestamped_filename("flipkart_prototype_result", "json", "output")
        with open(flipkart_file, 'w', encoding='utf-8') as f:
            json.dump(prototype_result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Flipkart prototype result saved: {flipkart_file}")
        
        if customer_verified:
            print("✅ Customer verification: PASSED")
        else:
            print("❌ Customer verification: FAILED (Potential Fraud)")
        
        save_workflow_log(state, "flipkart_prototype", f"Prototype execution completed - Verified: {customer_verified}")
        
        updates.update({
            "prototype_result": prototype_result,
            "prototype_output_file": flipkart_file,
            "processing_stage": "prototype_completed",
            "workflow_status": "completed",
            "processing_timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        error_msg = f"Flipkart prototype execution failed: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        save_workflow_log(state, "flipkart_prototype_error", error_msg)
        updates.update({
            "errors": state.get("errors", []) + [error_msg],
            "processing_stage": "prototype_failed",
            "workflow_status": "failed"
        })
    
    return updates

# ====================================
# CONDITIONAL ROUTING FUNCTIONS
# ====================================

def should_route_to_prototype(state: WorkflowState) -> str:
    """Determine the next step after company routing analysis"""
    processing_stage = state.get("processing_stage", "")
    routing_decision = state.get("routing_decision")
    errors = state.get("errors", [])
    
    if errors:
        return "end"
    elif processing_stage == "routing_decided" and routing_decision:
        return routing_decision  # "amazon_prototype", "facebook_prototype", or "flipkart_prototype"
    else:
        return "end"

def workflow_should_continue(state: WorkflowState) -> str:
    """Determine workflow continuation after input processing"""
    processing_stage = state.get("processing_stage", "")
    errors = state.get("errors", [])
    
    if errors:
        return "end"
    elif processing_stage == "conversation_loaded":
        return "company_routing"
    else:
        return "end"

# ====================================
# WORKFLOW GRAPH CONSTRUCTION
# ====================================

def create_routing_workflow():
    """Create the company routing workflow graph"""
    workflow = StateGraph(WorkflowState)
    
    # Add workflow nodes
    workflow.add_node("conversation_input", conversation_input_node)
    workflow.add_node("company_routing", company_routing_node)
    workflow.add_node("amazon_prototype", amazon_prototype_node)
    workflow.add_node("facebook_prototype", facebook_prototype_node)
    workflow.add_node("flipkart_prototype", flipkart_prototype_node)
    
    # Set entry point
    workflow.set_entry_point("conversation_input")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "conversation_input",
        workflow_should_continue,
        {
            "company_routing": "company_routing",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "company_routing",
        should_route_to_prototype,
        {
            "amazon_prototype": "amazon_prototype",
            "facebook_prototype": "facebook_prototype",
            "flipkart_prototype": "flipkart_prototype",
            "end": END
        }
    )
    
    # Prototype nodes end the workflow
    workflow.add_edge("amazon_prototype", END)
    workflow.add_edge("facebook_prototype", END)
    workflow.add_edge("flipkart_prototype", END)
    
    return workflow.compile()

# ====================================
# MAIN WORKFLOW EXECUTION
# ====================================

def execute_routing_workflow(conversation_json: Dict[str, Any] = None, 
                           conversation_file_path: str = None) -> Optional[Dict[str, Any]]:
    """
    Execute the complete routing workflow
    
    Args:
        conversation_json: Direct JSON input from conversational agent
        conversation_file_path: Path to saved conversation JSON file
    
    Returns:
        Final workflow result with prototype execution details
    """
    
    print("\n" + "="*70)
    print("🚀 STARTING LANGGRAPH ROUTING WORKFLOW")
    print("="*70)
    
    # Initialize workflow state
    initial_state: WorkflowState = {
        "conversation_json": conversation_json,
        "conversation_file_path": conversation_file_path,
        "detected_company": None,
        "company_confidence": None,
        "routing_decision": None,
        "prototype_result": None,
        "prototype_output_file": None,
        "processing_stage": "initializing",
        "processing_timestamp": datetime.now().isoformat(),
        "errors": [],
        "workflow_status": "pending"
    }
    
    try:
        # Create and execute workflow
        app = create_routing_workflow()
        final_state = app.invoke(initial_state)
        
        # Extract results
        workflow_status = final_state.get("workflow_status", "unknown")
        prototype_result = final_state.get("prototype_result")
        errors = final_state.get("errors", [])
        
        print("\n" + "="*70)
        if workflow_status == "completed" and prototype_result:
            print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
            print(f"🎯 Routed to: {final_state.get('detected_company', 'Unknown').title()}")
            print(f"📁 Output saved: {final_state.get('prototype_output_file', 'Unknown')}")
        else:
            print("❌ WORKFLOW FAILED OR INCOMPLETE")
            if errors:
                print("🔍 Errors encountered:")
                for error in errors:
                    print(f"   • {error}")
        print("="*70)
        
        return final_state
        
    except Exception as e:
        print(f"\n❌ Workflow execution error: {str(e)}")
        return None

# ====================================
# TESTING AND DEMONSTRATION
# ====================================

def test_workflow_with_sample_data():
    """Test the workflow with sample conversation data"""
    
    # Sample Amazon conversation
    amazon_sample = {
        "customer_info": {
            "name": "John Smith",
            "phone": "555-0123",
            "email": "john.smith@email.com"
        },
        "complaint_info": {
            "description": "My Amazon order was delayed and I want a refund",
            "category": "shipping",
            "urgency_level": "medium",
            "order_id": "AMZ123456789"
        },
        "company_info": {
            "company_name": "Amazon",
            "confidence": 0.95
        },
        "status": "conversation_completed"
    }
    
    # Sample Facebook conversation
    facebook_sample = {
        "customer_info": {
            "name": "Sarah Johnson",
            "phone": "555-0456",
            "email": "sarah.j@email.com"
        },
        "complaint_info": {
            "description": "My Facebook account was hacked and I can't log in",
            "category": "security",
            "urgency_level": "high"
        },
        "company_info": {
            "company_name": "Facebook",
            "confidence": 0.88
        },
        "status": "conversation_completed"
    }
    
    print("🧪 Testing workflow with sample data...")
    
    # Test Amazon routing
    print("\n🟠 Testing Amazon routing...")
    amazon_result = execute_routing_workflow(conversation_json=amazon_sample)
    
    # Test Facebook routing
    print("\n🔵 Testing Facebook routing...")
    facebook_result = execute_routing_workflow(conversation_json=facebook_sample)
    
    return amazon_result, facebook_result

if __name__ == "__main__":
    """
    Standalone execution for testing the LangGraph workflow
    """
    print("🔧 LangGraph Workflow - Standalone Testing Mode")
    
    # Test with sample data
    test_workflow_with_sample_data()