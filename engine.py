"""Offline analyse. Tijdgrenzen zijn sample-indexen in de beluisterde mono-opname."""
import json
import re
from dataclasses import dataclass
from pathlib import Path

RATE = 16000
UNKNOWN = "Niet te beoordelen uit dit gesprek"
RUBRIC = json.loads(Path(__file__).with_name("rubric.json").read_text(encoding="utf8"))


@dataclass
class Turn:
    id: int
    start: int
    end: int
    speaker: str
    text: str


def references(turns, ids):
    by_id = {turn.id: turn for turn in turns}
    if not ids or any(i not in by_id for i in ids):
        raise ValueError("Ongeldige beurtverwijzing")
    return [by_id[i] for i in ids]


def evidence(turns, rule, rubric):
    def match(pattern, turn):
        return re.search(pattern, turn.text, re.I)

    for i, client in enumerate(turns):
        if client.speaker != "cliënt" or not match(rubric["voorkeur"], client):
            continue
        if rule["id"] == "verkennen":
            if i and turns[i-1].speaker == "therapeut" and match(rule["patroon"], turns[i-1]):
                return [turns[i-1].id, client.id]
            continue
        candidates = turns[i+1:i+2] if rule["id"] == "reageren" else turns[i+1:i+6]
        for reply in candidates:
            if reply.speaker != "therapeut" or not match(rule["patroon"], reply):
                continue
            if rule["id"] == "afspreken" and not any(
                match(topic, client) and match(topic, reply) for topic in rubric["onderwerpen"]
            ):
                continue
            return [client.id, reply.id]
    return []


def transcribe(pcm, folder):
    import numpy as np
    import vosk

    vosk.SetLogLevel(-1)
    asr = vosk.Model(str(folder / "vosk-model-small-nl-0.22"))
    speaker = vosk.SpkModel(str(folder / "vosk-model-spk-0.4"))
    rec = vosk.KaldiRecognizer(asr, RATE)
    rec.SetSpkModel(speaker)
    rec.SetWords(True)
    turns, embeddings = [], []
    def collect(payload):
        item = json.loads(payload)
        words = item.get("result")
        if not words:
            return
        start = max(0, round(words[0]["start"] * RATE))
        end = min(len(pcm)//2, round(words[-1]["end"] * RATE))
        if end <= start:
            return
        turns.append(Turn(len(turns)+1, start, end, "?", item["text"]))
        if "spk" in item:
            v = np.array(item["spk"])
            embeddings.append((turns[-1], v / max(np.linalg.norm(v), 1e-10)))
    for pos in range(0, len(pcm), 8000):
        if rec.AcceptWaveform(pcm[pos:pos+8000]):
            collect(rec.Result())
    collect(rec.FinalResult())
    if embeddings:
        matrix = np.stack([v for _, v in embeddings])
        centers = matrix[[0, np.argmin(matrix @ matrix[0])]].copy()
        for _ in range(12):
            labels = (matrix @ centers.T).argmax(axis=1)
            for k in range(2):
                if np.any(labels == k):
                    c = matrix[labels == k].mean(axis=0)
                    centers[k] = c / max(np.linalg.norm(c), 1e-10)
        for (turn, _), k in zip(embeddings, labels):
            turn.speaker = "AB"[k]
    return turns
