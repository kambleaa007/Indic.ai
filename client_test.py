import sys, urllib.request, json

sys.stdout.reconfigure(encoding="utf-8")

def post(text, voice="hi", speed=1.0, out="cli_out.wav"):
    body = json.dumps({"text": text, "voice": voice, "speed": speed}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/tts", data=body,
        headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    with urllib.request.urlopen(req) as r:
        data = r.read()
    open(out, "wb").write(data)
    print(f"OK {r.status} {r.headers['Content-Type']} {len(data)} bytes -> {out} | {text[:40]}")

post("नमस्ते! यह पूर्ण रूप से मुफ़्त और असीमित है।", out="cli_hi.wav")
post("Indic AI speech is completely free and unlimited.", voice="en", speed=1.3, out="cli_en.wav")
