import sys
import os
import time
import threading
import warnings
import re

warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from IO.ears import listen, transcribe, wait_for_wake_word
from core.brain import think
from core import brain
from IO.mouth import talk

def type_text(text:str, typing_speed=0.03):
    sys.stdout.write("[A.P.R.I.L.] : ")
    sys.stdout.flush()

    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(typing_speed)
    
    print()

print("[System] : Initiating orchestrator and A.P.R.I.L.'s core.")
time.sleep(0.3)
print("[System] : A.P.R.I.L. is ready. Press Ctrl+C to exit.")

try:
    while True:
        wait_for_wake_word()
        while True:
            listen()
            spoken = transcribe()
            print(f"[User] : {spoken}")
            if spoken:
                clean_spoken = spoken.lower().strip(".!? ")
                shutdown_commands = [
                    "bye", "by april", "goodbye", "good by", "buy april", 
                    "exit", "sleep", "stop listening", "that is all", "shut down"
                ]
                
                if any(word in clean_spoken for word in shutdown_commands):
                    print("\n[System] : Exit command detected. Going to sleep.")
                    
                    audio_started_event = threading.Event()
                    speech_thread = threading.Thread(target=talk, args=("Going to standby.", audio_started_event))
                    speech_thread.start()
                    audio_started_event.wait()
                    speech_thread.join()

                    break
                if "clear memory" in clean_spoken or "reset mind" in clean_spoken:
                    print("\n[System] Wiping A.P.R.I.L.'s short-term memory array...")
                    brain.persistent_mem = [brain.persistent_mem[0]] # Keep ONLY the system prompt
                    audio_started_event = threading.Event()
                    speech_thread = threading.Thread(target=talk, args=("Memory cleared. What can I look up for you from scratch ?", audio_started_event))
                    speech_thread.start()
                    audio_started_event.wait()
                    speech_thread.join()
                    continue
                print("[A.P.R.I.L.] : Thinking...\n")
                
                raw_answer = think(spoken)
                
                # THE FAILSAFE: Deletes anything that looks like <tag>{data}</tag>
                clean_answer = re.sub(r'<[^>]+>.*?</[^>]+>', '', raw_answer, flags=re.DOTALL)
                clean_answer = clean_answer.strip()

                # If the LLM hallucinated ONLY a tag, prevent an empty string from breaking the TTS
                if not clean_answer:
                    clean_answer = "I'm sorry, my core logic encountered an error."

                audio_started_event = threading.Event()
                speech_thread = threading.Thread(target=talk, args=(clean_answer, audio_started_event))
                speech_thread.start()
                
                audio_started_event.wait() 
                type_text(clean_answer)
                speech_thread.join()
            
except KeyboardInterrupt as err:
    print("[System] : Command received exiting A.P.R.I.L. Bye!")
except Exception as e:
    print(f"Error occured: {e}")