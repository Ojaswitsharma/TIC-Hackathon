import json
import os
from datetime import datetime
from dotenv import load_dotenv
import pyttsx3
import sounddevice as sd
import numpy as np
import wave
import assemblyai as aai
import google.generativeai as genai

# Load environment variables
load_dotenv()

def test_tts():
    """Test text-to-speech functionality"""
    print("Testing TTS...")
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 0.9)
    
    test_message = "Hello! This is a test of the text to speech system."
    print(f"Speaking: {test_message}")
    engine.say(test_message)
    engine.runAndWait()
    print("TTS test completed!")

def test_audio_recording():
    """Test audio recording functionality"""
    print("\nTesting audio recording...")
    print("Speak for 5 seconds...")
    
    duration = 5
    sample_rate = 44100
    
    # Record audio
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.int16
    )
    sd.wait()
    
    # Save to file
    filename = "test_recording.wav"
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    
    print(f"Recording saved to: {filename}")
    
    # Check audio stats
    max_amplitude = np.max(np.abs(audio_data))
    avg_amplitude = np.mean(np.abs(audio_data))
    print(f"Audio stats - Max: {max_amplitude}, Avg: {avg_amplitude:.2f}")
    
    return filename

def test_transcription(audio_file):
    """Test speech-to-text functionality"""
    print(f"\nTesting transcription of {audio_file}...")
    
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        print("No AssemblyAI API key found")
        return None
    
    aai.settings.api_key = api_key
    config = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.universal,
        language_code="en"
    )
    transcriber = aai.Transcriber()
    
    transcript = transcriber.transcribe(audio_file, config=config)
    
    if transcript.status == aai.TranscriptStatus.error:
        print(f"Transcription failed: {transcript.error}")
        return None
    
    text = transcript.text if transcript.text else "[No speech detected]"
    print(f"Transcription result: {text}")
    return text

def test_gemini(text):
    """Test Google Gemini API"""
    print(f"\nTesting Gemini with text: {text}")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("No Google API key found")
        return
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"Analyze this customer message and extract any complaint information: {text}"
    
    try:
        response = model.generate_content(prompt)
        print(f"Gemini response: {response.text}")
    except Exception as e:
        print(f"Gemini error: {e}")

def main():
    """Run all tests"""
    print("=== CONVERSATIONAL AGENT COMPONENT TESTS ===\n")
    
    # Test 1: TTS
    test_tts()
    
    # Test 2: Audio Recording
    audio_file = test_audio_recording()
    
    # Test 3: Transcription
    if audio_file:
        text = test_transcription(audio_file)
        
        # Test 4: Gemini
        if text and text != "[No speech detected]":
            test_gemini(text)
    
    print("\n=== ALL TESTS COMPLETED ===")

if __name__ == "__main__":
    main()