#!/usr/bin/env python3
"""
Audio-to-TIC Bridge
Captures audio input through conversational agent, converts to TIC format, and processes through main system
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from conversational_agent import start_conversation, ensure_folders_exist
    CONVERSATIONAL_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing conversational agent: {e}")
    print("Please ensure all audio dependencies are installed:")
    print("pip install assemblyai langgraph sounddevice pyaudio pyttsx3")
    CONVERSATIONAL_AVAILABLE = False

from main import TICSystem


class AudioToTICBridge:
    """Bridge between conversational agent and TIC system"""
    
    def __init__(self):
        self.input_dir = "input"
        self.output_dir = "output"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        if CONVERSATIONAL_AVAILABLE:
            ensure_folders_exist()
    
    def convert_conversational_to_tic_format(self, conversational_output: Dict[str, Any]) -> Dict[str, Any]:
        """Convert conversational agent output to TIC system format"""
        
        # Extract customer info
        customer_info = conversational_output.get("customer_info", {})
        complaint_details = conversational_output.get("complaint_details", {})
        company_info = conversational_output.get("company_info", {})
        metadata = conversational_output.get("metadata", {})
        
        # Map conversational agent fields to TIC format
        tic_format = {
            "customer_info": {
                "name": customer_info.get("name") or "Unknown",
                "phone": customer_info.get("phone") or "Not provided",
                "email": customer_info.get("email") or "Not provided",
                "address": customer_info.get("address") or "Not provided"
            },
            "complaint_details": {
                "description": complaint_details.get("description") or "Audio conversation processed",
                "category": self._map_category(complaint_details.get("category")),
                "urgency_level": complaint_details.get("urgency_level") or "medium",
                "order_id": complaint_details.get("order_id") or "",
                "product_name": complaint_details.get("product_name") or ""
            },
            "company_info": {
                "company_name": company_info.get("company_name") or "Unknown"
            },
            "source": "audio_conversation",
            "processing_metadata": {
                "conversation_timestamp": metadata.get("processing_timestamp"),
                "completion_timestamp": metadata.get("conversation_completed"),
                "total_questions": metadata.get("total_questions", 0),
                "conversion_timestamp": datetime.now().isoformat(),
                "original_format": "conversational_agent"
            }
        }
        
        # Add conversation history if available
        conversation = conversational_output.get("conversation", {})
        if conversation:
            tic_format["conversation_summary"] = {
                "total_exchanges": conversation.get("total_exchanges", 0),
                "full_history": conversation.get("full_history", [])
            }
        
        return tic_format
    
    def _map_category(self, conversational_category: Optional[str]) -> str:
        """Map conversational agent categories to TIC categories"""
        if not conversational_category:
            return "General Inquiry"
        
        category_map = {
            "billing": "Billing Dispute",
            "technical": "Technical Support", 
            "product": "Product Complaint",
            "refund": "Refund Request",
            "shipping": "Delivery Issue",
            "account": "Account Management"
        }
        
        # Try exact match first
        mapped = category_map.get(conversational_category.lower())
        if mapped:
            return mapped
        
        # Try partial match
        for key, value in category_map.items():
            if key in conversational_category.lower():
                return value
        
        return "General Inquiry"
    
    def save_to_input_directory(self, tic_data: Dict[str, Any]) -> str:
        """Save TIC-formatted data to input directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_case_{timestamp}.json"
        filepath = os.path.join(self.input_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(tic_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved TIC case to: {filepath}")
        return filepath
    
    def process_audio_to_tic(self, max_questions: int = 3) -> Optional[Dict[str, Any]]:
        """Complete workflow: Audio → Conversational Agent → TIC Format → TIC Processing"""
        
        if not CONVERSATIONAL_AVAILABLE:
            print("❌ Conversational agent not available. Please install dependencies.")
            return None
        
        print("🎤 Starting Audio-to-TIC Processing Pipeline")
        print("=" * 60)
        
        # Step 1: Capture audio and process through conversational agent
        print("1️⃣ Capturing audio through conversational agent...")
        try:
            conversational_result = start_conversation(max_questions=max_questions)
            
            if not conversational_result:
                print("❌ Failed to get result from conversational agent")
                return None
            
            print("✅ Audio conversation completed successfully")
            print(f"📋 Conversational Result Summary:")
            print(f"   Customer: {conversational_result.get('customer_info', {}).get('name', 'Unknown')}")
            print(f"   Category: {conversational_result.get('complaint_details', {}).get('category', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error in conversational agent: {e}")
            return None
        
        # Step 2: Convert to TIC format
        print("\\n2️⃣ Converting to TIC format...")
        try:
            tic_data = self.convert_conversational_to_tic_format(conversational_result)
            print("✅ Conversion to TIC format completed")
            
        except Exception as e:
            print(f"❌ Error converting to TIC format: {e}")
            return None
        
        # Step 3: Save to input directory
        print("\\n3️⃣ Saving to input directory...")
        try:
            input_file = self.save_to_input_directory(tic_data)
            
        except Exception as e:
            print(f"❌ Error saving to input directory: {e}")
            return None
        
        # Step 4: Process through TIC system
        print("\\n4️⃣ Processing through TIC system...")
        try:
            tic_system = TICSystem()
            result = tic_system.process_json_input(tic_data)
            
            print("✅ TIC processing completed")
            print(f"📊 TIC Result:")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Case ID: {result.get('case_id', 'N/A')}")
            print(f"   Priority: {result.get('priority', 'N/A')}")
            print(f"   Estimated Time: {result.get('estimated_time', 'N/A')}")
            
            return {
                "audio_conversation": conversational_result,
                "tic_input": tic_data,
                "tic_result": result,
                "input_file": input_file
            }
            
        except Exception as e:
            print(f"❌ Error in TIC processing: {e}")
            return None


def main():
    """Main execution function"""
    print("🚀 Audio-to-TIC Bridge System")
    print("=" * 60)
    print("This system will:")
    print("1. 🎤 Capture audio through conversational agent")
    print("2. 🔄 Convert to TIC-compatible format") 
    print("3. 💾 Save to input directory")
    print("4. 🧠 Process through TIC system")
    print("5. 📊 Generate complete resolution")
    print("=" * 60)
    
    if not CONVERSATIONAL_AVAILABLE:
        print("\\n❌ Error: Conversational agent dependencies not available")
        print("Please install: pip install assemblyai langgraph sounddevice pyaudio pyttsx3")
        return
    
    # Check for required API keys
    required_keys = ["ASSEMBLYAI_API_KEY", "GROQ_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"\\n❌ Missing required API keys: {', '.join(missing_keys)}")
        print("Please set these environment variables before running.")
        return
    
    try:
        # Initialize bridge
        bridge = AudioToTICBridge()
        
        # Get user preferences
        print("\\n📋 Configuration:")
        max_questions = input("Max questions for conversation (default 3): ").strip()
        max_questions = int(max_questions) if max_questions.isdigit() else 3
        
        input("\\nPress Enter to start audio capture and processing...")
        
        # Run the complete pipeline
        result = bridge.process_audio_to_tic(max_questions=max_questions)
        
        if result:
            print("\\n🎉 Complete Audio-to-TIC Processing Successful!")
            print("=" * 60)
            print(f"📁 Input file created: {result['input_file']}")
            
            # Show brief summary
            tic_result = result['tic_result']
            print(f"🆔 Case ID: {tic_result.get('case_id')}")
            print(f"🚨 Priority: {tic_result.get('priority')}")
            print(f"⏱️ Estimated Time: {tic_result.get('estimated_time')}")
            
            # Option to show full results
            show_full = input("\\nShow full results? (y/N): ").strip().lower()
            if show_full == 'y':
                print("\\n📋 Complete Results:")
                print(json.dumps(result, indent=2, default=str))
                
        else:
            print("\\n❌ Audio-to-TIC processing failed. Please check error messages above.")
            
    except KeyboardInterrupt:
        print("\\n\\n👋 Process interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
