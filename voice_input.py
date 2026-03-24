"""
Voice Input
===========
Strg + Alt + Leertaste halten → sprechen → loslassen → Text wird eingefügt
Strg + Alt + Q = Beenden
"""

import sys, threading, time, ctypes
import numpy as np
import sounddevice as sd
import win32clipboard, win32con, win32api
import pystray
from PIL import Image, ImageDraw
from pynput import keyboard as pynput_kb
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
MODEL_SIZE  = "medium"
LANGUAGE    = "de"

# ── Icons ────────────────────────────────────────────────────────────────────
def make_icon(mic_col, bg_col):
    img = Image.new("RGBA", (64, 64), (0,0,0,0))
    d = ImageDraw.Draw(img)
    d.ellipse([2,2,62,62], fill=bg_col)
    d.rounded_rectangle([22,10,42,38], radius=10, fill=mic_col)
    d.arc([16,24,48,50], start=0, end=180, fill=mic_col, width=4)
    d.rectangle([30,48,34,56], fill=mic_col)
    d.rectangle([22,54,42,58], fill=mic_col)
    return img

ICO_READY = make_icon((255,255,255),(50,50,50))
ICO_REC   = make_icon((255,255,255),(200,40,40))
ICO_PROC  = make_icon((255,255,255),(40,120,200))

# ── Whisper ──────────────────────────────────────────────────────────────────
print("[VoiceInput] Lade Modell ...", flush=True)
model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")
print("[VoiceInput] Bereit! Strg+Alt+Leertaste halten = aufnehmen.", flush=True)

# ── State ────────────────────────────────────────────────────────────────────
recording      = False
audio_frames   = []
lock           = threading.Lock()
tray_icon      = None
target_window  = None   # Fenster, das beim Hotkey fokussiert war

def set_icon(img, tip):
    if tray_icon:
        tray_icon.icon  = img
        tray_icon.title = tip

# ── Aufnahme ─────────────────────────────────────────────────────────────────
def start_recording():
    global recording, audio_frames, target_window
    with lock:
        if recording: return
        recording = True
        audio_frames = []
        target_window = ctypes.windll.user32.GetForegroundWindow()
    set_icon(ICO_REC, "● Aufnahme läuft...")
    print("[VoiceInput] Aufnahme...", flush=True)
    threading.Thread(target=_record, daemon=True).start()

def stop_recording():
    global recording
    with lock:
        if not recording: return
        recording = False
    set_icon(ICO_PROC, "⏳ Transkribiere...")
    print("[VoiceInput] Gestoppt.", flush=True)

def _record():
    frames = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as s:
        while True:
            with lock:
                if not recording: break
            chunk, _ = s.read(1024)
            frames.append(chunk.copy())
    audio_frames.extend(frames)
    threading.Thread(target=_transcribe, daemon=True).start()

def _transcribe():
    if not audio_frames:
        set_icon(ICO_READY, "VoiceInput – Bereit"); return
    audio = np.concatenate(audio_frames).flatten()
    if len(audio) < SAMPLE_RATE * 0.3:
        set_icon(ICO_READY, "VoiceInput – Bereit"); return
    segs, _ = model.transcribe(audio, language=LANGUAGE, beam_size=5)
    text = " ".join(s.text.strip() for s in segs).strip()
    if text:
        print(f"[VoiceInput] → {text}", flush=True)
        _paste(text)
        set_icon(ICO_READY, f"Zuletzt: {text[:50]}")
    else:
        print("[VoiceInput] Kein Text erkannt.", flush=True)
        set_icon(ICO_READY, "VoiceInput – Bereit")

def _paste(text):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
    win32clipboard.CloseClipboard()
    time.sleep(0.1)
    if target_window:
        ctypes.windll.user32.SetForegroundWindow(target_window)
    time.sleep(0.2)
    print("[VoiceInput] Füge ein...", flush=True)
    VK_CTRL, VK_V = win32con.VK_CONTROL, ord('V')
    win32api.keybd_event(VK_CTRL, 0, 0, 0)
    win32api.keybd_event(VK_V,    0, 0, 0)
    win32api.keybd_event(VK_V,    0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(VK_CTRL, 0, win32con.KEYEVENTF_KEYUP, 0)
    print("[VoiceInput] Eingefügt.", flush=True)

# ── pynput Keyboard Listener ─────────────────────────────────────────────────
SPACE = pynput_kb.Key.space
CTRL  = {pynput_kb.Key.ctrl, pynput_kb.Key.ctrl_l, pynput_kb.Key.ctrl_r}
ALT   = {pynput_kb.Key.alt,  pynput_kb.Key.alt_l,  pynput_kb.Key.alt_r}

pressed = set()

def on_press(key):
    pressed.add(key)
    if (key == SPACE
            and any(k in pressed for k in CTRL)
            and any(k in pressed for k in ALT)):
        start_recording()
    # Beenden: Ctrl+Alt+Q
    try:
        if (key.char == 'q'
                and any(k in pressed for k in CTRL)
                and any(k in pressed for k in ALT)):
            tray_icon.stop() if tray_icon else None
            sys.exit(0)
    except AttributeError:
        pass

def on_release(key):
    if key == SPACE:
        stop_recording()
    pressed.discard(key)

listener = pynput_kb.Listener(on_press=on_press, on_release=on_release)
listener.start()

# ── Tray ─────────────────────────────────────────────────────────────────────
def _tray():
    global tray_icon
    menu = pystray.Menu(
        pystray.MenuItem("VoiceInput", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Beenden", lambda: (tray_icon.stop(), sys.exit(0)))
    )
    tray_icon = pystray.Icon("VoiceInput", ICO_READY, "VoiceInput – Bereit", menu)
    tray_icon.run()

threading.Thread(target=_tray, daemon=True).start()
print("[VoiceInput] Mikrofon-Symbol aktiv.", flush=True)

# ── Hauptloop ─────────────────────────────────────────────────────────────────
listener.join()
