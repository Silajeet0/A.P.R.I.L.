from kokoro import KPipeline
import sounddevice as sd

print("[System] : Loading vocal matrix Kokoro TTS")
pipeline = KPipeline(lang_code="a")
print("[System] : Vocal matrix loaded")

def talk(to_speak:str, start_event=None):
    generator = pipeline(
        text=to_speak,
        voice="af_heart",
        speed=1.1,
        split_pattern=r"\n+" #this tells Kokoro to process sentences one at a time
    )

    for i, (_,_,audio_array) in enumerate(generator):
        if i== 0 and start_event:
            start_event.set()
        sd.play(audio_array, samplerate=24000)
        sd.wait()

if __name__=="__main__":
    talk("Hello")
