#!/usr/bin/env python3
"""
Audio Setup and Demo Script
Shows you exactly how to run audio input with the TIC system
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking Dependencies...")
    
    required_packages = [
        'assemblyai', 'langgraph', 'sounddevice', 'pyaudio', 'pyttsx3'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing.append(package)
    
    return missing

def check_api_keys():
    """Check if required API keys are set"""
    print("\\n🔑 Checking API Keys...")
    
    required_keys = {
        'ASSEMBLYAI_API_KEY': 'AssemblyAI (for speech-to-text)',
        'GROQ_API_KEY': 'Groq (for conversation intelligence and TIC processing)'
    }
    
    missing = []
    for key, description in required_keys.items():
        if os.getenv(key):
            print(f"   ✅ {key} ({description})")
        else:
            print(f"   ❌ {key} ({description})")
            missing.append(key)
    
    return missing

def install_dependencies(packages):
    """Install missing packages"""
    if not packages:
        return True
    
    print(f"\\n📦 Installing missing packages: {', '.join(packages)}")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install'
        ] + packages, check=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def show_api_key_setup(missing_keys):
    """Show how to set up missing API keys"""
    if not missing_keys:
        return
    
    print("\\n🔧 API Key Setup Instructions:")
    print("=" * 50)
    
    for key in missing_keys:
        if key == 'ASSEMBLYAI_API_KEY':
            print("1. AssemblyAI API Key:")
            print("   - Go to https://www.assemblyai.com/")
            print("   - Sign up for free account")
            print("   - Get API key from dashboard")
            print(f"   - Run: export {key}='your_assemblyai_key'")
            
        elif key == 'GROQ_API_KEY':
            print("\\n2. Groq API Key:")
            print("   - Get your API key from https://console.groq.com/")
            print(f"   - Run: export {key}='your_groq_api_key_here'")

def run_audio_demo():
    """Run the audio input demo"""
    print("\\n🎤 Running Audio Input Demo...")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, 'simple_audio_pipeline.py'
        ], cwd=os.getcwd())
        
        if result.returncode == 0:
            print("\\n✅ Audio demo completed successfully!")
        else:
            print("\\n❌ Audio demo encountered issues")
            
    except KeyboardInterrupt:
        print("\\n👋 Demo cancelled by user")
    except Exception as e:
        print(f"\\n❌ Error running demo: {e}")

def main():
    """Main setup and demo function"""
    print("🎤 TIC Audio Input Setup & Demo")
    print("=" * 60)
    print("This script will help you set up and test audio input for the TIC system.")
    print("=" * 60)
    
    # Check current directory
    if not os.path.exists('main.py'):
        print("❌ Please run this script from the TIC directory")
        print("   cd /home/os/TIC")
        return
    
    # Check dependencies
    missing_deps = check_dependencies()
    
    # Check API keys  
    missing_keys = check_api_keys()
    
    # Summary
    print("\\n📊 Setup Status:")
    if not missing_deps and not missing_keys:
        print("   ✅ All dependencies installed")
        print("   ✅ All API keys configured")
        print("   🚀 Ready for audio input!")
        
        choice = input("\\nWould you like to run the audio demo? (y/N): ").strip().lower()
        if choice == 'y':
            run_audio_demo()
        else:
            print("\\n💡 To run audio input manually:")
            print("   python simple_audio_pipeline.py")
    
    else:
        print("   ⚠️  Setup incomplete")
        
        if missing_deps:
            print(f"   📦 Missing packages: {', '.join(missing_deps)}")
            install_choice = input("\\nInstall missing packages now? (y/N): ").strip().lower()
            if install_choice == 'y':
                if install_dependencies(missing_deps):
                    print("✅ Dependencies installed!")
                else:
                    print("❌ Installation failed. Please install manually:")
                    print(f"   pip install {' '.join(missing_deps)}")
        
        if missing_keys:
            show_api_key_setup(missing_keys)
            
        print("\\n🔄 After setup, run this script again to test audio input")

if __name__ == "__main__":
    main()
