"""Voer uit vanuit de projectmap: python -m tests.benchmark MODELMAP UITMAP"""
import audioop
import json
import subprocess
import sys
import time
import wave
from pathlib import Path
from tempfile import TemporaryDirectory

from engine import RATE, transcribe

scripts = json.loads(Path(__file__).with_name("scenarios.json").read_text(encoding="utf8"))
target = Path(sys.argv[2])
target.mkdir(exist_ok=True)
for number, script in enumerate(scripts,1):
    pcm = bytearray()
    bounds = []
    with TemporaryDirectory() as folder:
        sample = Path(folder) / "spraak.wav"
        for role, line in script:
            subprocess.run(["espeak","-v","nl" if role=="therapeut" else "nl+f3",
                            "-s","145","-w",str(sample),line],check=True)
            with wave.open(str(sample)) as w:
                raw,_ = audioop.ratecv(w.readframes(w.getnframes()),2,1,w.getframerate(),RATE,None)
            start = len(pcm)//2
            pcm.extend(raw)
            bounds.append((start,len(pcm)//2,role))
            pcm.extend(bytes(2*RATE))
    print("bounds",bounds)
    with wave.open(str(target / f"scenario-{number}.wav"),"wb") as w:
        w.setparams((1,2,RATE,0,"NONE",""))
        w.writeframes(pcm)
    started = time.monotonic()
    turns = transcribe(bytes(pcm),Path(sys.argv[1]))
    print(number, "audio", len(pcm)/(2*RATE), "verwerking",round(time.monotonic()-started,2))
    for t in turns:
        matches = [role for a,b,role in bounds if a <= (t.start+t.end)//2 <= b]
        print(t.id, round(t.start/RATE,2),round(t.end/RATE,2),t.speaker,matches,t.text)
