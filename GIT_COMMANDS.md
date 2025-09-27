# Manual Git Commands to Push to GitHub

## 📋 Step-by-Step Instructions

### 1. Navigate to the directory
```bash
cd /home/os/tic-v2
```

### 2. Initialize Git (if not already done)
```bash
git init
```

### 3. Add GitHub remote
```bash
git remote add origin https://github.com/Ojaswitsharma/TIC-Hackathon.git
```

### 4. Fetch latest from remote
```bash
git fetch origin
```

### 5. Create/switch to combined branch
```bash
git checkout -B combined
```

### 6. Add all files from current directory
```bash
git add .
```

### 7. Commit with descriptive message
```bash
git commit -m "Simplified TIC Customer Service System

- Removed universal solution generator for direct company responses
- Added Amazon & Apple specialized agents  
- 6-question structured conversation flow
- Enhanced company detection from product mentions
- Comprehensive JSON conversation logging
- Robust fallback extraction when AI fails
- Ready for production deployment"
```

### 8. Force push to replace combined branch
```bash
git push -f origin combined
```

## ⚠️ Important Notes

- The `-f` flag will **overwrite everything** on the combined branch
- Make sure you want to replace all existing content
- This will push the simplified system without solution.py
- All current files will be uploaded to the combined branch

## 🎯 What Gets Pushed

### ✅ Core System Files
- `main.py` - System orchestrator
- `conversation.py` - Audio & conversation handling  
- `amazon_agent.py` - Amazon customer service
- `apple_agent.py` - Apple customer service
- `tic_audio.py` - Audio utilities

### ✅ Configuration & Documentation  
- `requirements.txt` - Dependencies
- `README_GITHUB.md` - Main documentation
- `SIMPLIFIED_ARCHITECTURE.md` - Architecture guide
- `.gitignore` - Git ignore rules

### ✅ Example Files
- `example_conversation_output.json` - Sample output
- Various documentation and guides

### ❌ Excluded (via .gitignore)
- `newenv/` - Virtual environment
- `*.wav` - Temporary audio files
- `results/*.json` - Runtime logs
- `conversations/*.json` - Saved conversations
- `.env` - Environment secrets

## 🚀 After Pushing

Your GitHub repository will contain the complete simplified customer service system ready for:
- Production deployment
- Team collaboration  
- Easy extension with new company agents
- Demonstration and presentation
