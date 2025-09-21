# Conversational Customer Service Agent

## Overview
An intelligent conversational AI system that processes customer complaints through natural dialogue, extracting key information and providing empathetic customer service responses.

## Features
- 🤖 **Intelligent Conversation Flow**: Context-aware question generation (max 3 questions)
- 🧠 **Emotion Detection**: Real-time sentiment analysis of customer responses
- 🎤 **Audio Processing**: Speech-to-text and text-to-speech capabilities
- 📊 **Information Extraction**: Automatic extraction of customer data and complaint details
- 💾 **Conversation Logging**: Complete conversation history with structured output
- 🎯 **Professional Persona**: Empathetic customer service agent behavior

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Ojaswitsharma/TIC-Hackathon.git
cd TIC-Hackathon
git checkout dhairya
```

### 2. Create Virtual Environment
```bash
python -m venv myenv

# Windows
myenv\Scripts\activate

# Linux/Mac
source myenv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the project root:
```env
# Required API Keys
GOOGLE_API_KEY=your_google_gemini_api_key_here
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
```

## API Keys Setup

### Google Gemini API
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GOOGLE_API_KEY`

### AssemblyAI API
1. Sign up at [AssemblyAI](https://www.assemblyai.com/)
2. Get your API key from the dashboard
3. Add it to your `.env` file as `ASSEMBLYAI_API_KEY`

## Usage

### Text-Only Conversational Agent
```bash
python simple_conversational_agent.py
```
- Interactive text-based conversation
- Emotion detection and analysis
- Professional customer service responses
- Complete information extraction

### Full Audio-Enabled Agent
```bash
python conversational_agent.py
```
- Voice recording and transcription
- Text-to-speech responses
- LangGraph workflow implementation
- Advanced error handling

### Component Testing
```bash
python test_components.py
```
- Test individual system components
- Verify API connections
- Audio system diagnostics

## File Structure
```
TIC-Hackathon/
├── simple_conversational_agent.py    # Main text-only agent
├── conversational_agent.py           # Full audio-enabled agent
├── test_components.py                 # Testing utilities
├── requirements.txt                   # Dependencies
├── .env                              # API keys (create this)
├── .gitignore                        # Git ignore rules
├── audio_recordings/                 # Audio files
├── conversations/                    # Conversation logs
└── output/                          # Processed outputs
```

## System Requirements
- Python 3.8+
- Windows/Linux/macOS
- Microphone (for audio features)
- Internet connection (for API calls)
- 4GB+ RAM recommended

## Troubleshooting

### Audio Issues
- Ensure microphone permissions are granted
- Check microphone volume settings
- Install audio drivers if needed
- Use text-only mode if audio fails

### API Issues
- Verify API keys in `.env` file
- Check internet connection
- Ensure API quotas aren't exceeded
- Check API key permissions

### Installation Issues
- Use Python 3.8+ 
- Install Visual C++ Build Tools (Windows)
- Update pip: `pip install --upgrade pip`
- Try installing packages individually if batch fails

## Output Files
- **Conversations**: `conversations/conversation_YYYYMMDD_HHMMSS.json`
- **Audio Recordings**: `audio_recordings/complaint_YYYYMMDD_HHMMSS.wav`
- **Processed Outputs**: `output/complaint_output_YYYYMMDD_HHMMSS.json`

## License
MIT License - Feel free to use and modify for your projects.

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support
For issues and questions, please create an issue on GitHub or contact the development team.