"""
TIC Audio utilities for TTS playbook
Provides system audio playback functionality
"""

import os
import platform


def play_audio_from_bytes(audio_data, filename_hint="temp_audio.wav"):
    """
    Play audio from bytes data using system audio players
    
    Args:
        audio_data (bytes): Audio data in WAV format
        filename_hint (str): Filename hint for temporary file
    
    Returns:
        bool: True if playback was successful, False otherwise
    """
    print(f"🔊 Audio file size: {len(audio_data)} bytes")
    return _system_audio_playback(audio_data, filename_hint)


def _system_audio_playback(audio_data, filename_hint):
    """
    System audio playback using native audio players
    
    Args:
        audio_data (bytes): Audio data in WAV format
        filename_hint (str): Filename hint for temporary file
    
    Returns:
        bool: True if playback was attempted, False otherwise
    """
    try:
        # Create temporary file
        temp_file = filename_hint
        with open(temp_file, "wb") as f:
            f.write(audio_data)
            
        system = platform.system().lower()
        print(f"🔊 Using system audio player for {system}")
        
        if system == "linux":
            # Try multiple players
            players = ["aplay", "paplay", "pulseaudio"]
            for player in players:
                result = os.system(f"which {player} > /dev/null 2>&1")
                if result == 0:  # Player found
                    result = os.system(f"{player} {temp_file}")
                    if result == 0:
                        print(f"✅ Audio played successfully with {player}")
                        break
        elif system == "darwin":  # macOS
            result = os.system(f"afplay {temp_file}")
            if result == 0:
                print("✅ Audio played successfully with afplay")
        elif system == "windows":
            result = os.system(f"start /wait {temp_file}")
            if result == 0:
                print("✅ Audio played successfully with system player")
        else:
            print("🔊 Audio file saved for manual playback")
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except OSError:
            pass
            
        return True
        
    except Exception as e:
        print(f"⚠️ System audio playback failed: {e}")
        print(f"🔍 Debug: Audio file saved as {filename_hint} for inspection")
        return False
