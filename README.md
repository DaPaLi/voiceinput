# VoiceInput

Lokale Spracheingabe für Windows – powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (OpenAI Whisper) mit GPU-Beschleunigung.

Gesprochener Text wird transkribiert und per Zwischenablage in das aktive Fenster eingefügt – komplett **offline**, **kostenlos** und **ohne Cloud**.

## Features

- Lokale Transkription via Whisper (kein Internet nötig)
- GPU-Beschleunigung (NVIDIA CUDA)
- Gute Erkennung für **Deutsch** und andere Sprachen
- Einfacher Hotkey: `Strg + Alt + Leertaste` halten → sprechen → loslassen
- Text wird eingefügt – du prüfst, dann selbst Enter drücken

## Voraussetzungen

- Windows 10/11
- Python 3.10+
- NVIDIA GPU mit CUDA (empfohlen) – funktioniert auch auf CPU, aber langsamer

## Installation

```bash
pip install faster-whisper sounddevice numpy keyboard
```

## Starten

Doppelklick auf **`VoiceInput starten.bat`**

Oder direkt:
```bash
python voice_input.py
```

Beim ersten Start wird das Whisper-Modell (~1,5 GB) automatisch heruntergeladen.

## Bedienung

| Aktion | Hotkey |
|---|---|
| Aufnahme starten/stoppen | `Strg + Alt + Leertaste` (halten) |
| Programm beenden | `Strg + Alt + Q` |

## Konfiguration

In `voice_input.py` oben anpassbar:

```python
MODEL_SIZE = "medium"   # small / medium / large-v3
LANGUAGE   = "de"       # de, en, fr, ...
HOTKEY_RECORD = "ctrl+alt+space"
```

## Lizenz

MIT License – siehe [LICENSE](LICENSE)
