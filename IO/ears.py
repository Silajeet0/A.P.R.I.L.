import pyaudio as pa
import subprocess
import webrtcvad
import wave
import re
import openwakeword
from openwakeword.model import Model
import numpy as np

openwakeword.utils.download_models()

def wait_for_wake_word():
    """loops silently on the background until the wake word is spoken"""
    print("\n[System] Microphone is in standby. Say 'Hey Jarvis' to wake...")

    oww_model = Model(wakeword_models=["hey_jarvis"])

    aud = pa.PyAudio()
    stream = aud.open(
        rate=16000,
        channels=1,
        format=pa.paInt16,
        input=True,
        frames_per_buffer=1280
    )

    try:
        while True:
            pcm = stream.read(1280, exception_on_overflow=False)
            audio_data = np.frombuffer(pcm, dtype=np.int16)
            prediction = oww_model.predict(audio_data)

            if prediction["hey_jarvis"] > 0.5:
                print("\n[System] Wake word detected!")
                break
    finally:
        stream.stop_stream()
        stream.close()
        aud.terminate()

# directories
WHISPER_DIR = "/home/silajeet0/workspace/whisper.cpp/build/bin/whisper-cli"
MODEL_DIR = "/home/silajeet0/workspace/whisper.cpp/models/ggml-base.en.bin"

def transcribe():
    """Takes in the .wav input and processes through the whisper's c++ backend to extract the text from audio"""

    command = [
        WHISPER_DIR,
        "-m", MODEL_DIR,
        "-f", "/tmp/input.wav",
        "-nt" #nt means no timestamps so whisper outputs only the text
    ]

    print("[System] Handing audio to whisper engine...")
    try:
        process_result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        spoken_text = process_result.stdout.strip()
        clean_text = re.sub(r'\(.*?\)|\[.*?\]|\*.*?\*', '', spoken_text)
        clean_text = clean_text.strip()

        return clean_text
    
    except Exception as e:
        print(f"[System] Error: {e}")
        return None

def listen():
    """listens to the words spoken on the mic and saves it temporarily in /tmp/input.wav"""

    vad = webrtcvad.Vad(3) #use Google's WebRTC Voice Activity Detector with aggresiveness = 3 to filter out non-speech aggressively
    aud = pa.PyAudio()
    stream = aud.open(rate=16000, format=pa.paInt16, channels=1, input=True, frames_per_buffer=480) #specifics in accordance to vad

    print("[A.P.R.I.L.] Listening...")
    silence_counter = 0
    audio_frames = []
    has_spoken=False
    TRIGGER_THRESHOLD = 5
    trigger_counter = 0
    while True:
        chunk = stream.read(num_frames=480, exception_on_overflow=False)
        
        # 1. Calculate the raw volume (energy) of the audio chunk
        audio_data = np.frombuffer(chunk, dtype=np.int16)
        rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
        
        # 2. The Noise Gate: A quiet room/fan is usually 50-200. Human speech is 500-2000+.
        # Adjust this number if she still gets stuck, or if she cuts you off too early!
        VOLUME_THRESHOLD = 400 
        
        # 3. Only ask WebRTC to check for speech IF the volume is loud enough
        if rms > VOLUME_THRESHOLD:
            human = vad.is_speech(chunk, 16000)
        else:
            human = False # Force silence, ignore the fan!

        if human:
            print("!", end="", flush=True) 
            trigger_counter += 1
            if trigger_counter >= TRIGGER_THRESHOLD:
                has_spoken = True
            if has_spoken:
                audio_frames.append(chunk)
                silence_counter = 0
        else:
            print(".", end="", flush=True) 
            trigger_counter = 0
            if has_spoken:
                audio_frames.append(chunk)
                silence_counter += 1
                
        if has_spoken and silence_counter >= 25: 
            print() 
            break

    print("[System] Voice captured. Processing...")
    stream.stop_stream()
    stream.close()
    aud.terminate()

    with wave.open("/tmp/input.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(aud.get_sample_size(pa.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(audio_frames))



if __name__=="__main__":
    listen()
    spoken = transcribe()
    if spoken:
        print(F"[A.P.R.I.L.]: {spoken}")
    else:
        print("[System] Error in listening or transcribing")