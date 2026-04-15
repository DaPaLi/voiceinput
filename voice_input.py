"""
Voice Input
===========
Tastenkombination halten → sprechen → loslassen → Text wird eingefügt
Strg + Alt + Q = Beenden
"""

import sys, threading, time, ctypes, json, os
import numpy as np
import sounddevice as sd
import win32clipboard, win32con, win32api
import pystray
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw
from pynput import keyboard as pynput_kb
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000

MODELS = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]

LANGUAGES = [
    ("de", "Deutsch"),
    ("en", "Englisch"),
    ("fr", "Französisch"),
    ("es", "Spanisch"),
    ("it", "Italienisch"),
    ("pt", "Portugiesisch"),
    ("nl", "Niederländisch"),
    ("pl", "Polnisch"),
    ("ru", "Russisch"),
    ("ja", "Japanisch"),
    ("zh", "Chinesisch"),
    ("ar", "Arabisch"),
    ("tr", "Türkisch"),
    ("ko", "Koreanisch"),
]

# ── Config ───────────────────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_HOTKEY = {"modifiers": ["ctrl", "alt"], "key": "space", "display": "Strg+Alt+Leertaste"}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"model": "large-v3", "language": "de", "hotkey": DEFAULT_HOTKEY}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

# Tkinter keysym → (modifier_name or key_name, is_modifier)
TK_MODIFIER_MAP = {
    "Control_L": "ctrl", "Control_R": "ctrl",
    "Alt_L": "alt", "Alt_R": "alt",
    "Shift_L": "shift", "Shift_R": "shift",
    "Super_L": "win", "Super_R": "win",
}
TK_KEY_DISPLAY = {
    "space": "Leertaste", "Return": "Enter", "Tab": "Tab",
    "BackSpace": "Rücktaste", "Escape": "Escape",
    "F1":"F1","F2":"F2","F3":"F3","F4":"F4","F5":"F5","F6":"F6",
    "F7":"F7","F8":"F8","F9":"F9","F10":"F10","F11":"F11","F12":"F12",
}
MOD_DISPLAY = {"ctrl": "Strg", "alt": "Alt", "shift": "Umschalt", "win": "Win"}

def tk_event_to_hotkey(event):
    """Wandelt ein tkinter KeyPress-Event in unser Hotkey-Dict um."""
    keysym = event.keysym
    # Modifier-only keys ignorieren
    if keysym in TK_MODIFIER_MAP:
        return None
    # Modifiers ermitteln
    mods = []
    if event.state & 0x4:   mods.append("ctrl")
    if event.state & 0x20000: mods.append("alt")
    if event.state & 0x1:   mods.append("shift")
    if not mods:
        return None  # Mindestens ein Modifier erforderlich
    # Key-Name normalisieren
    if len(keysym) == 1:
        key = keysym.lower()
        display_key = keysym.upper()
    else:
        key = keysym  # z.B. "space", "Return", "F5"
        display_key = TK_KEY_DISPLAY.get(keysym, keysym)
    display = "+".join(MOD_DISPLAY.get(m, m.capitalize()) for m in mods) + "+" + display_key
    return {"modifiers": mods, "key": key, "display": display}

# ── Einstellungen ─────────────────────────────────────────────────────────────
def choose_settings(cfg):
    result = {"model": cfg["model"], "language": cfg["language"], "hotkey": cfg["hotkey"]}

    root = tk.Tk()
    root.title("VoiceInput – Einstellungen")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.eval("tk::PlaceWindow . center")

    frame = tk.Frame(root, padx=20, pady=15)
    frame.pack()

    # Modell
    tk.Label(frame, text="Whisper-Modell:", font=("Segoe UI", 11, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
    model_var = tk.StringVar(value=result["model"])
    for i, m in enumerate(MODELS):
        tk.Radiobutton(frame, text=m, variable=model_var, value=m,
                       font=("Segoe UI", 10)).grid(row=i+1, column=0, sticky="w", padx=10)

    # Sprache
    tk.Label(frame, text="Sprache:", font=("Segoe UI", 11, "bold")).grid(
        row=0, column=1, sticky="w", padx=(30, 0), pady=(0, 5))
    lang_var = tk.StringVar(value=result["language"])
    for i, (code, name) in enumerate(LANGUAGES):
        tk.Radiobutton(frame, text=name, variable=lang_var, value=code,
                       font=("Segoe UI", 10)).grid(row=i+1, column=1, sticky="w", padx=(40, 0))

    # Hotkey
    hotkey_row = max(len(MODELS), len(LANGUAGES)) + 2
    tk.Label(frame, text="Aufnahme-Hotkey:", font=("Segoe UI", 11, "bold")).grid(
        row=hotkey_row, column=0, columnspan=2, sticky="w", pady=(15, 5))

    hotkey_var = tk.StringVar(value=result["hotkey"]["display"])
    hotkey_entry = tk.Entry(frame, textvariable=hotkey_var, font=("Segoe UI", 10),
                            width=28, state="readonly", readonlybackground="#f0f0f0",
                            relief="solid", cursor="hand2")
    hotkey_entry.grid(row=hotkey_row+1, column=0, columnspan=2, sticky="w", padx=10)

    hint_label = tk.Label(frame, text="← Klicken, dann Tastenkombination drücken",
                          font=("Segoe UI", 9), fg="#888")
    hint_label.grid(row=hotkey_row+2, column=0, columnspan=2, sticky="w", padx=10, pady=(2, 0))

    capturing = {"active": False}

    def start_capture(e=None):
        capturing["active"] = True
        hotkey_var.set("Drücke jetzt deine Kombination...")
        hotkey_entry.config(readonlybackground="#fff3cd")
        hint_label.config(text="Halten + Loslassen zum Bestätigen", fg="#b8860b")
        root.bind("<KeyPress>", on_capture_key)

    def on_capture_key(e):
        if not capturing["active"]:
            return
        hk = tk_event_to_hotkey(e)
        if hk:
            result["hotkey"] = hk
            hotkey_var.set(hk["display"])
            hotkey_entry.config(readonlybackground="#d4edda")
            hint_label.config(text="Hotkey gespeichert!", fg="#28a745")
            capturing["active"] = False
            root.unbind("<KeyPress>")
            root.after(1500, lambda: hint_label.config(
                text="← Klicken, dann Tastenkombination drücken", fg="#888"))
            root.after(1500, lambda: hotkey_entry.config(readonlybackground="#f0f0f0"))

    hotkey_entry.bind("<Button-1>", start_capture)

    def confirm():
        result["model"] = model_var.get()
        result["language"] = lang_var.get()
        root.destroy()

    tk.Button(root, text="Starten", command=confirm,
              font=("Segoe UI", 10, "bold"), padx=20, pady=6,
              bg="#1a73e8", fg="white", relief="flat", cursor="hand2").pack(pady=15)

    root.protocol("WM_DELETE_WINDOW", confirm)
    root.mainloop()
    return result["model"], result["language"], result["hotkey"]

cfg = load_config()
MODEL_SIZE, LANGUAGE, HOTKEY = choose_settings(cfg)
cfg.update({"model": MODEL_SIZE, "language": LANGUAGE, "hotkey": HOTKEY})
save_config(cfg)

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

def _show_loading():
    win = tk.Tk()
    win.title("VoiceInput")
    win.resizable(False, False)
    win.attributes("-topmost", True)
    win.overrideredirect(True)
    win.configure(bg="#1e1e1e")
    win.geometry("320x80")
    win.eval("tk::PlaceWindow . center")
    tk.Label(win, text=f"Lade Modell: {MODEL_SIZE} ...", font=("Segoe UI", 12),
             bg="#1e1e1e", fg="white").pack(expand=True)
    bar = ttk.Progressbar(win, mode="indeterminate", length=260)
    bar.pack(pady=(0, 12))
    bar.start(12)
    return win

_load_win = _show_loading()
_load_win.update()

model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")

_load_win.destroy()
print(f"[VoiceInput] Bereit! {HOTKEY['display']} halten = aufnehmen.", flush=True)

# ── Hotkey-Matching ──────────────────────────────────────────────────────────
PYNPUT_MODS = {
    "ctrl":  {pynput_kb.Key.ctrl, pynput_kb.Key.ctrl_l, pynput_kb.Key.ctrl_r},
    "alt":   {pynput_kb.Key.alt,  pynput_kb.Key.alt_l,  pynput_kb.Key.alt_r},
    "shift": {pynput_kb.Key.shift, pynput_kb.Key.shift_l, pynput_kb.Key.shift_r},
    "win":   {pynput_kb.Key.cmd,  pynput_kb.Key.cmd_l,  pynput_kb.Key.cmd_r},
}
PYNPUT_SPECIAL = {
    "space": pynput_kb.Key.space,
    "Return": pynput_kb.Key.enter,
    "Tab": pynput_kb.Key.tab,
    "BackSpace": pynput_kb.Key.backspace,
    "Escape": pynput_kb.Key.esc,
    **{f"F{i}": getattr(pynput_kb.Key, f"f{i}") for i in range(1, 13)},
}

def key_is_main(key, key_name):
    """Prüft ob 'key' dem konfigurierten Haupt-Taste entspricht."""
    if key_name in PYNPUT_SPECIAL:
        return key == PYNPUT_SPECIAL[key_name]
    if len(key_name) == 1:
        try:
            return key.char and key.char.lower() == key_name.lower()
        except AttributeError:
            return False
    return False

def hotkey_active(key, pressed_keys):
    """Gibt True zurück wenn der konfigurierte Hotkey gedrückt ist."""
    if not key_is_main(key, HOTKEY["key"]):
        return False
    for mod in HOTKEY["modifiers"]:
        if not any(k in pressed_keys for k in PYNPUT_MODS.get(mod, set())):
            return False
    return True

def main_key_released(key):
    return key_is_main(key, HOTKEY["key"])

# ── State ────────────────────────────────────────────────────────────────────
recording     = False
audio_frames  = []
lock          = threading.Lock()
tray_icon     = None
target_window = None

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
CTRL_KEYS = {pynput_kb.Key.ctrl, pynput_kb.Key.ctrl_l, pynput_kb.Key.ctrl_r}
ALT_KEYS  = {pynput_kb.Key.alt,  pynput_kb.Key.alt_l,  pynput_kb.Key.alt_r}

pressed = set()

def on_press(key):
    pressed.add(key)
    if hotkey_active(key, pressed):
        start_recording()
    # Beenden: Ctrl+Alt+Q
    try:
        if (key.char == 'q'
                and any(k in pressed for k in CTRL_KEYS)
                and any(k in pressed for k in ALT_KEYS)):
            tray_icon.stop() if tray_icon else None
            sys.exit(0)
    except AttributeError:
        pass

def on_release(key):
    if main_key_released(key):
        stop_recording()
    pressed.discard(key)

listener = pynput_kb.Listener(on_press=on_press, on_release=on_release)
listener.start()

# ── Tray ─────────────────────────────────────────────────────────────────────
def _tray():
    global tray_icon
    menu = pystray.Menu(
        pystray.MenuItem("VoiceInput", None, enabled=False),
        pystray.MenuItem(f"Hotkey: {HOTKEY['display']}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Beenden", lambda: (tray_icon.stop(), sys.exit(0)))
    )
    tray_icon = pystray.Icon("VoiceInput", ICO_READY, "VoiceInput – Bereit", menu)
    tray_icon.run()

threading.Thread(target=_tray, daemon=True).start()
print("[VoiceInput] Mikrofon-Symbol aktiv.", flush=True)

# ── Hauptloop ─────────────────────────────────────────────────────────────────
listener.join()
