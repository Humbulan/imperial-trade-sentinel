# Imperial Trade Sentinel

**Microsoft Agents League Hackathon 2026**
**Track:** Reasoning Agents (Microsoft Foundry IQ)
**Prize targets:** Best Reasoning Agent, Best Use of IQ Tools

## What it does
Imperial Trade Sentinel is an AI agent that answers natural‑language questions about real‑time SADC trade corridors, wealth portfolio, lithium exports, and logistics performance – all powered by a live 59‑service microgrid running on a Samsung Galaxy A73 (Android 16).

## How it works
1. User sends a `POST /ask` with a question.
2. Agent fetches live data from the imperial stack (Sovereign_Master, SADC_Sync, Surge_Monitor, etc.)
3. It sends the question + context to **Microsoft Foundry IQ** for grounded reasoning.
4. Returns a cited answer with sources.

## Integration with Microsoft IQ
- Uses **Foundry IQ** for agentic knowledge retrieval
- Reduces hallucination by grounding answers in real imperial data
- All answers include citations pointing to the source

## Demo video
https://youtube.com/shorts/jfC0BK7VC1g
## How to run
```bash
pip install -r requirements.txt
python agent.py
```

Then query:
```bash
curl -X POST http://localhost:8123/ask -H "Content-Type: application/json" -d '{"question": "What is our portfolio value?"}'
```

## Why it is unique
- Entire infrastructure runs on a **mobile phone** – no cloud dependency (except IQ)
- Real‑time SADC trade corridor monitoring with wealth lock analytics
- 59 active ports orchestrated from a single Termux terminal
