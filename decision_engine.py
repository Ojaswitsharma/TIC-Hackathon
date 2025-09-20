"""
Decision Engine for Procedural Plan Generation

This module creates intelligent procedural plans based on case fingerprints
by combining company knowledge base retrieval with LLM reasoning.

Input: case_fingerprint (dict) with Case_Type, Urgency, Customer_Anger_Level, etc.
Process: Query knowledge base + Apply business rules + Generate structured plan
Output: Structured procedural plan with next actions and conditions

Author: Assistant
Date: September 20, 2025
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# LangChain imports
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, Runnable
from langchain_core.messages import BaseMessage
from langchain_community.vectorstores import FAISS

# LLM imports - with Groq support (primary) and Google Gemini (fallback)
try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    from langchain_openai import OpenAIEmbeddings
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Environment variables
from dotenv import load_dotenv
load_dotenv()

# Local imports
from knowledge_base import CompanyKnowledgeBase, SentenceTransformerEmbeddings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CaseType(Enum):
    """Enumeration of supported case types"""
    BILLING_DISPUTE = "Billing_Dispute"
    REFUND_REQUEST = "Refund_Request"
    TECHNICAL_SUPPORT = "Technical_Support"
    ACCOUNT_ACCESS = "Account_Access"
    PRODUCT_COMPLAINT = "Product_Complaint"
    GENERAL_INQUIRY = "General_Inquiry"
    ESCALATION = "Escalation"


class UrgencyLevel(Enum):
    """Urgency levels for case prioritization"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class CaseFingerprint:
    """Structured representation of a customer case"""
    case_type: str
    urgency: Union[float, str]
    customer_anger_level: str
    request_contains_refund: bool = False
    account_type: str = "Standard"
    previous_interactions: int = 0
    case_age_days: int = 0
    additional_attributes: List[str] = None
    
    def __post_init__(self):
        if self.additional_attributes is None:
            self.additional_attributes = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for processing"""
        return {
            "Case_Type": self.case_type,
            "Urgency": self.urgency,
            "Customer_Anger_Level": self.customer_anger_level,
            "Request_Contains_Refund": self.request_contains_refund,
            "Account_Type": self.account_type,
            "Previous_Interactions": self.previous_interactions,
            "Case_Age_Days": self.case_age_days,
            "Additional_Attributes": self.additional_attributes
        }


@dataclass
class ProceduralStep:
    """Individual step in a procedural plan"""
    step_number: int
    action: str
    description: str
    responsible_team: str = "Customer Service"
    estimated_time: str = "5-10 minutes"
    conditions: List[str] = None
    escalation_triggers: List[str] = None
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []
        if self.escalation_triggers is None:
            self.escalation_triggers = []


@dataclass
class ProceduralPlan:
    """Complete procedural plan for a case"""
    case_id: str
    plan_type: str
    priority: str
    estimated_resolution_time: str
    steps: List[ProceduralStep]
    escalation_required: bool = False
    special_notes: List[str] = None
    
    def __post_init__(self):
        if self.special_notes is None:
            self.special_notes = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "case_id": self.case_id,
            "plan_type": self.plan_type,
            "priority": self.priority,
            "estimated_resolution_time": self.estimated_resolution_time,
            "escalation_required": self.escalation_required,
            "special_notes": self.special_notes,
            "steps": [
                {
                    "step_number": step.step_number,
                    "action": step.action,
                    "description": step.description,
                    "responsible_team": step.responsible_team,
                    "estimated_time": step.estimated_time,
                    "conditions": step.conditions,
                    "escalation_triggers": step.escalation_triggers
                }
                for step in self.steps
            ]
        }


class BusinessRulesEngine:
    """Company-specific business rules and decision logic"""
    
    @staticmethod
    def determine_priority(case_fingerprint: Dict) -> str:
        """Determine case priority based on business rules"""
        urgency = case_fingerprint.get("Urgency", 0)
        anger_level = case_fingerprint.get("Customer_Anger_Level", "Low").lower()
        case_age = case_fingerprint.get("Case_Age_Days", 0)
        
        # Convert urgency to numeric if string
        if isinstance(urgency, str):
            urgency_map = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
            urgency = urgency_map.get(urgency.lower(), 0.5)
        
        # Business rules for priority determination
        if urgency >= 0.9 or anger_level in ["high", "extreme"] or case_age > 7:
            return "Critical"
        elif urgency >= 0.7 or anger_level == "moderate" or case_age > 3:
            return "High"
        elif urgency >= 0.4 or case_age > 1:
            return "Medium"
        else:
            return "Low"
    
    @staticmethod
    def requires_escalation(case_fingerprint: Dict) -> bool:
        """Determine if case requires immediate escalation"""
        case_type = case_fingerprint.get("Case_Type", "").lower()
        anger_level = case_fingerprint.get("Customer_Anger_Level", "").lower()
        previous_interactions = case_fingerprint.get("Previous_Interactions", 0)
        urgency = case_fingerprint.get("Urgency", 0)
        
        # Escalation triggers
        escalation_cases = ["billing_dispute", "escalation", "product_complaint"]
        high_anger = anger_level in ["high", "extreme"]
        multiple_interactions = previous_interactions >= 3
        high_urgency = urgency >= 0.8 if isinstance(urgency, (int, float)) else False
        
        return (case_type in escalation_cases or high_anger or 
                multiple_interactions or high_urgency)
    
    @staticmethod
    def estimate_resolution_time(case_fingerprint: Dict, priority: str) -> str:
        """Estimate resolution time based on case characteristics"""
        case_type = case_fingerprint.get("Case_Type", "").lower()
        
        base_times = {
            "billing_dispute": "2-4 hours",
            "refund_request": "1-2 hours", 
            "technical_support": "30 minutes - 2 hours",
            "account_access": "15-30 minutes",
            "product_complaint": "1-3 hours",
            "general_inquiry": "15-30 minutes",
            "escalation": "4-24 hours"
        }
        
        base_time = base_times.get(case_type, "1-2 hours")
        
        # Adjust based on priority
        if priority == "Critical":
            return f"URGENT: {base_time}"
        elif priority == "High":
            return f"Priority: {base_time}"
        else:
            return base_time


class DecisionEngine:
    """
    Intelligent Decision Engine for generating procedural plans
    
    Combines knowledge base retrieval, business rules, and LLM reasoning
    to create context-aware procedural plans for customer service cases.
    """
    
    def __init__(self, 
                 knowledge_base: Optional[CompanyKnowledgeBase] = None,
                 llm_model: str = None,
                 use_groq: bool = None,
                 use_google: bool = None,
                 use_openai: bool = None,
                 temperature: float = None):
        """
        Initialize the Decision Engine
        
        Args:
            knowledge_base: Pre-initialized knowledge base
            llm_model: LLM model to use (auto-detect from env if None)
            use_groq: Whether to use Groq (auto-detect if None)
            use_google: Whether to use Google Gemini (auto-detect if None)
            use_openai: Whether to use OpenAI (auto-detect if None)
            temperature: LLM temperature for creativity control
        """
        
        # Load environment variables
        self.llm_model = llm_model or os.getenv("DEFAULT_LLM_MODEL", "llama-3.1-8b-instant")
        self.temperature = temperature or float(os.getenv("LLM_TEMPERATURE", "0.1"))
        
        self.business_rules = BusinessRulesEngine()
        
        # Initialize knowledge base
        if knowledge_base:
            self.knowledge_base = knowledge_base
        else:
            self.knowledge_base = self._load_knowledge_base()
        
        # Initialize LLM with Groq priority, then Google Gemini, then OpenAI
        self.llm = self._initialize_llm(self.llm_model, use_groq, use_google, use_openai, self.temperature)
        
        # Initialize prompt templates
        self.prompt_templates = self._create_prompt_templates()
        
        # Create processing chains
        self.decision_chain = self._create_decision_chain()
        
        logger.info("Decision Engine initialized successfully")
    
    def _load_knowledge_base(self) -> CompanyKnowledgeBase:
        """Load or create knowledge base"""
        try:
            kb = CompanyKnowledgeBase()
            if os.path.exists("company_kb_index"):
                kb.load_index("company_kb_index")
                logger.info("Loaded existing knowledge base")
            else:
                logger.warning("No knowledge base found. Please run knowledge base creation first.")
            return kb
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            # Return a basic knowledge base
            return CompanyKnowledgeBase()
    
    def _initialize_llm(self, model: str, use_groq: Optional[bool], use_google: Optional[bool], use_openai: Optional[bool], temperature: float):
        """Initialize LLM with Groq priority, then Google Gemini, then OpenAI fallback"""
        
        # Auto-detect Groq availability
        if use_groq is None:
            use_groq = GROQ_AVAILABLE and bool(os.getenv("GROQ_API_KEY"))
        
        # Auto-detect Google Gemini availability
        if use_google is None:
            use_google = GOOGLE_AVAILABLE and bool(os.getenv("GOOGLE_API_KEY"))
        
        # Auto-detect OpenAI availability
        if use_openai is None:
            use_openai = OPENAI_AVAILABLE and bool(os.getenv("OPENAI_API_KEY"))
        
        # Priority 1: Groq LLM
        if use_groq and GROQ_AVAILABLE:
            try:
                llm = ChatGroq(
                    model=model,
                    temperature=temperature,
                    max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
                    groq_api_key=os.getenv("GROQ_API_KEY")
                )
                logger.info(f"Using Groq LLM: {model}")
                return llm
            except Exception as e:
                logger.warning(f"Groq LLM initialization failed: {e}")
        
        # Priority 2: Google Gemini (fallback)
        if use_google and GOOGLE_AVAILABLE:
            try:
                # Convert Groq model names to Gemini equivalents
                gemini_model = "gemini-1.5-flash" if "llama" in model.lower() else model
                llm = ChatGoogleGenerativeAI(
                    model=gemini_model,
                    temperature=temperature,
                    max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
                    google_api_key=os.getenv("GOOGLE_API_KEY")
                )
                logger.info(f"Using Google Gemini LLM as fallback: {gemini_model}")
                return llm
            except Exception as e:
                logger.warning(f"Google Gemini LLM initialization failed: {e}")
        
        # Priority 3: OpenAI (secondary fallback)
        if use_openai and OPENAI_AVAILABLE:
            try:
                # Convert model names to OpenAI equivalents
                openai_model = "gpt-3.5-turbo" if ("llama" in model.lower() or "gemini" in model.lower()) else model
                llm = ChatOpenAI(
                    model=openai_model,
                    temperature=temperature,
                    max_tokens=2000
                )
                logger.info(f"Using OpenAI LLM as secondary fallback: {openai_model}")
                return llm
            except Exception as e:
                logger.warning(f"OpenAI LLM initialization failed: {e}")
        
        # Priority 4: Mock LLM for demonstration
        logger.info("Using fallback Mock LLM (no API keys available)")
        return MockLLM()
    
    def _create_prompt_templates(self) -> Dict[str, PromptTemplate]:
        """Create prompt templates for different scenarios"""
        
        # Main decision prompt
        decision_prompt = PromptTemplate(
            input_variables=["case_fingerprint", "context", "priority", "escalation_required"],
            template="""
You are an expert customer service decision engine. Generate a detailed procedural plan 
for the following case based on company procedures and business rules.

CASE DETAILS:
{case_fingerprint}

BUSINESS ANALYSIS:
- Priority: {priority}
- Escalation Required: {escalation_required}

RELEVANT COMPANY PROCEDURES:
{context}

INSTRUCTIONS:
Create a structured procedural plan with specific steps, responsible teams, and timing.
Focus on efficient resolution while following company policies.

Return your response as a JSON object with this structure:
{{
    "plan_type": "string describing the type of plan",
    "steps": [
        {{
            "step_number": 1,
            "action": "brief action name",
            "description": "detailed description",
            "responsible_team": "team name",
            "estimated_time": "time estimate",
            "conditions": ["any conditions"],
            "escalation_triggers": ["escalation triggers"]
        }}
    ],
    "special_notes": ["any special considerations"]
}}

Procedural Plan:
"""
        )
        
        # Context extraction prompt
        context_prompt = PromptTemplate(
            input_variables=["case_type", "case_details"],
            template="Extract relevant procedures for {case_type} case: {case_details}"
        )
        
        return {
            "decision": decision_prompt,
            "context": context_prompt
        }
    
    def _create_decision_chain(self):
        """Create LangChain processing chain"""
        
        def get_relevant_context(case_fingerprint: Dict) -> str:
            """Retrieve relevant context from knowledge base"""
            try:
                case_type = case_fingerprint.get("Case_Type", "")
                query = f"{case_type} procedures policy guidelines"
                
                if self.knowledge_base.vector_store:
                    results = self.knowledge_base.search_similar(query, k=4)
                    context = "\n\n".join([doc.page_content for doc in results])
                    return context[:2000]  # Limit context length
                else:
                    return "No specific procedures found. Use general customer service guidelines."
            except Exception as e:
                logger.error(f"Error retrieving context: {e}")
                return "Use standard customer service procedures."
        
        def analyze_case(case_fingerprint: Dict) -> Dict:
            """Analyze case using business rules"""
            priority = self.business_rules.determine_priority(case_fingerprint)
            escalation_required = self.business_rules.requires_escalation(case_fingerprint)
            estimated_time = self.business_rules.estimate_resolution_time(case_fingerprint, priority)
            
            return {
                "priority": priority,
                "escalation_required": escalation_required,
                "estimated_time": estimated_time
            }
        
        # Create the chain
        chain = (
            RunnablePassthrough.assign(
                context=lambda x: get_relevant_context(x["case_fingerprint"]),
                analysis=lambda x: analyze_case(x["case_fingerprint"])
            )
            | RunnablePassthrough.assign(
                priority=lambda x: x["analysis"]["priority"],
                escalation_required=lambda x: x["analysis"]["escalation_required"],
                estimated_time=lambda x: x["analysis"]["estimated_time"]
            )
            | self.prompt_templates["decision"]
            | self.llm
            | JsonOutputParser()
        )
        
        return chain
    
    def generate_procedural_plan(self, 
                                case_fingerprint: Union[Dict, CaseFingerprint],
                                case_id: str = None) -> ProceduralPlan:
        """
        Generate a procedural plan for the given case
        
        Args:
            case_fingerprint: Case details as dict or CaseFingerprint object
            case_id: Unique case identifier
            
        Returns:
            ProceduralPlan object with structured plan
        """
        
        try:
            # Convert to dict if CaseFingerprint object
            if isinstance(case_fingerprint, CaseFingerprint):
                case_dict = case_fingerprint.to_dict()
            else:
                case_dict = case_fingerprint
            
            # Generate case ID if not provided
            if not case_id:
                case_id = f"CASE_{hash(str(case_dict)) % 100000:05d}"
            
            logger.info(f"Generating procedural plan for case {case_id}")
            
            # Run the decision chain
            result = self.decision_chain.invoke({"case_fingerprint": case_dict})
            
            # Extract business analysis
            priority = self.business_rules.determine_priority(case_dict)
            escalation_required = self.business_rules.requires_escalation(case_dict)
            estimated_time = self.business_rules.estimate_resolution_time(case_dict, priority)
            
            # Create procedural steps
            steps = []
            if "steps" in result:
                for step_data in result["steps"]:
                    step = ProceduralStep(
                        step_number=step_data.get("step_number", len(steps) + 1),
                        action=step_data.get("action", "Review case"),
                        description=step_data.get("description", "Review case details"),
                        responsible_team=step_data.get("responsible_team", "Customer Service"),
                        estimated_time=step_data.get("estimated_time", "5-10 minutes"),
                        conditions=step_data.get("conditions", []),
                        escalation_triggers=step_data.get("escalation_triggers", [])
                    )
                    steps.append(step)
            
            # Create procedural plan
            plan = ProceduralPlan(
                case_id=case_id,
                plan_type=result.get("plan_type", f"{case_dict.get('Case_Type', 'General')} Resolution"),
                priority=priority,
                estimated_resolution_time=estimated_time,
                steps=steps,
                escalation_required=escalation_required,
                special_notes=result.get("special_notes", [])
            )
            
            logger.info(f"Generated {len(steps)} procedural steps for case {case_id}")
            return plan
            
        except Exception as e:
            logger.error(f"Error generating procedural plan: {e}")
            # Return a basic fallback plan
            return self._create_fallback_plan(case_dict, case_id)
    
    def _create_fallback_plan(self, case_fingerprint: Dict, case_id: str) -> ProceduralPlan:
        """Create a basic fallback plan when LLM processing fails"""
        
        case_type = case_fingerprint.get("Case_Type", "General")
        priority = self.business_rules.determine_priority(case_fingerprint)
        
        # Basic steps based on case type
        if "billing" in case_type.lower():
            steps = [
                ProceduralStep(1, "Verify Account", "Verify customer account and billing history"),
                ProceduralStep(2, "Review Charges", "Review disputed charges and transactions"),
                ProceduralStep(3, "Determine Resolution", "Determine appropriate resolution action")
            ]
        elif "refund" in case_type.lower():
            steps = [
                ProceduralStep(1, "Verify Eligibility", "Check refund policy eligibility"),
                ProceduralStep(2, "Process Request", "Process refund according to guidelines"),
                ProceduralStep(3, "Confirm Resolution", "Confirm refund with customer")
            ]
        else:
            steps = [
                ProceduralStep(1, "Initial Review", "Review case details and customer history"),
                ProceduralStep(2, "Apply Procedures", "Apply relevant company procedures"),
                ProceduralStep(3, "Follow Up", "Follow up with customer on resolution")
            ]
        
        return ProceduralPlan(
            case_id=case_id,
            plan_type=f"{case_type} Resolution (Fallback)",
            priority=priority,
            estimated_resolution_time="1-2 hours",
            steps=steps,
            special_notes=["Generated using fallback procedures"]
        )
    
    def get_case_context(self, case_fingerprint: Dict, k: int = 5) -> List[str]:
        """Get relevant context documents for a case"""
        case_type = case_fingerprint.get("Case_Type", "")
        query = f"{case_type} procedures policy"
        
        try:
            results = self.knowledge_base.search_similar(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            logger.error(f"Error retrieving case context: {e}")
            return []


from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage


class MockLLM(Runnable):
    """Mock LLM for demonstration when OpenAI is not available"""
    
    def invoke(self, input_data, config=None, **kwargs) -> str:
        """Mock LLM response"""
        # Handle different input types
        if isinstance(input_data, str):
            prompt = input_data
        elif hasattr(input_data, 'text'):
            prompt = input_data.text
        else:
            prompt = str(input_data)
        
        if "billing" in prompt.lower():
            return json.dumps({
                "plan_type": "Billing Dispute Resolution",
                "steps": [
                    {
                        "step_number": 1,
                        "action": "Account Verification",
                        "description": "Verify customer account details and billing history",
                        "responsible_team": "Billing Team",
                        "estimated_time": "5-10 minutes",
                        "conditions": ["Customer authenticated"],
                        "escalation_triggers": ["Unable to verify account"]
                    },
                    {
                        "step_number": 2,
                        "action": "Charge Investigation",
                        "description": "Investigate disputed charges and transaction details",
                        "responsible_team": "Billing Team",
                        "estimated_time": "15-20 minutes",
                        "conditions": ["Account verified"],
                        "escalation_triggers": ["Complex billing discrepancy"]
                    },
                    {
                        "step_number": 3,
                        "action": "Resolution Action",
                        "description": "Apply appropriate resolution based on investigation",
                        "responsible_team": "Billing Team",
                        "estimated_time": "10-15 minutes",
                        "conditions": ["Investigation complete"],
                        "escalation_triggers": ["Refund over $500"]
                    }
                ],
                "special_notes": ["Document all findings", "Follow billing dispute procedures"]
            })
        else:
            return json.dumps({
                "plan_type": "General Customer Service Resolution",
                "steps": [
                    {
                        "step_number": 1,
                        "action": "Initial Assessment",
                        "description": "Assess customer issue and gather relevant information",
                        "responsible_team": "Customer Service",
                        "estimated_time": "5-10 minutes",
                        "conditions": [],
                        "escalation_triggers": ["Complex technical issue"]
                    },
                    {
                        "step_number": 2,
                        "action": "Apply Solution",
                        "description": "Apply appropriate solution based on company procedures",
                        "responsible_team": "Customer Service",
                        "estimated_time": "10-20 minutes",
                        "conditions": ["Issue assessed"],
                        "escalation_triggers": ["Solution not effective"]
                    }
                ],
                "special_notes": ["Follow standard procedures", "Document resolution"]
            })


def main():
    """Demo the Decision Engine functionality"""
    print("🎯 Decision Engine Demo")
    print("=" * 50)
    
    # Initialize decision engine
    decision_engine = DecisionEngine()
    
    # Sample case fingerprints
    sample_cases = [
        {
            "Case_Type": "Billing_Dispute",
            "Urgency": 0.7,
            "Customer_Anger_Level": "Moderate",
            "Request_Contains_Refund": True,
            "Account_Type": "Premium",
            "Previous_Interactions": 1,
            "Case_Age_Days": 2,
            "Additional_Attributes": ["Subscription_Charge", "Auto_Renewal"]
        },
        {
            "Case_Type": "Technical_Support",
            "Urgency": 0.9,
            "Customer_Anger_Level": "High",
            "Request_Contains_Refund": False,
            "Account_Type": "Enterprise",
            "Previous_Interactions": 3,
            "Case_Age_Days": 5,
            "Additional_Attributes": ["System_Outage", "Critical_Business_Impact"]
        },
        {
            "Case_Type": "Refund_Request",
            "Urgency": 0.4,
            "Customer_Anger_Level": "Low",
            "Request_Contains_Refund": True,
            "Account_Type": "Standard",
            "Previous_Interactions": 0,
            "Case_Age_Days": 1,
            "Additional_Attributes": ["Product_Return"]
        }
    ]
    
    # Process each case
    for i, case in enumerate(sample_cases, 1):
        print(f"\n🔍 Processing Case {i}: {case['Case_Type']}")
        print("-" * 40)
        
        # Generate procedural plan
        plan = decision_engine.generate_procedural_plan(case, f"CASE_{i:03d}")
        
        # Display results
        print(f"📋 Plan Type: {plan.plan_type}")
        print(f"🚨 Priority: {plan.priority}")
        print(f"⏱️ Estimated Time: {plan.estimated_resolution_time}")
        print(f"🔄 Escalation Required: {plan.escalation_required}")
        
        print(f"\n📝 Procedural Steps ({len(plan.steps)} steps):")
        for step in plan.steps:
            print(f"   {step.step_number}. {step.action}")
            print(f"      → {step.description}")
            print(f"      → Team: {step.responsible_team} | Time: {step.estimated_time}")
            if step.conditions:
                print(f"      → Conditions: {', '.join(step.conditions)}")
            if step.escalation_triggers:
                print(f"      → Escalation Triggers: {', '.join(step.escalation_triggers)}")
            print()
        
        if plan.special_notes:
            print(f"📌 Special Notes: {', '.join(plan.special_notes)}")
        
        print()


if __name__ == "__main__":
    main()
