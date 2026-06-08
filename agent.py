#!/usr/bin/env python3
"""
Imperial Trade Sentinel - Microsoft Agents League Submission
Track: Reasoning Agents (Foundry IQ)
Integrates with Microsoft Foundry IQ for grounded, cited answers.
"""

import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from functools import lru_cache
import time

load_dotenv()

app = Flask(__name__)

# ========== Configuration ==========
FOUNDRY_ENDPOINT = os.getenv("FOUNDRY_ENDPOINT", "https://api.foundry.microsoft.com/v1")
FOUNDRY_API_KEY = os.getenv("FOUNDRY_API_KEY")
USE_MOCK_IQ = os.getenv("USE_MOCK_IQ", "false").lower() == "true"

# Imperial internal service endpoints (all running on localhost)
IMPERIAL_SERVICES = {
    "portfolio": "http://localhost:8124/api/value",
    "trade_volume": "http://localhost:8124/api/volume",
    "lithium": "http://localhost:8124/api/lithium",
    "wealth_lock": "http://localhost:8124/api/wealth_lock",
    "bi_summary": "http://localhost:8124/api/summary",
    "system_status": "http://localhost:8124/api/status",
}

# ========== Data Fetching from Imperial Stack ==========
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
    if USE_MOCK_IQ or not FOUNDRY_API_KEY:
        return {
            "answer": f"Based on the provided data, {question[:100]}... (mock IQ response. Replace with real Foundry IQ call.)",
            "sources": ["Imperial internal telemetry"]
        }
    payload = {
        "query": question,
        "context": json.dumps(context),
        "grounding": True,
        "max_tokens": 500
    }
    headers = {
        "Authorization": f"Bearer {FOUNDRY_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(f"{FOUNDRY_ENDPOINT}/query", json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "answer": data.get("answer", "No answer"),
                "sources": data.get("sources", [])
            }
        else:
            return {"answer": f"IQ error: {response.status_code}", "sources": []}
    except Exception as e:
        return {"answer": f"Failed to reach Foundry IQ: {str(e)}", "sources": []}

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
    return jsonify({"status": "Imperial Trade Sentinel is online", "iq_ready": not USE_MOCK_IQ and bool(FOUNDRY_API_KEY)})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8123))
    app.run(host="0.0.0.0", port=port, debug=False)
