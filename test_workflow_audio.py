#!/usr/bin/env python3
"""
Test script to demonstrate TTS functionality in workflow coordinator
"""

from workflow_coordinator import CustomerServiceWorkflowCoordinator
import json

def test_workflow_audio():
    """Test that workflow coordinator speaks the final solution"""
    
    print("🎯 Testing Workflow Audio Delivery")
    print("=" * 50)
    
    # Initialize coordinator
    coordinator = CustomerServiceWorkflowCoordinator()
    
    # Check TTS availability
    if coordinator.tts_manager and coordinator.tts_manager.enabled:
        print("✅ TTS system ready")
        print(f"🎤 Voice: {coordinator.tts_manager.voice_id}")
        print()
        
        # Create a mock result to test the audio delivery
        mock_result = {
            "success": True,
            "solution_result": {
                "solvability_assessment": {"solvable": True},
                "issue_category": "test_issue",
                "customer_data_found": True,
                "solution_response": "Dear customer, your issue has been resolved successfully. We have processed your request and applied the necessary changes to your account. Thank you for your patience."
            }
        }
        
        print("🔊 Testing audio delivery with mock solution...")
        print("💬 Mock Solution Response:")
        print("-" * 40)
        print(mock_result["solution_result"]["solution_response"])
        print("-" * 40)
        print()
        
        # Test the print workflow results method which includes TTS
        coordinator.print_workflow_results(mock_result)
        
    else:
        print("❌ TTS system not available")
        print("   Make sure MURF_API_KEY is set in .env file")

if __name__ == "__main__":
    test_workflow_audio()
