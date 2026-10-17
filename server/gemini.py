"""Gemini adapter (server-side only).

Key handling: read ONLY from host environment (GEMINI_API_KEY or LLM_API_KEY).
Never from repo files, never sent to the browser, never logged.
Data minimisation: only verified propositions + source passages are sent to
the model. The user's original narrative is NEVER sent.
"""
import os, json, urllib.request
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
SYSTEM = ("Rewrite the given verified legal-information propositions in clear, empathetic UK English. "
          "Rules: introduce NO new legal claims, cases, statutes, dates, probabilities, costs or outcomes; "
          "keep every citation exactly as a bracketed source URL from the input; if unsure, keep the original wording.")
def api_key(): return os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY", "")
def model_name(): return os.getenv("LLM_MODEL_EXPLANATION") or os.getenv("LLM_MODEL", "")
def enabled(): return bool(api_key() and model_name())
def parse_response(payload: dict) -> str:
    try:
        parts = payload["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()
    except Exception:
        return ""
def gemini_client(propositions_json: str) -> str:
    """Callable matching server.llm.polish(client=...). Sends propositions only."""
    body = {"system_instruction": {"parts": [{"text": SYSTEM}]},
            "contents": [{"parts": [{"text": propositions_json}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 900}}
    req = urllib.request.Request(API.format(model=model_name()), data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key()}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return parse_response(json.loads(r.read().decode()))
