# Technical Specification & POC Blueprint: Indic Voice & Multimodal Agents for Bharat Commerce

## 1. Executive Summary

* **Target Problem:** Over 500 million internet users in Tier-2, Tier-3, and rural India face severe literacy and digital friction barriers. Existing commerce and utility applications rely on complex, English-first touch interfaces, causing high cart abandonment and low adoption in rural transactional ecosystems.
* **Proposed Product:** A low-latency, plug-and-play voice agent SDK embedded into mobile applications (Web/Android/Flutter) tailored for high-friction transactional workflows: Agri-commerce, Microfinance (MFI) collections, crop insurance reporting, and local delivery logistics.
* **Core Moat:** Acoustic and linguistic models tuned for dialectal code-mixing (Hinglish, Marathi-Hindi mixing, Tanglish), noisy background conditions (Mandis, rural roads, APMC yards), and low-bandwidth network tolerance (2G/3G/spotty 4G).

---

## 2. Target Scope & Pilot User Journey

### 2.1 Pilot Use Case
**Multilingual Seed and Fertilizer Ordering (Agri-Commerce)** supporting **Hindi, Marathi, and Hinglish**.

### 2.2 End-to-End Dialog Workflow
1. **User Voice Input:**  
   *"Bhaiya, do bori urea aur ek packet hybrid tamatar ka beej bhejna Baramati ke liye."*
2. **ASR & Ingestion:** Streaming audio captured at 16kHz Linear PCM, processed through VAD and streaming Indic ASR.
3. **Intent Extraction & Normalization:** LLM parses entities (`product`, `quantity`, `unit`, `destination_hub`) into a typed schema.
4. **Mock ERP Verification:** Inventory and pricing lookup via internal service.
5. **Agent Audio Response:** Synthesized colloquial audio stream played back within $< 1.2\text{s}$:  
   *"Urea aur tamatar beej available hai. Total ₹960 hua. Kya main order confirm kar doon?"*
6. **User Confirmation & Termination:** User responds *"Haan confirm karo"*; agent triggers order placement and emits an instant WhatsApp/SMS notification hook.

---

## 3. End-to-End Latency Budget

To maintain natural conversational cadence in conversational voice interfaces, perceived latency must remain under $1,200\text{ ms}$.

$$T_{\text{total}} = T_{\text{upload}} + T_{\text{VAD}} + T_{\text{ASR}} + T_{\text{LLM\_TTFT}} + T_{\text{TTS\_TTFB}} + T_{\text{audio\_buffer}}$$

| Component | Target Budget | Optimization Strategy |
| :--- | :--- | :--- |
| **Audio Chunk Uplink** | $\approx 100 - 150\text{ ms}$ | Direct binary WebSocket streaming / WebRTC data channel (100ms chunking) |
| **Voice Activity Detection (VAD)** | $\approx 30 - 50\text{ ms}$ | Local on-device Silero VAD; halts transmission immediately on speech offset |
| **Streaming ASR (Indic)** | $\approx 250 - 350\text{ ms}$ | Sarvam AI (`saaras:v3`) / Bhashini real-time streaming WebSocket |
| **LLM Time-To-First-Token (TTFT)** | $\approx 200 - 300\text{ ms}$ | Fast inference engine (Groq / Fireworks) running Llama 3.3 70B or Claude 3.5 Haiku |
| **Streaming TTS Time-To-First-Byte (TTFB)** | $\approx 200 - 250\text{ ms}$ | Sarvam Bulbul V3 / ElevenLabs Indic with sentence-level chunk streaming |
| **Client Audio Buffer & Playback** | $\approx 50 - 100\text{ ms}$ | AudioWorklet non-blocking audio queue playback |
| **Total Cumulative Latency** | **$\approx 830 - 1,200\text{ ms}$** | Meets real-time interactive voice conversational threshold |

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Client Layer (Mobile / Web)                 │
│  - 16kHz PCM AudioWorklet Recorder                          │
│  - On-Device Silero VAD (Client-side silence pruning)       │
│  - Low-jitter Audio Buffer Queue                            │
└──────────────────────────────▲──────────────────────────────┘
                               │
               Full-Duplex WS  │ Binary PCM Chunks
               (Low Latency)   │ Base64/Opus Responses
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             FastAPI Gateway & Session Orchestrator          │
│  - Connection pooling & Session state tracker               │
│  - Audio pipeline multiplexer                               │
└──────────────┬───────────────────────────────▲──────────────┘
               │                               │
       Audio   │                       Audio   │
       Stream  │                       Stream  │
               ▼                               │
    ┌──────────────────────┐        ┌──────────────────────┐
    │  Streaming Indic ASR │        │  Streaming Indic TTS │
    │  (Sarvam / Bhashini) │        │   (Sarvam Bulbul)    │
    └──────────┬───────────┘        └──────────▲───────────┘
               │ Transcripts                   │ Synthesized
               │ (Partial/Final)               │ Text Chunks
               ▼                               │
    ┌──────────────────────────────────────────┴───────────┐
    │          Orchestration & Reasoning Layer             │
    │  - LLM Inference (Llama 3.3 70B / Claude 3.5 Haiku)  │
    │  - Pydantic Function Calling Engine                  │
    │  - Dialog State Machine & Interrupt Controller       │
    └──────────────────────────┬───────────────────────────┘
                               │ Tool Calls / DB Queries
                               ▼
    ┌──────────────────────────────────────────────────────┐
    │      Mock Rural Commerce & Inventory Services        │
    │  - SKU Catalog & Regional Nomenclature Mapper        │
    │  - Local Mandi Pricing Engine                        │
    └──────────────────────────────────────────────────────┘
```

---

## 5. Technology Stack Selection

| Subsystem | Component | Technology / Vendor | Justification |
| :--- | :--- | :--- | :--- |
| **Edge / Client** | Audio Ingestion | Web Audio API (`AudioWorklet`) / Flutter `record` | Uninterrupted 16kHz Linear PCM capture without UI thread locks. |
| | VAD Engine | Silero VAD (On-Device ONNX runtime) | Eliminates transmitting ambient silence over limited cellular data. |
| **Ingress Layer** | WebSocket Gateway | Python 3.11+ / FastAPI / `uvloop` | Asynchronous event loop capable of handling thousands of concurrent audio sockets. |
| **ASR Layer** | Indic Speech-to-Text | Sarvam AI (`saaras:v3`) / Bhashini WebSocket | Proven high accuracy on code-mixed Hinglish and regional dialects. |
| **Reasoning Engine** | Function-Calling LLM | Llama 3.3 70B (Groq) or Claude 3.5 Haiku | Sub-250ms TTFT with strict JSON-schema adherence for structured tool calling. |
| **TTS Layer** | Indic Voice Synthesis | Sarvam Bulbul V3 | Natural conversational cadence, low TTFB, and regional pronunciation accuracy. |
| **Backend & Mock DB** | Data & State | SQLite / Redis | Session-state caching, barge-in flag tracking, and inventory storage. |

---

## 6. Implementation Code Blueprint

### 6.1 Data Models & Schemas (`schemas.py`)

```python
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class OrderItem(BaseModel):
    product_name: str = Field(
        description="Standardized product name in English or Hindi (e.g., 'urea', 'tamatar beej')"
    )
    quantity: float = Field(description="Quantity requested")
    unit: str = Field(
        description="Measurement unit: 'bori', 'packet', 'kg', 'litre', 'katta'"
    )

class IntentExtraction(BaseModel):
    intent: Literal["order_create", "price_inquiry", "order_status", "fallback"]
    items: List[OrderItem] = Field(default_factory=list)
    location: Optional[str] = Field(
        default=None, description="Destination Mandi, village, or town"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
```

---

### 6.2 Conversational Orchestrator & Fast Pipeline (`agent_server.py`)

```python
import asyncio
import json
import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import httpx

app = FastAPI(title="Indic Voice Agent Backend")
logging.basicConfig(level=logging.INFO)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "your_sarvam_api_key")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key")

MOCK_CATALOG = {
    "urea": {"price": 266.50, "unit": "bori", "in_stock": True},
    "tamatar beej": {"price": 420.00, "unit": "packet", "in_stock": True},
    "dap": {"price": 1350.00, "unit": "bori", "in_stock": False}
}

SYSTEM_PROMPT = """
You are a helpful rural commerce co-pilot for Bharat.
Understand code-mixed queries (Hindi, Marathi, Hinglish).
Always output valid JSON conforming to the requested schema.
Normalize regional terms:
- 'bori' / 'katta' -> bori
- 'tamatar beej' -> tamatar beej
"""

@app.websocket("/ws/voice-agent")
async def voice_agent_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("Client connected to voice session.")

    try:
        while True:
            # Receive binary audio chunk or JSON control payload
            message = await websocket.receive()
            
            if "bytes" in message:
                audio_bytes = message["bytes"]
                # In production: forward audio_bytes directly to ASR streaming pipeline
                continue

            elif "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "utterance_end":
                    # Simulated transcript for POC verification
                    transcript = data.get("transcript", "")
                    logging.info(f"Processing transcript: {transcript}")

                    # 1. Parse Intent & Extract Entities via Fast LLM
                    parsed_intent = await extract_intent_from_llm(transcript)
                    
                    # 2. Execute Business Logic / Inventory Lookup
                    response_text = handle_commerce_logic(parsed_intent)
                    
                    # 3. Stream Response Text & Trigger TTS synthesis
                    await websocket.send_json({
                        "type": "agent_response_text",
                        "text": response_text
                    })

    except WebSocketDisconnect:
        logging.info("Client disconnected from session.")
    except Exception as e:
        logging.error(f"Error in pipeline: {e}")
        await websocket.close()

async def extract_intent_from_llm(text: str) -> dict:
    """Call Groq / Fast Inference endpoint to extract typed JSON."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Parse this order request: '{text}'"}
        ],
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=3.0) as client:
        res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        res_json = res.json()
        return json.loads(res_json["choices"][0]["message"]["content"])

def handle_commerce_logic(intent_data: dict) -> str:
    """Process inventory check and calculate subtotal."""
    items = intent_data.get("items", [])
    if not items:
        return "Bhaiya, aapko kya samaan chahiye? Urea ya beej ke baare mein batayein."

    total_amount = 0.0
    confirmed_items = []

    for item in items:
        name = item.get("product_name", "").lower()
        qty = item.get("quantity", 1)
        unit = item.get("unit", "unit")

        if name in MOCK_CATALOG:
            stock_info = MOCK_CATALOG[name]
            if stock_info["in_stock"]:
                cost = stock_info["price"] * qty
                total_amount += cost
                confirmed_items.append(f"{int(qty)} {unit} {name}")
            else:
                return f"Maaf kijiye, {name} abhi stock mein uplabdh nahi hai."
        else:
            return f"Maaf kijiye, {name} hamare catalog mein nahi mila."

    items_str = ", ".join(confirmed_items)
    return f"{items_str} available hai. Kul milakar ₹{total_amount:.2f} hua. Kya main order book kar doon?"
```

---

### 6.3 Browser Audio Producer (`recorder.js`)

```javascript
// AudioWorklet-based client streaming capture at 16kHz
let audioCtx;
let socket;

async function startVoiceSession() {
    socket = new WebSocket("ws://localhost:8000/ws/voice-agent");
    socket.binaryType = "arraybuffer";

    socket.onopen = () => console.log("Voice agent WebSocket established.");
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "agent_response_text") {
            console.log("Agent response:", data.text);
            // Play incoming synthesized audio chunks here
        }
    };

    audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const source = audioCtx.createMediaStreamSource(stream);

    // Create script processor or worklet to intercept raw PCM
    const processor = audioCtx.createScriptProcessor(4096, 1, 1);
    source.connect(processor);
    processor.connect(audioCtx.destination);

    processor.onaudioprocess = (e) => {
        if (socket.readyState === WebSocket.OPEN) {
            const inputData = e.inputBuffer.getChannelData(0);
            // Convert Float32Array to 16-bit signed PCM
            const pcm16 = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                pcm16[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
            }
            socket.send(pcm16.buffer);
        }
    };
}
```

---

## 7. Field Validation & Evaluation Framework

| Metric | Target Goal | Unacceptable Boundary | Verification Protocol |
| :--- | :--- | :--- | :--- |
| **Latency (Audio-In to Audio-Out)** | $< 1,200\text{ ms}$ | $> 2,000\text{ ms}$ | Automated timestamp logs tracking `VAD_SPEECH_STOP` to `TTS_FIRST_BUFFER_PLAYBACK`. |
| **Colloquial Entity Parsing** | $> 92\%$ accuracy | $< 80\%$ accuracy | Test suite of 200 field-recorded Hinglish and regional dialect audio samples. |
| **Acoustic Noise Resilience** | Word Error Rate (WER) $< 18\%$ | WER $> 30\%$ | Benchmarked against background noise recordings from Pune APMC Mandi ($15\text{dB}$ to $20\text{dB}$ SNR). |
| **Barge-in / Interruption Lag** | $< 250\text{ ms}$ | $> 600\text{ ms}$ | Time taken for playback to stop when user interrupts agent speech mid-sentence. |

---

## 8. Two-Week Implementation Timeline

```
Week 1: Audio Pipes & Speech Integrations
├── Day 01: Client AudioWorklet & 16kHz PCM streaming pipeline.
├── Day 02: On-device Silero VAD integration; filter ambient Mandi audio noise.
├── Day 03: Sarvam AI / Bhashini streaming WebSocket ingestion bridge.
├── Day 04: Real-time transcript buffering and barge-in signal handler.
└── Day 05: Benchmark Speech-to-Text latency across 2G/3G throttled networks.

Week 2: Intelligence, Catalog Mock, & TTS Streaming
├── Day 06: Pydantic Structured Extraction pipeline via fast-inference LLMs.
├── Day 07: Regional agricultural nomenclature translation layer ('katta', 'bori', etc.).
├── Day 08: Mock catalog lookup & WhatsApp confirmation webhook trigger.
├── Day 09: Sarvam Bulbul V3 low-latency TTS chunking and browser playback queue.
└── Day 10: End-to-end latency optimization, error fallbacks, and live interactive demo.
```