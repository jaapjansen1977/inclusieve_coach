import audioop
import gc
import io
import os
import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import sounddevice as sd
import soundfile as sf
import numpy as np
from engine import RATE, RUBRIC, UNKNOWN, evidence, references, transcribe

LOCAL = Path(os.getenv("LOCALAPPDATA", Path.home())) / "InclusieveCoach"


class Coach:
    def __init__(self, root):
        self.root = root
        root.title("Inclusieve coach · Gespreksreflectie")
        root.geometry("920x690")
        self.model = LOCAL / "modellen"
        self.stream = None
        self.recording = False
        self.busy = False
        self.result = queue.Queue()
        self.body = ttk.Frame(root, padding=18)
        self.body.pack(fill="both", expand=True)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.reset()

    def page(self, title):
        for widget in self.body.winfo_children():
            widget.destroy()
        ttk.Label(self.body, text=title, font=("Segoe UI", 18)).pack(anchor="w", pady=8)

    def button(self, label, command, parent=None):
        b = ttk.Button(parent or self.body, text=label, command=command)
        b.pack(anchor="w", pady=3)
        return b

    def reset(self):
        self.stop_stream()
        sd.stop()
        self.buffer = io.BytesIO()
        self.pcm = b""
        self.turns = []
        gc.collect()
        self.page("Nieuwe oefensessie")
        ttk.Label(self.body, text="Nederlandstalig simulatiegesprek · twee deelnemers").pack(anchor="w")
        self.button("Kies lokale modelmap", self.choose_models)
        self.button("Microfoon instellen", self.setup)
        self.button("WAV importeren", self.load)

    def choose_models(self):
        path = filedialog.askdirectory(title="Map met de twee uitgepakte Vosk-modelmappen")
        if path:
            self.model = Path(path)

    def ready(self):
        ok = all((self.model / name).is_dir() for name in
                 ("vosk-model-small-nl-0.22", "vosk-model-spk-0.4"))
        if not ok:
            messagebox.showwarning("Modellen ontbreken", "Kies de map met beide uitgepakte modellen.")
        return ok

    def load(self):
        if not self.ready():
            return
        path = filedialog.askopenfilename(filetypes=[("WAV", "*.wav")])
        if not path:
            return
        try:
            with sf.SoundFile(path) as source:
                state = None
                out = io.BytesIO()
                for block in source.blocks(blocksize=65536, dtype="float32", always_2d=True):
                    mono = (np.clip(block.mean(axis=1), -1, 1)*32767).astype("<i2").tobytes()
                    data, state = audioop.ratecv(mono, 2, 1, source.samplerate, RATE, state)
                    out.write(data)
                self.pcm = out.getvalue()
        except Exception:
            messagebox.showerror("Import", "Dit audiobestand kon niet worden gelezen.")
            return
        self.analyze()

    def setup(self):
        if not self.ready():
            return
        try:
            self.devices = [(i,d) for i,d in enumerate(sd.query_devices()) if d["max_input_channels"]]
        except sd.PortAudioError:
            self.devices = []
        if not self.devices:
            messagebox.showwarning("Microfoon", "Geen audio-ingang gevonden.")
            return
        self.page("Controleer de microfoon")
        self.device = ttk.Combobox(self.body, state="readonly", width=70,
                                   values=[f"{i} · {d['name']}" for i,d in self.devices])
        self.device.pack(anchor="w")
        self.device.current(0)
        self.device.bind("<<ComboboxSelected>>", lambda _: self.monitor())
        self.meter = ttk.Progressbar(self.body, maximum=100, length=400)
        self.meter.pack(anchor="w", pady=10)
        self.toggle = self.button("Opname starten", self.toggle_record)
        self.finish = self.button("Gesprek beëindigen", self.finish_record)
        self.finish.configure(state="disabled")
        self.button("Sessie verwijderen", self.reset)
        self.monitor()

    def monitor(self):
        self.stop_stream()
        self.level = 0
        self.loss = False
        i, device = self.devices[self.device.current()]
        self.rate = int(device["default_samplerate"])
        def callback(data, frames, timing, status):
            raw = bytes(data)
            self.level = min(100, audioop.rms(raw, 2)/100)
            if self.recording:
                self.loss |= bool(status.input_overflow)
                self.buffer.write(raw)
        try:
            self.stream = sd.RawInputStream(device=i, samplerate=self.rate, channels=1,
                                            dtype="int16", callback=callback)
            self.stream.start()
            self.toggle.configure(state="normal")
            self.tick(self.stream)
        except sd.PortAudioError:
            self.stop_stream()
            self.toggle.configure(state="disabled")
            messagebox.showerror("Microfoon", "Kies een andere ingang of controleer de microfoontoegang.")

    def tick(self, stream):
        if stream is self.stream:
            self.meter["value"] = self.level
            self.root.after(100, lambda: self.tick(stream))

    def toggle_record(self):
        self.recording = not self.recording
        self.device.configure(state="disabled")
        self.toggle.configure(text="Pauzeren" if self.recording else "Hervatten")
        self.finish.configure(state="normal")

    def stop_stream(self):
        self.recording = False
        if self.stream is not None:
            self.stream.close()
            self.stream = None

    def finish_record(self):
        self.stop_stream()
        if self.loss:
            messagebox.showwarning("Opname", "De audio-ingang meldde verlies van samples. Controleer de fragmenten.")
        self.pcm, _ = audioop.ratecv(self.buffer.getvalue(), 2, 1, self.rate, RATE, None)
        self.buffer = io.BytesIO()
        self.analyze()

    def analyze(self):
        self.page("Gesprek wordt lokaal verwerkt…")
        self.busy = True
        started = time.monotonic()
        def worker():
            try:
                value = transcribe(self.pcm, self.model)
            except Exception:
                value = None
            self.result.put(value)
        threading.Thread(target=worker, daemon=True).start()
        def poll():
            try:
                result = self.result.get_nowait()
            except queue.Empty:
                self.root.after(150, poll)
                return
            self.busy = False
            if not result:
                messagebox.showwarning("Transcript", "Geen transcript beschikbaar. Controleer audio en modelmappen.")
                self.reset()
                return
            self.turns = result
            self.stats = f"Audio {len(self.pcm)/(2*RATE):.1f} s · Verwerking {time.monotonic()-started:.1f} s"
            self.review()
        poll()

    def play(self, turn):
        try:
            sd.play(np.frombuffer(self.pcm, dtype="<i2")[turn.start:turn.end], RATE)
        except sd.PortAudioError:
            messagebox.showwarning("Afspelen", "Controleer het uitvoerapparaat.")

    def review(self):
        self.page("Controleer transcript en rollen")
        ttk.Label(self.body, text=self.stats + " · Selecteer een beurt om te luisteren of corrigeren.").pack(anchor="w")
        self.table = ttk.Treeview(self.body, columns=("time","role","text"), show="headings", height=12)
        for col, label, width in zip(("time","role","text"), ("Tijd (s)","Spreker","Transcript"), (95,90,620)):
            self.table.heading(col, text=label)
            self.table.column(col, width=width)
        self.table.pack(fill="both", expand=True)
        for t in self.turns:
            self.table.insert("", "end", iid=str(t.id), values=(f"{t.start/RATE:.2f}–{t.end/RATE:.2f}", t.speaker, t.text))
        def selected(action):
            ids = self.table.selection()
            if ids:
                action(references(self.turns, [int(ids[0])])[0])
        self.button("Beluister beurt", lambda: selected(self.play))
        self.button("Corrigeer tekst", lambda: selected(self.edit))
        row = ttk.Frame(self.body)
        row.pack(anchor="w")
        for role in ("therapeut","cliënt"):
            ttk.Button(row, text=f"Deze beurt → {role}", command=lambda r=role: selected(lambda t: self.assign(t,r))).pack(side="left")
        if any(t.speaker in ("A","B") for t in self.turns):
            for speaker in ("A","B"):
                self.button(f"{speaker} is therapeut · andere spreker is cliënt", lambda s=speaker: self.map_roles(s))
        self.button("Transcript gecontroleerd · toon feedback", self.feedback)
        self.button("Sessie verwijderen", self.reset)

    def edit(self, t):
        value = simpledialog.askstring("Tekst corrigeren", "Gecontroleerde tekst", initialvalue=t.text, parent=self.root)
        if value and value.strip():
            t.text = value.strip()
            self.review()

    def assign(self, t, role):
        t.speaker = role
        self.review()

    def map_roles(self, speaker):
        for t in self.turns:
            if t.speaker in ("A","B"):
                t.speaker = "therapeut" if t.speaker == speaker else "cliënt"
        self.review()

    def feedback(self):
        if any(t.speaker not in ("therapeut","cliënt") for t in self.turns):
            messagebox.showinfo("Controle", "Wijs eerst aan elke beurt een rol toe, ook aan de beurten met een vraagteken.")
            return
        self.page(RUBRIC["status"])
        self.button("Terug naar transcript", self.review)
        self.button("Sessie afsluiten en gegevens verwijderen", self.reset)
        canvas = tk.Canvas(self.body, highlightthickness=0)
        scroll = ttk.Scrollbar(self.body, command=canvas.yview)
        scroll.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(fill="both", expand=True)
        cards = ttk.Frame(canvas)
        window = canvas.create_window(0,0,window=cards,anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window,width=e.width))
        cards.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        for rule in RUBRIC["criteria"]:
            card = ttk.LabelFrame(cards, text=rule["titel"], padding=8)
            card.pack(fill="x", pady=4)
            ids = evidence(self.turns, rule, RUBRIC)
            ttk.Label(card,text=rule["observatie"] if ids else UNKNOWN,wraplength=740).pack(anchor="w")
            if ids:
                for t in references(self.turns, ids):
                    ttk.Label(card,text=f"“{t.text}”",wraplength=740).pack(anchor="w")
                    self.button(f"▶ {t.speaker} · beurt {t.id} · {t.start/RATE:.2f}–{t.end/RATE:.2f} s",lambda t=t:self.play(t),card)
                ttk.Label(card,text=rule["suggestie"],wraplength=740).pack(anchor="w")

    def close(self):
        self.stop_stream()
        sd.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    Coach(root)
    root.mainloop()
