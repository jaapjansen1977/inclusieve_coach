"""Echte modellen, echte desktopwidgets, gesimuleerde consulten. Geen hardwaretest."""
import json
import sys
import tempfile
import time
import tkinter as tk
from pathlib import Path
from unittest.mock import patch
import soundfile as sf
from coach import Coach
from engine import RATE, RUBRIC, evidence, references

def run(models, folder):
    scripts = json.loads((folder/"scenarios.json").read_text(encoding="utf8"))
    metrics = []
    root = tk.Tk()
    app = Coach(root)
    app.model = models
    with tempfile.TemporaryDirectory() as tmp:
        for n, script in enumerate(scripts,1):
            pcm,rate = sf.read(folder/f"audio/scenario-{n}.flac",dtype="int16")
            assert rate == RATE
            path = Path(tmp)/"test.wav"
            sf.write(path,pcm,rate)
            with patch("coach.filedialog.askopenfilename",return_value=str(path)):
                app.load()
            while app.busy:
                root.update()
                time.sleep(.02)
            metrics.append(app.stats)
            # Grenzen van de afzonderlijk gesynthetiseerde zinnen, inclusief slotstilte.
            bounds = json.loads((folder/"bounds.json").read_text())[n-1]
            if n == 1:
                assert len(app.turns) == len(script)
                mapping = {t.speaker:role for t,(role,_) in zip(app.turns,script)}
                assert set(mapping) == {"A","B"} and len(set(mapping.values())) == 2
                assert all(mapping[t.speaker] == role for t,(role,_) in zip(app.turns,script))
            for t in app.turns:
                hits = [i for i,(a,b,_) in enumerate(bounds) if a <= (t.start+t.end)//2 <= b]
                assert len(hits)==1
                idx = hits[0]
                role,line = script[idx]
                assert 0 <= t.start < t.end <= len(pcm)
                # Herstel fictieve referentietekst wanneer er één herkende beurt per zin is.
                app.assign(t,role)
                if n==1:
                    with patch("coach.simpledialog.askstring",return_value=line):
                        app.edit(t)
            app.feedback()
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            widgets = list(descendants(app.body))
            buttons = [w for w in widgets if w.winfo_class()=="TButton" and w.cget("text").startswith("▶")]
            unknowns = [w for w in widgets if w.winfo_class()=="TLabel" and w.cget("text")=="Niet te beoordelen uit dit gesprek"]
            assert len(unknowns) == (0 if n==1 else 3)
            assert len(buttons) == (6 if n==1 else 0)
            expected = [[1,2],[2,3],[2,5]] if n==1 else [[],[],[]]
            for rule,ids in zip(RUBRIC["criteria"],expected):
                assert evidence(app.turns,rule,RUBRIC)==ids
                for t in references(app.turns,ids) if ids else []:
                    assert (t.speaker,t.text)==tuple(script[t.id-1])
                    with patch("coach.sd.play") as output:
                        button = buttons.pop(0)
                        assert f"{t.speaker} · beurt {t.id} · {t.start/RATE:.2f}–{t.end/RATE:.2f}" in button.cget("text")
                        assert any(w.winfo_class()=="TLabel" and w.cget("text")==f"“{t.text}”" for w in button.master.winfo_children())
                        button.invoke()
                        samples, hz = output.call_args.args
                        assert hz==rate and (samples==pcm[t.start:t.end]).all()
            app.reset()
            assert not app.turns and not app.pcm
    root.destroy()
    return metrics


if __name__ == "__main__":
    print(run(Path(sys.argv[1]),Path(__file__).parent))
