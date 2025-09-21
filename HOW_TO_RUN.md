# 🚀 TIC System - Complete Usage Guide

## Prerequisites

Make sure you're in the TIC directory and have the virtual environment activated:

```bash
cd /home/os/TIC
source ticvenv/bin/activate
```

## 🎯 Quick Start Options

### 1. **Default Mode - Process Input Directory** (Recommended for Batch Processing)
```bash
python main.py
```
- Automatically processes all JSON files in the `input/` directory
- Generates resolution reports in the `output/` directory
- Moves processed files to `input/processed/`
- **Best for**: Processing multiple customer cases at once

### 2. **Demo Mode** (Great for First-Time Users)
```bash
python main.py --demo
```
- Shows interactive demonstration of all system capabilities
- Processes sample cases (billing, technical, product issues)
- **Best for**: Understanding how the system works

### 3. **Interactive Mode** (Manual Case Entry)
```bash
python main.py --interactive
```
- Guided interface for entering customer data manually
- Step-by-step case creation
- **Best for**: Single case processing with manual input

## 📄 JSON File Processing

### Single JSON File:
```bash
python main.py --json-file path/to/customer_case.json
```

### JSON String Directly:
```bash
python main.py --json '{"customer_info": {"name": "John", "email": "john@email.com"}, "complaint_details": {"description": "Billing issue", "category": "billing"}}'
```

### Example JSON Format:
```json
{
  "customer_info": {
    "name": "Sarah Johnson",
    "email": "sarah@email.com",
    "phone": "+1-555-0123"
  },
  "complaint_details": {
    "description": "I was charged twice for my subscription",
    "category": "billing",
    "urgency_level": "high"
  },
  "company_info": {
    "company_name": "TechCorp"
  }
}
```

## 🎤 Audio Processing (Advanced)

### Live Audio Recording:
```bash
python main.py --audio
```
- Records live audio from microphone
- Converts speech to text using Whisper
- Processes through conversational AI agent

### Audio Files Processing:
```bash
python main.py --audio-file
```
- Processes audio files in current directory
- Supports multiple audio formats

## 📂 Directory Structure Setup

### Create Input Files:
```bash
# Create sample case files
mkdir -p input

# Sample billing case
cat > input/billing_case.json << EOF
{
  "customer_info": {
    "name": "Alice Smith",
    "email": "alice@email.com",
    "phone": "+1-555-1234"
  },
  "complaint_details": {
    "description": "Double charged for premium subscription",
    "category": "billing",
    "urgency_level": "high"
  }
}
EOF

# Sample technical case
cat > input/technical_case.json << EOF
{
  "customer_info": {
    "name": "Bob Wilson",
    "email": "bob@email.com",
    "phone": "+1-555-5678"
  },
  "complaint_details": {
    "description": "Cannot access my account dashboard",
    "category": "technical",
    "urgency_level": "medium"
  }
}
EOF
```

## 🎮 Complete Workflow Examples

### Example 1: Batch Processing
```bash
# 1. Add JSON files to input directory
cp your_cases/*.json input/

# 2. Run batch processing
python main.py

# 3. Check results
ls output/
ls input/processed/
```

### Example 2: Single Case Processing
```bash
# Process a specific case
python main.py --json-file input/billing_case.json

# View the result
cat output/billing_case_result.json
```

### Example 3: Quick Demo
```bash
# See the system in action
python main.py --demo
```

### Example 4: Custom Directory Processing
```bash
# Process files from custom directories
python main.py --input-dir /path/to/cases --output-dir /path/to/results
```

## 📊 Understanding Output

After processing, you'll get:

### Console Output:
- Customer information summary
- Generated resolution plan
- Case ID and priority level
- Estimated resolution time

### JSON Result Files:
```json
{
  "status": "resolved",
  "case_id": "CASE_12345",
  "priority": "High",
  "estimated_time": "1-2 hours",
  "resolution_message": "Complete resolution text...",
  "procedural_plan": {
    "steps": [...],
    "escalation_required": false
  }
}
```

## 🔧 System Capabilities

### Knowledge Base:
- ✅ 5 company documents loaded
- ✅ 223 document chunks indexed
- ✅ Smart vectorization (only rebuilds when documents change)

### Decision Engine:
- ✅ Groq LLM (llama-3.1-8b-instant)
- ✅ Intelligent case classification
- ✅ Procedural plan generation

### Execution Layer:
- ✅ Automated resolution generation
- ✅ Escalation detection
- ✅ Customer communication templates

### Audio Processing:
- ✅ Whisper speech-to-text
- ✅ LangGraph conversational AI
- ✅ Real-time audio processing

## 🚨 Troubleshooting

### Common Issues:

1. **"No such file or directory"**
   ```bash
   # Make sure you're in the right directory
   cd /home/os/TIC
   ```

2. **"Virtual environment not activated"**
   ```bash
   source ticvenv/bin/activate
   ```

3. **"No JSON files found"**
   ```bash
   # Check input directory
   ls input/
   # Create sample files as shown above
   ```

4. **Audio not working**
   - Audio features require additional setup
   - System gracefully falls back to JSON processing

## 🎯 Recommended Usage Patterns

### For Development/Testing:
```bash
python main.py --demo              # See capabilities
python main.py --interactive       # Manual testing
```

### For Production/Batch:
```bash
python main.py                     # Process input directory
python main.py --input-dir cases   # Custom directory
```

### For Single Cases:
```bash
python main.py --json-file case.json
```

---

## 🚀 Ready to Start!

**Quickest way to see it working:**
```bash
cd /home/os/TIC
source ticvenv/bin/activate
python main.py --demo
```

This will show you the full system capabilities with sample cases!
