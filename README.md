# VoiceInput

Lokale Spracheingabe für Windows – powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (OpenAI Whisper) mit GPU-Beschleunigung.

Gesprochener Text wird transkribiert und per Zwischenablage in das aktive Fenster eingefügt – komplett **offline**, **kostenlos** und **ohne Cloud**.

## Features

- Lokale Transkription via Whisper (kein Internet nötig)
- GPU-Beschleunigung (NVIDIA CUDA)
- Gute Erkennung für **Deutsch** und andere Sprachen
- Einfacher Hotkey: `Strg + Alt + Leertaste` halten → sprechen → loslassen
- Text wird direkt ins aktive Fenster eingefügt
- System-Tray-Symbol zeigt Status (grau = bereit, rot = Aufnahme, blau = Transkription)
- Kein Admin-Modus nötig

## Voraussetzungen

- Windows 10/11
- Python 3.10+
- NVIDIA GPU mit CUDA (empfohlen) – funktioniert auch auf CPU, aber langsamer

## Installation

```bash
pip install faster-whisper sounddevice numpy pynput pystray Pillow pywin32
```

## Starten

Doppelklick auf **`VoiceInput starten.bat`**

Oder direkt:
```bash
python voice_input.py
```

Beim ersten Start wird das Whisper-Modell automatisch heruntergeladen (~1,5 GB für `medium`, ~3 GB für `large-v3`).

## Bedienung

| Aktion | Hotkey |
|---|---|
| Aufnahme starten/stoppen | `Strg + Alt + Leertaste` (halten) |
| Programm beenden | `Strg + Alt + Q` oder Rechtsklick aufs Tray-Symbol |

## Konfiguration

In `voice_input.py` oben anpassbar:

```python
MODEL_SIZE = "medium"   # small / medium / large-v3
LANGUAGE   = "de"       # de, en, fr, ...
```

### Modelle im Vergleich

| Modell | Größe | Qualität | Geschwindigkeit |
|---|---|---|---|
| `small` | ~500 MB | gut | sehr schnell |
| `medium` | ~1,5 GB | sehr gut | schnell |
| `large-v3` | ~3 GB | beste | langsamer |

## Lizenz

MIT License – siehe [LICENSE](LICENSE)
