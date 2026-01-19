import sys
import sounddevice as sd
import numpy as np
import whisper
import requests
import os
import time
from scipy.io.wavfile import write

API_URL = "http://localhost:8000/chat"
USER_ID = "vikram"
WHISPER_MODEL_SIZE = "base" 

def record_audio(duration=5, fs=44100):
    print("Listening... (Speak now!)")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  
    print("Processing...")
    return recording, fs

def run_jarvis():
    print(f"LOADING WHISPER MODEL ({WHISPER_MODEL_SIZE})")
    model = whisper.load_model(WHISPER_MODEL_SIZE)
    print("JARVIS IS ONLINE")
    
    while True:
        try:
            input("\nPress Enter to talk (or Ctrl+C to quit)...")
            

            my_recording, fs = record_audio(duration=5) 
            write("input.wav", fs, my_recording) 
            

            result = model.transcribe("input.wav")
            user_text = result["text"].strip()
            
            if not user_text:
                print("Didn't catch that.")
                continue
                
            print(f"You said: '{user_text}'")
            
            
            print("Thinking...")
            response = requests.post(API_URL, json={"text": user_text, "user_id": USER_ID})
            
            if response.status_code == 200:
                data = response.json()
                ai_reply = data.get("reply", "I am silent.")
                
                print(f"OS: {ai_reply}")
                

                safe_reply = ai_reply.replace("'", "").replace('"', "")
                os.system(f"say '{safe_reply}'")
            else:
                print("Brain Error.")

        except KeyboardInterrupt:
            print("\n Goodbye.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_jarvis()