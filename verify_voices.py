import sys

sys.stdout.reconfigure(encoding="utf-8")

from piper import PiperVoice

VOICES = {
    "hi": ("hi_IN-rohan-medium", "नमस्ते दोस्तों, यह हिंदी में बोलने वाला एआई है।"),
    "hi-f": ("hi_IN-priyamvada-medium", "नमस्ते, आज मौसम बहुत अच्छा है।"),
    "mr": ("mr_IN-google-medium", "नमस्कार मित्रांनी, हे मराठीत बोलणारे एआय आहे."),
    "te": ("te_IN-maya-medium", "నమస్కారం స్నేహితులు, ఇది తెలుగులో మాట్లాడే ఏఐ."),
    "te-m": ("te_IN-venkatesh-medium", "నమస్కారం, ఈరోజు వాతావరణం చాలా బాగుంది."),
    "bn": ("bn_BD-google-medium", "নমস্কার বন্ধুরা, এটি বাংলায় কথা বলা এআই।"),
    "ml": ("ml_IN-arjun-medium", "നമസ്കാരം സുഹൃതാക്കൾ, ഇത് മലയാളത്തിൽ സംസാരിക്കുന്ന AI ആണ്."),
    "ur": ("ur_PK-fasih-medium", "سلام دوستو، یہ اردو میں بولنے والا AI ہے۔"),
    "en": ("en_US-lessac-medium", "Indic AI speech is completely free and unlimited."),
}

ok, fail = 0, 0
for name, (stem, text) in VOICES.items():
    try:
        v = PiperVoice.load(f"voices/{stem}.onnx", config_path=f"voices/{stem}.onnx.json")
        chunks = list(v.synthesize(text))
        total = sum(len(c.audio_int16_bytes) for c in chunks)
        if total > 1000:
            print(f"OK   {name:6} chunks={len(chunks):2} bytes={total:7}")
            ok += 1
        else:
            print(f"EMPTY {name:6} bytes={total}")
            fail += 1
    except Exception as e:
        print(f"FAIL {name:6} {type(e).__name__}: {e}")
        fail += 1

print(f"\n{ok} ok, {fail} failed")
