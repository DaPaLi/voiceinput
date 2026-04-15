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

## Einstellungen beim Start

Beim Start erscheint ein Dialog zur Auswahl von **Modell** und **Sprache**:

### Modelle im Vergleich

| Modell | Größe | Qualität | Geschwindigkeit |
|---|---|---|---|
| `tiny` | ~75 MB | ausreichend | extrem schnell |
| `base` | ~145 MB | gut | sehr schnell |
| `small` | ~500 MB | gut | sehr schnell |
| `medium` | ~1,5 GB | sehr gut | schnell |
| `large-v2` | ~3 GB | sehr gut | langsamer |
| `large-v3` | ~3 GB | beste | langsamer |

### Unterstützte Sprachen

Deutsch, Englisch, Französisch, Spanisch, Italienisch, Portugiesisch, Niederländisch, Polnisch, Russisch, Japanisch, Chinesisch, Arabisch, Türkisch, Koreanisch – und viele mehr.

## Lizenz

MIT License – siehe [LICENSE](LICENSE)
