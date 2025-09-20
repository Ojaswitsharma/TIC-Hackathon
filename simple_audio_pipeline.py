#!/usr/bin/env python3
"""
Simple Audio Input Pipeline
1. Captures audio via conversational agent
2. Saves output to input/ folder  
3. Runs main.py to process the case
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from conversational_agent import start_conversation, ensure_folders_exist
    CONVERSATIONAL_AVAILABLE = True
except ImportError:
    print("❌ Conversational agent not available. Please install dependencies:")
    print("pip install assemblyai langgraph sounddevice pyaudio pyttsx3")
    CONVERSATIONAL_AVAILABLE = False


def convert_to_tic_format(conversational_output):
    """Convert conversational agent output to TIC input format"""
    
    customer_info = conversational_output.get("customer_info", {})
    complaint_details = conversational_output.get("complaint_details", {})
    company_info = conversational_output.get("company_info", {})
    
    # Create TIC-compatible JSON
    tic_input = {
        "customer_info": {
            "name": customer_info.get("name") or "Unknown",
            "email": customer_info.get("email") or "Not provided", 
            "phone": customer_info.get("phone") or "Not provided"
        },
        "complaint_details": {
            "description": complaint_details.get("description") or "Audio conversation - details captured",
            "category": complaint_details.get("category") or "general",
            "urgency_level": complaint_details.get("urgency_level") or "medium",
            "order_id": complaint_details.get("order_id") or "",
            "product_name": complaint_details.get("product_name") or ""
        },
        "company_info": {
            "company_name": company_info.get("company_name") or "Unknown"
        },
        "source": "audio_conversation",
        "timestamp": datetime.now().isoformat()
    }
    
    return tic_input


def save_to_input_folder(data):
    """Save data to input folder with timestamp"""
    
    # Ensure input directory exists
    os.makedirs("input", exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"input/audio_case_{timestamp}.json"
    
    # Save JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved case to: {filename}")
    return filename


def run_main_tic_system():
    """Run the main TIC system to process input folder"""
    
    print("\\n🧠 Running TIC system to process the case...")
    print("=" * 50)
    
    try:
        # Run main.py in the same environment
        result = subprocess.run([
            sys.executable, "main.py"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ TIC processing completed successfully!")
            print("\\n📊 TIC Output:")
            print(result.stdout)
        else:
            print("❌ TIC processing failed:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error running main TIC system: {e}")


def main():
    """Main pipeline function"""
    
    print("🎤 Audio Input Pipeline for TIC System")
    print("=" * 60)
    print("Step 1: Capture audio conversation")
    print("Step 2: Convert to TIC format") 
    print("Step 3: Save to input/ folder")
    print("Step 4: Run main TIC system")
    print("=" * 60)
    
    if not CONVERSATIONAL_AVAILABLE:
        print("\\n❌ Cannot proceed without conversational agent")
        return
    
    # Check API keys
    required_keys = ["ASSEMBLYAI_API_KEY", "GROQ_API_KEY"]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        print(f"\\n❌ Missing API keys: {', '.join(missing)}")
        return
    
    try:
        # Step 1: Capture audio conversation
        print("\\n🎤 Step 1: Starting audio capture...")
        input("Press Enter to begin conversation (Ctrl+C to cancel)...")
        
        ensure_folders_exist()
        conversation_result = start_conversation(max_questions=3)
        
        if not conversation_result:
            print("❌ Failed to capture conversation")
            return
        
        print("✅ Audio conversation captured successfully!")
        
        # Step 2: Convert to TIC format
        print("\\n🔄 Step 2: Converting to TIC format...")
        tic_data = convert_to_tic_format(conversation_result)
        
        # Show what was captured
        customer_name = tic_data["customer_info"]["name"]
        description = tic_data["complaint_details"]["description"]
        category = tic_data["complaint_details"]["category"]
        
        print(f"   Customer: {customer_name}")
        print(f"   Issue: {description[:50]}...")
        print(f"   Category: {category}")
        
        # Step 3: Save to input folder
        print("\\n💾 Step 3: Saving to input folder...")
        input_file = save_to_input_folder(tic_data)
        
        # Step 4: Run main TIC system
        print("\\n🧠 Step 4: Processing through TIC system...")
        run_main_tic_system()
        
        print("\\n🎉 Complete pipeline finished!")
        print(f"📁 Check output/ folder for results")
        print(f"📁 Original input saved as: {input_file}")
        
    except KeyboardInterrupt:
        print("\\n\\n👋 Pipeline cancelled by user")
    except Exception as e:
        print(f"\\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
