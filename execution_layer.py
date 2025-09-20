"""
Step 3: Execution Layer - Procedural Plan Execution System

This module implements an intelligent execution layer that:
1. Parses procedural plans from the Decision Engine
2. Executes steps using LangChain agents and tools
3. Provides conversational interaction with users
4. Implements confidence checking and human escalation
5. Logs all interactions for learning and improvement

Author: Decision Engine System
Date: September 2025
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

# LangChain imports
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_core.callbacks import BaseCallbackHandler

# Import our existing modules
from knowledge_base import CompanyKnowledgeBase
from decision_engine import DecisionEngine, ProceduralPlan, CaseFingerprint

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for execution session"""
    session_id: str
    user_id: str
    case_fingerprint: CaseFingerprint
    procedural_plan: ProceduralPlan
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    confidence_scores: List[float] = field(default_factory=list)
    escalation_triggered: bool = False
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """Result of executing a procedural step"""
    success: bool
    response: str
    confidence_score: float
    step_completed: bool
    escalation_required: bool
    next_action: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0


class ConfidenceAnalyzer:
    """Analyzes response confidence for escalation decisions"""
    
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        
    def analyze_confidence(self, response: str, context: Dict[str, Any]) -> float:
        """
        Analyze confidence score for a response
        In production, this would use a trained classifier
        """
        confidence = 0.8  # Base confidence
        
        # Reduce confidence for uncertainty indicators
        uncertainty_indicators = [
            "i'm not sure", "i don't know", "uncertain", "unclear",
            "might be", "possibly", "perhaps", "could be", "?"
        ]
        
        response_lower = response.lower()
        for indicator in uncertainty_indicators:
            if indicator in response_lower:
                confidence -= 0.2
                
        # Reduce confidence for very short responses
        if len(response.split()) < 10:
            confidence -= 0.1
            
        # Increase confidence for specific, detailed responses
        if len(response.split()) > 50:
            confidence += 0.1
            
        # Check if response addresses the user's query
        user_query = context.get('user_query', '').lower()
        if user_query and any(word in response_lower for word in user_query.split()):
            confidence += 0.1
            
        return max(0.0, min(1.0, confidence))


class ExecutionLogger:
    """Logs execution events for analysis and learning"""
    
    def __init__(self, log_file: str = "execution_logs.jsonl"):
        self.log_file = Path(log_file)
        
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an execution event"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
            
        logger.info(f"Logged {event_type}: {data.get('session_id', 'N/A')}")


class HumanEscalationHandler:
    """Handles escalation to human agents"""
    
    def __init__(self):
        self.escalation_queue = []
        
    def escalate(self, context: ExecutionContext, reason: str) -> str:
        """Escalate case to human agent"""
        escalation_data = {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "case_type": context.case_fingerprint.case_type,
            "urgency": context.case_fingerprint.urgency,
            "reason": reason,
            "conversation_history": context.conversation_history,
            "current_step": context.current_step,
            "procedural_plan": context.procedural_plan.__dict__,
            "escalated_at": datetime.now().isoformat()
        }
        
        self.escalation_queue.append(escalation_data)
        
        logger.warning(f"Case escalated to human: {context.session_id} - {reason}")
        
        return (
            "I understand this is important to you. I'm connecting you with one of our "
            "specialized agents who can provide more detailed assistance. They'll have "
            "access to your full conversation history and case details. Please hold for "
            "just a moment."
        )
    
    def get_escalation_queue(self) -> List[Dict[str, Any]]:
        """Get current escalation queue"""
        return self.escalation_queue.copy()


class ExecutionTools:
    """Custom tools for the execution agent"""
    
    def __init__(self, knowledge_base: CompanyKnowledgeBase):
        self.knowledge_base = knowledge_base
        
    def get_tools(self) -> List[Tool]:
        """Get list of available tools for the agent"""
        return [
            Tool(
                name="search_company_policy",
                description="Search company policies and procedures for specific information",
                func=self._search_policy
            ),
            Tool(
                name="verify_account_details",
                description="Verify customer account information and status",
                func=self._verify_account
            ),
            Tool(
                name="check_billing_history",
                description="Check customer billing and transaction history",
                func=self._check_billing
            ),
            Tool(
                name="process_refund_request",
                description="Process or validate refund requests",
                func=self._process_refund
            ),
            Tool(
                name="escalate_technical_issue",
                description="Escalate technical issues to appropriate team",
                func=self._escalate_technical
            )
        ]
    
    def _search_policy(self, query: str) -> str:
        """Search company policies"""
        try:
            results = self.knowledge_base.search_documents(query, top_k=3)
            if results:
                return f"Found relevant policies:\n" + "\n".join([
                    f"- {result['content'][:200]}..." for result in results
                ])
            return "No relevant policies found for this query."
        except Exception as e:
            logger.error(f"Policy search error: {e}")
            return "Unable to search policies at this time."
    
    def _verify_account(self, account_info: str) -> str:
        """Verify account details (simulated)"""
        # In production, this would integrate with customer database
        return f"Account verified: {account_info}. Status: Active, Premium tier."
    
    def _check_billing(self, customer_id: str) -> str:
        """Check billing history (simulated)"""
        # In production, this would query billing system
        return "Recent billing: $29.99 subscription charged on 2025-09-15. No failed payments."
    
    def _process_refund(self, request_details: str) -> str:
        """Process refund request (simulated)"""
        # In production, this would interface with payment processing system
        return f"Refund request processed: {request_details}. Refund ID: RF_20250921_001"
    
    def _escalate_technical(self, issue_details: str) -> str:
        """Escalate technical issue"""
        return f"Technical issue escalated: {issue_details}. Ticket ID: TECH_20250921_001"


class ExecutionLayer:
    """Main execution layer for procedural plan execution"""
    
    def __init__(self, 
                 knowledge_base: CompanyKnowledgeBase,
                 decision_engine: DecisionEngine,
                 confidence_threshold: float = 0.6,
                 max_conversation_turns: int = 20):
        
        self.knowledge_base = knowledge_base
        self.decision_engine = decision_engine
        self.confidence_threshold = confidence_threshold
        self.max_conversation_turns = max_conversation_turns
        
        # Initialize components
        self.confidence_analyzer = ConfidenceAnalyzer(confidence_threshold)
        self.execution_logger = ExecutionLogger()
        self.escalation_handler = HumanEscalationHandler()
        self.tools = ExecutionTools(knowledge_base)
        
        # Initialize LangChain components
        self._initialize_agent()
        
        logger.info("Execution Layer initialized successfully")
            
    def _initialize_agent(self):
        """Initialize the LangChain conversational agent"""
        try:
            # Get the same LLM used in decision engine with proper parameters
            llm = self.decision_engine._initialize_llm(
                model=os.getenv("DEFAULT_LLM_MODEL", "llama-3.1-8b-instant"),
                use_groq=True,
                temperature=0.1
            )
            
            # Create memory for conversation
            self.memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                return_messages=True,
                k=10  # Remember last 10 exchanges
            )
            
            # Create retrieval chain for knowledge base access
            if hasattr(self.knowledge_base, 'vector_store') and self.knowledge_base.vector_store:
                retriever = self.knowledge_base.vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 4}
                )
                
                self.retrieval_chain = ConversationalRetrievalChain.from_llm(
                    llm=llm,
                    retriever=retriever,
                    memory=self.memory,
                    return_source_documents=False,
                    verbose=True
                )
            else:
                logger.warning("Vector store not available, skipping retrieval chain")
                self.retrieval_chain = None
            
            # Initialize agent with tools
            self.agent = initialize_agent(
                tools=self.tools.get_tools(),
                llm=llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True,
                max_iterations=3
            )
            
            logger.info("Agent initialized with tools and memory")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    def create_execution_context(self, 
                                case_fingerprint: CaseFingerprint,
                                user_id: str = "user_001") -> ExecutionContext:
        """Create execution context for a new case"""
        
        # Generate procedural plan using decision engine
        procedural_plan = self.decision_engine.generate_procedural_plan(case_fingerprint)
        
        session_id = f"EXEC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{case_fingerprint.case_type}"
        
        context = ExecutionContext(
            session_id=session_id,
            user_id=user_id,
            case_fingerprint=case_fingerprint,
            procedural_plan=procedural_plan
        )
        
        # Log execution start
        self.execution_logger.log_event("execution_started", {
            "session_id": session_id,
            "case_type": case_fingerprint.case_type,
            "plan_type": procedural_plan.plan_type
        })
        
        return context
    
    def execute_step(self, 
                    context: ExecutionContext, 
                    user_query: str) -> ExecutionResult:
        """Execute a single step in the procedural plan"""
        
        start_time = datetime.now()
        
        try:
            # Get current step from procedural plan
            if context.current_step >= len(context.procedural_plan.steps):
                return ExecutionResult(
                    success=True,
                    response="All procedural steps have been completed. Is there anything else I can help you with?",
                    confidence_score=1.0,
                    step_completed=True,
                    escalation_required=False
                )
            
            current_step = context.procedural_plan.steps[context.current_step]
            
            # Prepare context for agent
            step_context = f"""
            Current procedural step: {current_step.description}
            Team responsible: {current_step.responsible_team}
            Conditions: {current_step.conditions}
            User query: {user_query}
            
            Please respond helpfully while following the procedural guidelines.
            """
            
            # Execute using agent
            response = self.agent.run(step_context)
            
            # Analyze confidence
            confidence_score = self.confidence_analyzer.analyze_confidence(
                response, {"user_query": user_query, "step": current_step.__dict__}
            )
            
            # Check for escalation conditions
            escalation_required = (
                confidence_score < self.confidence_threshold or
                any(trigger in user_query.lower() for trigger in [
                    "speak to manager", "human agent", "escalate", "supervisor"
                ]) or
                current_step.escalation_triggers and 
                any(trigger.lower() in user_query.lower() for trigger in current_step.escalation_triggers)
            )
            
            # Update conversation history
            context.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "user_query": user_query,
                "agent_response": response,
                "step_number": context.current_step + 1,
                "confidence_score": confidence_score
            })
            
            # Move to next step if current step is completed
            step_completed = len(context.conversation_history) > 0 and not escalation_required
            if step_completed:
                context.current_step += 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Log execution step
            self.execution_logger.log_event("step_executed", {
                "session_id": context.session_id,
                "step_number": context.current_step,
                "confidence_score": confidence_score,
                "escalation_required": escalation_required,
                "execution_time": execution_time
            })
            
            return ExecutionResult(
                success=True,
                response=response,
                confidence_score=confidence_score,
                step_completed=step_completed,
                escalation_required=escalation_required,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Execution error in step {context.current_step}: {e}")
            
            return ExecutionResult(
                success=False,
                response="I encountered an error processing your request. Let me connect you with a human agent.",
                confidence_score=0.0,
                step_completed=False,
                escalation_required=True,
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    def handle_conversation(self, 
                           context: ExecutionContext, 
                           user_query: str) -> Tuple[str, bool]:
        """
        Handle a conversational turn
        Returns: (response, should_continue)
        """
        
        # Check if conversation should continue
        if len(context.conversation_history) >= self.max_conversation_turns:
            escalation_response = self.escalation_handler.escalate(
                context, "Maximum conversation turns reached"
            )
            return escalation_response, False
        
        # Execute current step
        result = self.execute_step(context, user_query)
        
        # Handle escalation
        if result.escalation_required:
            escalation_reason = "Low confidence" if result.confidence_score < self.confidence_threshold else "User requested escalation"
            escalation_response = self.escalation_handler.escalate(context, escalation_reason)
            return escalation_response, False
        
        # Handle errors
        if not result.success:
            escalation_response = self.escalation_handler.escalate(
                context, f"Execution error: {result.error_message}"
            )
            return escalation_response, False
        
        return result.response, True
    
    def get_execution_summary(self, context: ExecutionContext) -> Dict[str, Any]:
        """Get summary of execution session"""
        return {
            "session_id": context.session_id,
            "case_type": context.case_fingerprint.case_type,
            "total_steps": len(context.procedural_plan.steps),
            "completed_steps": context.current_step,
            "conversation_turns": len(context.conversation_history),
            "average_confidence": np.mean(context.confidence_scores) if context.confidence_scores else 0.0,
            "escalation_triggered": context.escalation_triggered,
            "execution_duration": (datetime.now() - context.created_at).total_seconds()
        }


def main():
    """Demo the execution layer"""
    print("🚀 Execution Layer Demo")
    print("=" * 50)
    
    try:
        # Initialize components
        print("Initializing components...")
        knowledge_base = CompanyKnowledgeBase()
        decision_engine = DecisionEngine(knowledge_base)
        execution_layer = ExecutionLayer(knowledge_base, decision_engine)
        
        # Create test case
        test_case = CaseFingerprint(
            case_type="Billing_Dispute",
            urgency="High",
            customer_anger_level="Moderate",
            request_contains_refund=True,
            account_type="Premium",
            previous_interactions=1,
            case_age_days=2,
            additional_attributes=["dispute_amount:$29.99", "auto_renewal:True"]
        )
        
        # Create execution context
        print(f"\\nCreating execution context for {test_case.case_type}...")
        context = execution_layer.create_execution_context(test_case)
        
        print(f"📋 Generated Plan: {context.procedural_plan.plan_type}")
        print(f"🔢 Total Steps: {len(context.procedural_plan.steps)}")
        print(f"🚨 Priority: {context.procedural_plan.priority}")
        
        # Simulate conversation
        user_queries = [
            "I was charged $29.99 for a subscription I thought I cancelled",
            "Can you check my account and process a refund?",
            "This is very frustrating, I want to speak to a manager"
        ]
        
        print("\\n🎭 Simulating User Conversation")
        print("-" * 40)
        
        for i, query in enumerate(user_queries, 1):
            print(f"\\n👤 User: {query}")
            
            response, should_continue = execution_layer.handle_conversation(context, query)
            print(f"🤖 Agent: {response}")
            
            if not should_continue:
                print("🚨 Conversation escalated to human agent")
                break
        
        # Show execution summary
        print("\\n📊 Execution Summary")
        print("-" * 30)
        summary = execution_layer.get_execution_summary(context)
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        # Show escalation queue
        escalations = execution_layer.escalation_handler.get_escalation_queue()
        if escalations:
            print(f"\\n⚠️  Escalation Queue: {len(escalations)} cases")
            for escalation in escalations:
                print(f"  - {escalation['session_id']}: {escalation['reason']}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
