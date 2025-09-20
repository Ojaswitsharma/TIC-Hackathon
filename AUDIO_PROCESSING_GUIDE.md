# 🎤 Audio-to-TIC Processing Guide

## Overview

This guide shows you how to capture audio input through the conversational agent, convert it to TIC format, and process it through the main TIC system.

## 🔧 Prerequisites

### 1. Install Audio Dependencies
```bash
cd /home/os/TIC
source ticvenv/bin/activate
pip install assemblyai langgraph sounddevice pyaudio pyttsx3
```

### 2. Set Required API Keys
You need these environment variables:
```bash
export ASSEMBLYAI_API_KEY="your_assemblyai_key"
export GROQ_API_KEY="your_groq_api_key_here"
```

## 🚀 Usage Options

### Option 1: Simple Audio Pipeline (Recommended)
```bash
cd /home/os/TIC
source ticvenv/bin/activate
python simple_audio_pipeline.py
```

**What it does:**
1. 🎤 Captures audio through conversational agent
2. 🔄 Converts output to TIC-compatible JSON format
3. 💾 Saves to `input/audio_case_TIMESTAMP.json`
4. 🧠 Automatically runs `main.py` to process the case
5. 📊 Shows complete results

### Option 2: Advanced Audio-to-TIC Bridge
```bash
python audio_to_tic_bridge.py
```

**What it does:**
- More detailed processing and error handling
- Step-by-step progress reporting
- Option to show full detailed results
- Better integration with TIC system

### Option 3: Manual Step-by-Step
```bash
# Step 1: Capture audio conversation
python conversational_agent.py

# Step 2: Check the saved conversation
ls conversations/

# Step 3: Convert and save to input/ (manual process)
# ... (requires manual conversion)

# Step 4: Run TIC system
python main.py
```

## 📋 Expected Workflow

### 1. Audio Capture Phase
```
🎤 INTELLIGENT CUSTOMER SERVICE AGENT
🗣️  Two-way Conversational Complaint Processing
====================================================

Instructions:
• The agent will ask up to 3 intelligent questions
• Speak clearly after each question  
• Recording stops automatically after 2 seconds of silence
• Press Ctrl+C anytime to exit

Press Enter to start the conversation...
```

### 2. Conversation Example
```
🤖 Agent: Hello! I'm here to help you with your complaint. Can you please tell me your name?
🎤 [Recording...] [Customer speaks]
👤 Customer: My name is John Smith

🤖 Agent: Thank you John. What seems to be the issue you're experiencing?
🎤 [Recording...] [Customer speaks]  
👤 Customer: I was charged twice for my subscription

🤖 Agent: I understand that's frustrating. Can you provide your email address so I can look into this?
🎤 [Recording...] [Customer speaks]
👤 Customer: It's john.smith@email.com
```

### 3. Conversion to TIC Format
```json
{
  "customer_info": {
    "name": "John Smith",
    "email": "john.smith@email.com",
    "phone": "Not provided"
  },
  "complaint_details": {
    "description": "I was charged twice for my subscription",
    "category": "billing",
    "urgency_level": "medium"
  },
  "source": "audio_conversation",
  "timestamp": "2025-09-21T03:15:30.123456"
}
```

### 4. TIC Processing
```
🚀 Initializing TIC System...
📚 Loading Knowledge Base... ✅ 223 chunks loaded
🧠 Initializing Decision Engine... ✅ Groq LLM ready
⚡ Setting up Execution Layer... ✅ Conversational AI ready

🎯 Processing Customer Data
👤 Customer: John Smith
📧 Email: john.smith@email.com
📋 Issue: I was charged twice for my subscription
🏷️ Category: billing

📋 Generated Plan: Billing_Dispute Resolution
🚨 Priority: High
⏱️ Estimated Time: 1-2 hours
Case ID: CASE_12345
```

## 📁 File Structure

After running the audio pipeline:

```
TIC/
├── input/
│   ├── audio_case_20250921_031530.json  # ← Generated TIC input
│   └── processed/
│       └── audio_case_20250921_031530.json  # ← Moved after processing
├── output/
│   └── audio_case_20250921_031530_result.json  # ← TIC resolution
├── conversations/
│   └── conversation_20250921_031530.json  # ← Original conversation
└── audio_recordings/
    └── audio_20250921_031530.wav  # ← Original audio file
```

## 🔧 Troubleshooting

### Common Issues:

1. **"Conversational agent not available"**
   ```bash
   pip install assemblyai langgraph sounddevice pyaudio pyttsx3
   ```

2. **"Missing API keys"**
   ```bash
   export ASSEMBLYAI_API_KEY="your_key"
   export GROQ_API_KEY="your_groq_api_key_here"
   ```

3. **Audio recording issues**
   - Check microphone permissions
   - Ensure microphone is connected and working
   - Speak clearly and wait for recording to stop

4. **No audio detected**
   - Check microphone levels
   - Try speaking louder
   - Ensure 2 seconds of silence to stop recording

## 🎯 Quick Start

**Fastest way to test audio input:**

```bash
cd /home/os/TIC
source ticvenv/bin/activate

# Set API keys (if not already set)
export ASSEMBLYAI_API_KEY="your_assemblyai_key"
export GROQ_API_KEY="your_groq_api_key_here"

# Run the simple pipeline
python simple_audio_pipeline.py
```

This will guide you through the complete audio-to-resolution workflow!

## 📊 Expected Output

After successful processing, you'll see:
- ✅ Audio conversation captured
- ✅ TIC format conversion completed  
- ✅ Case saved to input folder
- ✅ TIC system processing completed
- 📊 Resolution plan generated
- 🆔 Case ID assigned
- 📁 Results saved to output folder

The system provides a complete end-to-end workflow from spoken complaint to structured resolution plan!
