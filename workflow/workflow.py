#!/usr/bin/env python3
"""
Centralized Customer Care Workflow
==================================

LangGraph workflow that orchestrates the customer care system:
1. Customer conversation → 2. Company routing → 3. Agent processing → 4. Solution delivery

This workflow uses LangGraph state management instead of JSON files for data flow.
"""

import os
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import our nodes
from nodes import (
    CustomerCareState,
    listener_node,
    routing_node,
    amazon_agent_node,
    facebook_agent_node,
    protocol_execution_node
)

class CustomerCareWorkflow:
    """
    Main workflow orchestrator using LangGraph
    Replaces the main.py workflow with a graph-based approach
    """
    
    def __init__(self):
        """Initialize the workflow graph"""
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(CustomerCareState)
        
        # Add nodes
        workflow.add_node("listener", listener_node)
        workflow.add_node("amazon_agent", amazon_agent_node)  
        workflow.add_node("facebook_agent", facebook_agent_node)
        workflow.add_node("protocol_execution", protocol_execution_node)
        
        # Add conditional routing node
        workflow.add_conditional_edges(
            "listener",  # From the listener node
            routing_node,  # Use routing_node as the condition function
            {
                "amazon_agent": "amazon_agent",
                "facebook_agent": "facebook_agent"
            }
        )
        
        # Both agents go to protocol execution
        workflow.add_edge("amazon_agent", "protocol_execution")
        workflow.add_edge("facebook_agent", "protocol_execution")
        
        # Protocol execution ends the workflow
        workflow.add_edge("protocol_execution", END)
        
        # Set entry point
        workflow.set_entry_point("listener")
        
        # Compile the graph
        return workflow.compile(checkpointer=self.memory)
    
    def run(self, initial_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the complete customer care workflow
        
        Args:
            initial_input: Optional initial state data
            
        Returns:
            Final state with customer care results
        """
        print("\n" + "="*60)
        print("🚀 CENTRALIZED CUSTOMER CARE SYSTEM (LangGraph)")
        print("="*60)
        
        # Initialize state
        if initial_input is None:
            initial_input = {}
        
        # Create thread configuration for memory
        config = {"configurable": {"thread_id": "customer_care_session"}}
        
        try:
            # Execute the workflow
            final_state = self.graph.invoke(initial_input, config)
            
            # Print results
            self._print_results(final_state)
            
            return final_state
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
    
    def _print_results(self, state: CustomerCareState):
        """Print the final workflow results"""
        print("\n" + "="*60)
        print("📋 WORKFLOW RESULTS")
        print("="*60)
        
        if state.get("error"):
            print(f"❌ Error: {state['error']}")
            return
        
        # Customer Information
        print("\n👤 CUSTOMER INFORMATION:")
        print(f"  Name: {state.get('customer_name', 'N/A')}")
        print(f"  Email: {state.get('customer_email', 'N/A')}")
        print(f"  Phone: {state.get('customer_phone', 'N/A')}")
        print(f"  Product: {state.get('product_name', 'N/A')}")
        print(f"  Company: {state.get('company_name', 'N/A')}")
        
        # Issue Description
        print("\n🔍 ISSUE DESCRIPTION:")
        print(f"  {state.get('problem_description', 'N/A')}")
        
        # Agent Response
        print("\n🤖 AGENT PROTOCOL:")
        solution = state.get('final_solution', 'No solution generated')
        print(f"  {solution}")
        
        # Protocol Execution
        print("\n🎯 PROTOCOL EXECUTION:")
        execution = state.get('protocol_execution', 'No execution performed')
        print(f"  {execution}")
        
        # Customer Reassurance
        print("\n💬 CUSTOMER REASSURANCE:")
        reassurance = state.get('customer_reassurance', 'No reassurance message')
        print(f"  {reassurance}")
        
        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
        print("="*60)

def main():
    """
    Main entry point - replaces the main.py functionality
    """
    # Initialize workflow
    workflow = CustomerCareWorkflow()
    
    # Run the workflow
    result = workflow.run()
    
    # Optional: Save results (if needed)
    if result and not result.get("error"):
        print("\n💾 Results saved in workflow state")
    
    return result

def demo_run():
    """Run with demo data for testing"""
    print("🧪 DEMO MODE - Using sample data")
    
    workflow = CustomerCareWorkflow()
    
    # Demo input (similar to example_conversation_output.json)
    demo_input = {
        "audio_input": "demo_audio",
        "query": "My MacBook Pro suddenly stopped working"
    }
    
    result = workflow.run(demo_input)
    return result

if __name__ == "__main__":
    import sys
    
    # Check for demo mode
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_run()
    else:
        main()