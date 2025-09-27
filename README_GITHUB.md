# TIC Hackathon - Simplified Customer Service AI

A streamlined AI-powered customer service automation system with **direct company-specific responses**.

## 🎯 Overview

This system provides automated customer service through audio conversations, intelligent company routing, and specialized agent responses - **no universal solution layer needed**.

## 🚀 Key Features

- **🎤 Audio Conversation**: 6-question structured data collection
- **🏢 Smart Company Detection**: From product mentions (iPhone→Apple, Prime→Amazon)
- **🤖 Company-Specific Agents**: Amazon & Apple agents with specialized knowledge
- **📝 Comprehensive Logging**: Full conversation JSON with extracted data
- **🔊 Text-to-Speech**: Murf API integration for audio responses
- **🛡️ Robust Fallback**: Works even when AI analysis fails

## 📁 Architecture

```
Customer Audio → Conversation Agent → Company Detection → Company Agent → Direct Response
```

### Core Files
- **`main.py`** - System orchestrator & workflow management
- **`conversation.py`** - Audio capture, transcription & 6-question flow
- **`amazon_agent.py`** - Amazon-specific customer service agent
- **`apple_agent.py`** - Apple-specific customer service agent
- **`tic_audio.py`** - System audio playback utilities

## 🔧 Setup

### 1. Environment Setup
```bash
python -m venv newenv
source newenv/bin/activate  # Linux/Mac
# or: newenv\\Scripts\\activate  # Windows

pip install -r requirements.txt
```

### 2. Environment Variables
Create `.env` file:
```bash
GROQ_API_KEY=your_groq_api_key_here
MURF_API_KEY=your_murf_api_key_here  # Optional for TTS
```

### 3. Run System
```bash
python main.py
```

## 🎮 Usage

1. **Start the system**: `python main.py`
2. **Answer 6 questions** about your issue
3. **System detects company** from your responses
4. **Routes to appropriate agent** (Amazon/Apple)
5. **Receive direct response** from specialized agent

### Example Conversation Flow
```
🤖 "Tell me your name and describe your issue"
👤 "I'm John, my iPhone keeps crashing"

🤖 "Please provide phone/email for follow-up"  
👤 "555-0123, john@email.com"

🤖 "More details about the problem?"
👤 "Apps crash immediately when opened"

🤖 "Product name/model?"
👤 "iPhone 14 Pro Max"

🤖 "When did you purchase/when did issue start?"
👤 "Bought last month, started yesterday"

🤖 "Anything else to help resolve this?"
👤 "Need it fixed ASAP for work"

→ System detects "Apple" from "iPhone"
→ Routes to Apple Agent
→ Apple Agent provides specialized response
```

## 🏪 Company Agents

### Amazon Agent
- **Products**: Amazon orders, Prime, AWS
- **Handles**: Shipping, refunds, account issues
- **Features**: Order tracking, customer verification

### Apple Agent  
- **Products**: iPhone, MacBook, iPad, iOS
- **Handles**: Hardware repair, software issues, warranty
- **Features**: Device diagnostics, Genius Bar scheduling

## 📊 Data Collection

The system collects comprehensive customer data:

```json
{
  "customer_name": "John",
  "company_name": "Apple", 
  "product_name": "iPhone 14 Pro Max",
  "problem_category": "software_issue",
  "urgency_level": "high",
  "customer_phone": "555-0123",
  "customer_email": "john@email.com"
}
```

## 🎯 Company Detection

Enhanced detection from product mentions:
- **Apple**: iPhone, MacBook, iPad, Mac, iOS
- **Amazon**: Amazon, Prime, AWS  
- **Microsoft**: Windows, Xbox, Office
- **Samsung**: Galaxy, Samsung
- **And more...**

## 🔄 Workflow Benefits

### ✅ Simplified Architecture
- **Before**: Conversation → Company Agent → Universal Solution → Response
- **After**: Conversation → Company Agent → **Direct Response**

### ✅ Company Expertise
- Each agent specializes in their company's products/services
- No generic responses - all company-specific
- Direct access to company policies and procedures

### ✅ Easy Extension
```python
# Add new company agent:
from facebook_agent import FacebookAgent
self.facebook_agent = FacebookAgent()

# Add routing:
elif "facebook" in detected_company:
    agent_result = self.facebook_agent.process_customer_issue(conversation_data)
```

## 🛠️ Technical Stack

- **Speech-to-Text**: OpenAI Whisper (local)
- **AI Analysis**: Groq LLM (llama-3.1-8b-instant)
- **Text-to-Speech**: Murf API
- **Audio**: sounddevice + system audio players
- **Language**: Python 3.13

## 📝 Dependencies

```
groq>=0.4.0
openai-whisper>=20231117
sounddevice>=0.4.6  
numpy>=1.24.0
requests>=2.31.0
python-dotenv>=1.0.0
```

## 🚀 Future Extensions

- **Facebook/Meta Agent**: Instagram, WhatsApp support
- **Google Agent**: Android, Pixel, Gmail support  
- **Microsoft Agent**: Windows, Office support
- **Multi-language Support**: Conversation in different languages
- **Advanced Analytics**: Customer satisfaction tracking

## 📄 License

MIT License - Feel free to modify and extend!

## 🤝 Contributing

1. Fork the repository
2. Create company-specific agents in `{company}_agent.py`
3. Add routing logic in `main.py`
4. Test end-to-end workflow
5. Submit pull request

---

**Built for TIC Hackathon** - Streamlined AI Customer Service 🎯
