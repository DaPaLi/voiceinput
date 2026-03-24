"""
Voice Input für Claude Code
============================
Hotkey: Strg + Alt + Leertaste gedrückt halten → sprechen → loslassen → Text wird eingefügt

Starten: voice_input.bat (Doppelklick oder Autostart)
Beenden: Strg+Alt+Q
"""

import sys
import threading
import time
import numpy as np
import sounddevice as sd
import keyboard
import subprocess
import ctypes

PYTHON = sys.executable
HOTKEY_RECORD = "ctrl+alt+space"
HOTKEY_QUIT   = "ctrl+alt+q"
SAMPLE_RATE   = 16000
MODEL_SIZE    = "medium"     # small=schnell, medium=besser für DE, large-v3=beste Qualität
LANGUAGE      = "de"

# ── Whisper-Modell laden (einmalig beim Start) ──────────────────────────────
print(f"[VoiceInput] Lade Whisper-Modell '{MODEL_SIZE}' ...", flush=True)
from faster_whisper import WhisperModel
model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")
print("[VoiceInput] Bereit!  Strg+Alt+Leertaste halten = aufnehmen, loslassen = Text einfügen.", flush=True)
print("[VoiceInput] Strg+Alt+Q zum Beenden.", flush=True)

# ── Aufnahme-State ──────────────────────────────────────────────────────────
recording      = False
audio_frames   = []
lock           = threading.Lock()

def set_title(text):
    ctypes.windll.kernel32.SetConsoleTitleW(f"VoiceInput – {text}")

set_title("Bereit")

def on_hotkey_down(e):
    global recording, audio_frames
    with lock:
        if recording:
            return
        recording = True
        audio_frames = []
    set_title("● Aufnahme läuft...")
    print("[VoiceInput] Aufnahme gestartet...", flush=True)
    threading.Thread(target=record_audio, daemon=True).start()

def on_hotkey_up(e):
    global recording
    with lock:
        recording = False
    set_title("⏳ Transkribiere...")
    print("[VoiceInput] Aufnahme gestoppt. Transkribiere...", flush=True)

def record_audio():
    frames = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        while True:
            with lock:
                if not recording:
                    break
            chunk, _ = stream.read(1024)
            frames.append(chunk.copy())
    audio_frames.extend(frames)
    threading.Thread(target=transcribe_and_paste, daemon=True).start()

def transcribe_and_paste():
    global audio_frames
    if not audio_frames:
        set_title("Bereit")
        return

    audio = np.concatenate(audio_frames, axis=0).flatten()
    if len(audio) < SAMPLE_RATE * 0.3:   # kürzer als 0,3 Sek → ignorieren
        set_title("Bereit")
        return

    segments, info = model.transcribe(audio, language=LANGUAGE, beam_size=5)
    text = " ".join(seg.text.strip() for seg in segments).strip()

    if text:
        print(f"[VoiceInput] → {text}", flush=True)
        paste_text(text)
        set_title(f"Bereit  (zuletzt: {text[:40]})")
    else:
        print("[VoiceInput] Kein Text erkannt.", flush=True)
        set_title("Bereit")

def paste_text(text):
    # Text in Zwischenablage → Strg+V ins aktive Fenster
    ps = f"Set-Clipboard -Value '{text.replace(chr(39), chr(96))}'"
    subprocess.run(["powershell.exe", "-Command", ps], capture_output=True)
    time.sleep(0.1)
    keyboard.press_and_release("ctrl+v")

# ── Hotkeys registrieren ────────────────────────────────────────────────────
keyboard.on_press_key(HOTKEY_RECORD.split("+")[-1],
                      lambda e: on_hotkey_down(e) if keyboard.is_pressed("ctrl") and keyboard.is_pressed("alt") else None,
                      suppress=False)
keyboard.on_release_key(HOTKEY_RECORD.split("+")[-1],
                        lambda e: on_hotkey_up(e) if recording else None,
                        suppress=False)

keyboard.add_hotkey(HOTKEY_QUIT, lambda: (print("[VoiceInput] Beendet."), sys.exit(0)))

# ── Hauptloop ───────────────────────────────────────────────────────────────
keyboard.wait()
