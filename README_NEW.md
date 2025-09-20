# TIC System - Three-Intelligence Confluence

An AI-powered customer service system that combines document knowledge, intelligent decision-making, and conversational AI execution.

## 🚀 Quick Start

### Method 1: Direct Python (Recommended)
```bash
cd /home/os/TIC
source ticvenv/bin/activate
python main.py
```

### Method 2: Using Launcher Script
```bash
cd /home/os/TIC
./run_tic.sh
```

## 🎯 Usage Options

### Interactive Mode (Default)
Start a full customer service session:
```bash
python main.py
```

### Demo Mode
See the system in action with pre-configured scenarios:
```bash
python main.py --demo
```

### Specific Case Processing
Generate plans for specific case types:
```bash
python main.py --case billing     # Billing dispute
python main.py --case technical   # Technical support
python main.py --case refund      # Refund request
```

## 🏗️ System Components

### 📚 Step 1: Knowledge Base (`knowledge_base.py`)
- Loads and processes company documents
- Creates vector embeddings for semantic search
- Provides context-aware document retrieval

### 🧠 Step 2: Decision Engine (`decision_engine.py`)
- Analyzes case fingerprints
- Generates procedural plans using Google Gemini Flash 1.5
- Applies business rules and escalation logic

### ⚡ Step 3: Execution Layer (`execution_layer.py`)
- Executes procedural plans conversationally
- Uses LangChain agents with custom tools
- Handles escalation and conversation management

## 📁 Directory Structure

```
TIC/
├── main.py                 # Main entry point
├── run_tic.sh             # Launcher script
├── knowledge_base.py      # Document processing
├── decision_engine.py     # Plan generation
├── execution_layer.py     # Conversation execution
├── .env                   # API keys
├── config.py              # System configuration
├── requirements.txt       # Dependencies
├── documents/             # Company documents
├── company_kb_index/      # Vector database
└── ticvenv/              # Python environment
```

## 🔧 Configuration

### API Keys
The system uses Google Gemini Flash 1.5. Your API key is stored in `.env`:
```
GOOGLE_API_KEY=your_api_key_here
```

### Documents
Add company documents to the `documents/` folder:
- Supported formats: PDF, TXT, Markdown
- Documents are automatically indexed on startup

## 🎭 Example Session

```
🚀 Initializing TIC System...
📚 Loading Knowledge Base...
   ✅ 4 documents, 16 chunks loaded
🧠 Initializing Decision Engine...
   ✅ Google Gemini Flash 1.5 ready
⚡ Setting up Execution Layer...
   ✅ Conversational AI ready

💬 Interactive Customer Service Session
Select case type (1-4): 1
Select urgency (1-4): 3
Customer anger level (1-4): 2
Account type (1-3): 2

📋 Generated Plan: Billing Dispute Resolution Plan
🚨 Priority: High
⏱️ Estimated Time: 2-4 hours
🔢 Total Steps: 6

👤 Customer: I was charged but cancelled my subscription
🤖 Agent: I understand your concern about the charge...
```

## 🛠️ System Requirements

- Python 3.8+
- Internet connection (for Google Gemini API)
- ~2GB RAM for vector operations
- Linux/macOS/Windows

## 📊 Features

✅ **Document Processing**: Automatic indexing of company policies  
✅ **Intelligent Planning**: Context-aware procedural plan generation  
✅ **Conversational AI**: Natural language customer interactions  
✅ **Smart Escalation**: Automatic handoff to human agents when needed  
✅ **Multi-Case Support**: Billing, Technical, Refund, and General inquiries  
✅ **Real-time Tools**: Account verification and system integration  
✅ **Comprehensive Logging**: Full conversation and decision tracking  

## 🆘 Troubleshooting

### Common Issues

**"No documents loaded"**: Ensure documents are in `documents/` folder
**"Vector store not available"**: Run system once to create initial index
**"API key error"**: Check your Google API key in `.env` file
**"Module not found"**: Activate virtual environment first

### Getting Help

1. Check system status: Components load without errors
2. Verify documents: Files exist in `documents/` folder
3. Test API: Google Gemini API key is valid and has credits
4. Check logs: Review console output for specific error messages

## 📝 Version History

- **v1.0**: Initial release with full TIC system
  - Knowledge Base with FAISS vector storage
  - Decision Engine with Google Gemini integration
  - Execution Layer with LangChain agents
