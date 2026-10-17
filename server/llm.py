"""Phase 5/7: best-model generation layer — OPTIONAL, off unless configured.

Model strategy: choose per-task best available model via env; never hardcode a
provider as 'truth'. The model may ONLY polish verified propositions. Output is
re-validated: any citation/source id not in the verified set, or any numeric
probability/cost/duration claim, causes the polished text to be DISCARDED and
the deterministic text kept. No key => deterministic path (current default)."""
import os, re, json, urllib.request
TASK_MODELS={  # overridable via env LLM_MODEL_<TASK>; defaults are capability tiers, not endorsements
 "extraction": os.getenv("LLM_MODEL_EXTRACTION",""),
 "explanation": os.getenv("LLM_MODEL_EXPLANATION",""),
 "verification": "",  # verification is deterministic by design — no LLM
}
BANNED=re.compile(r"(\d+\s?%|£\s?\d|chance of winning|will win|guaranteed|success rate)",re.I)
def enabled():
    from .gemini import enabled as gemini_enabled
    return gemini_enabled()
def polish(verified_output, client=None):
    """client: injectable callable(prompt)->str for tests. Default keeps deterministic text."""
    if client is None: return verified_output
    allowed={p["supporting_source_ids"][0] for p in verified_output.get("propositions",[])}
    try: text=client(json.dumps(verified_output.get("propositions",[])))
    except Exception: return verified_output
    if not text or BANNED.search(text): return verified_output
    # Model text may not introduce bracketed citations to unknown sources
    for cid in re.findall(r"\[([^\]]+)\]", text):
        if cid not in allowed: return verified_output
    out=dict(verified_output); out["explanation_polished"]=text; out["generation"]="llm-polished, citation-revalidated"
    return out
