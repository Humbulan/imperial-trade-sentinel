#!/usr/bin/env python3
import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

IMPERIAL_SERVICES = {
    "portfolio": "http://localhost:8124/api/value",
    "trade_volume": "http://localhost:8124/api/volume",
    "lithium": "http://localhost:8124/api/lithium",
    "wealth_lock": "http://localhost:8124/api/wealth_lock",
    "bi_summary": "http://localhost:8124/api/summary",
    "system_status": "http://localhost:8124/api/status",
}

def fetch_imperial_data(metric):
    url = IMPERIAL_SERVICES.get(metric)
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def gather_context(question):
    q_lower = question.lower()
    context = {}
    if any(k in q_lower for k in ["portfolio", "valuation", "wealth", "r500b"]):
        context["portfolio"] = fetch_imperial_data("portfolio")
        context["wealth_lock"] = fetch_imperial_data("wealth_lock")
    if any(k in q_lower for k in ["trade", "volume", "sadc", "corridor"]):
        context["trade_volume"] = fetch_imperial_data("trade_volume")
    if any(k in q_lower for k in ["lithium", "export"]):
        context["lithium"] = fetch_imperial_data("lithium")
    if any(k in q_lower for k in ["bi", "business", "intelligence"]):
        context["bi_summary"] = fetch_imperial_data("bi_summary")
    context["system_health"] = fetch_imperial_data("system_status") or {"status": "unknown"}
    if not any(context.values()):
        context["message"] = "Imperial stack is operational with 59 services."
    return context

def query_foundry_iq(question, context):
    endpoint = os.getenv("FOUNDRY_ENDPOINT")
    api_key = os.getenv("FOUNDRY_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    if not endpoint or not api_key:
        return {"answer": "Credentials missing. Set FOUNDRY_ENDPOINT and FOUNDRY_API_KEY in .env", "sources": []}

    context_str = json.dumps(context, indent=2)
    system_prompt = f"""You are Imperial Trade Sentinel, an AI agent for SADC trade logistics.
Answer the user's question using ONLY the provided imperial data context.
If the answer is not in the context, say so.
Cite specific values from the context.

Context: {context_str}"""

    chat_url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview"
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "max_tokens": 500,
        "temperature": 0.3
    }

    try:
        resp = requests.post(chat_url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            answer = data["choices"][0]["message"]["content"]
            return {"answer": answer, "sources": ["Azure AI Foundry with imperial context"]}
        else:
            return {"answer": f"API error: {resp.status_code} - {resp.text[:200]}", "sources": []}
    except Exception as e:
        return {"answer": f"Request failed: {str(e)}", "sources": []}

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Missing 'question' field"}), 400
    context = gather_context(question)
    iq_result = query_foundry_iq(question, context)
    return jsonify({
        "question": question,
        "answer": iq_result["answer"],
        "sources": iq_result["sources"],
        "imperial_context": {k: v for k, v in context.items() if v is not None}
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Imperial Trade Sentinel is online", "iq_ready": not os.getenv("USE_MOCK_IQ", "false").lower() == "true"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8123))
    app.run(host="0.0.0.0", port=port, debug=False)
