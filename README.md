# Indic.ai TTS

Local, **free and unlimited** text-to-speech. No API key, no character quota, no
cloud calls — the model runs offline on your CPU via [Piper](https://github.com/OHF-Voice/piper1-gpl)
(ONNX).

| Voice | Model | Language |
|---|---|---|
| `hi` | `hi_IN-rohan-medium` | Hindi |
| `en` | `en_US-lessac-medium` | English |

## Run it

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn tts_server:app --host 127.0.0.1 --port 8000
```

Then open http://127.0.0.1:8000/docs for the interactive API.

## Speak text

```powershell
$body = @{ text = "नमस्ते दोस्तों!"; voice = "hi" } | ConvertTo-Json
Invoke-WebRequest -Uri "http://127.0.0.1:8000/tts" -Method Post `
  -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body)) `
  -OutFile speech.wav
```

Or from Python:

```python
import json, urllib.request

body = json.dumps({"text": "नमस्ते दोस्तों!", "voice": "hi"}).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8000/tts", data=body,
    headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
open("speech.wav", "wb").write(urllib.request.urlopen(req).read())
```

Run `client_test.py` for a working example.

### Important: send UTF-8

Windows PowerShell 5.1 mangles Devanagari text if you pass a string body
directly. Always encode explicitly with `[Text.Encoding]::UTF8.GetBytes($body)`,
as shown above. Without this the server returns 422.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `GET` | `/voices` | List voices |
| `POST` | `/tts` | Synthesize speech, returns `audio/wav` |

Request body:

| Field | Type | Default | Range |
|---|---|---|---|
| `text` | string | required | min 1 char |
| `voice` | string | `hi` | `hi` or `en` |
| `speed` | float | `1.0` | 0.5 – 2.0 (>1 is faster) |

## CLI, no server

```powershell
echo नमस्ते | .\.venv\Scripts\python.exe -m piper -m voices\hi_IN-rohan-medium.onnx -f out.wav
```

## Adding more voices

Piper has 30+ languages. Copy a model + config into `voices/`, then register it
in the `VOICES` dict in `tts_server.py`:

```python
VOICES = {
    "hi": "hi_IN-rohan-medium",
    "en": "en_US-lessac-medium",
    "mr": "mr_IN-...",   # Marathi
}
```

Model URLs follow this pattern on Hugging Face
(`rhasspy/piper-voices`, repo path `<lang>/<locale>/<name>/<quality>/`):

```
https://huggingface.co/rhasspy/piper-voices/resolve/main/<lang>/<locale>/<name>/<quality>/<file>
```

Useful Indic voices: `hi_IN/pratham`, `hi_IN/priyamvada`, `hi_IN/rohan`.

## Performance

Roughly 1–2x real time on a modern CPU. The 60 MB models load lazily on first
use per voice and stay cached. On an 11.9 GB RAM machine without a GPU, both
voices fit comfortably.

## Licenses

Piper code is MIT; the original `rhasspy/piper` repo is archived, development
continues at `OHF-Voice/piper1-gpl` under GPL-3.0. **Each voice model has its
own license — check the model's card before commercial use.**
