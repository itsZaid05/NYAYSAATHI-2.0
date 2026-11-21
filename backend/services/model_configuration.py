"""Verify the actual account at startup; expose model fallback decisions instead of hiding them."""

import json
from datetime import datetime, timezone
from backend.config import settings
from backend.providers import GeminiProvider, ProviderUnavailable
from backend.schemas import ModelProbe

# These are the stable identifiers actually exercised in this repository's audit.
GENERATION_FALLBACK = "gemini-3.1-flash-lite"
EMBEDDING_FALLBACK = "gemini-embedding-001"


def verify_runtime_models():
    # A fresh probe supersedes historical success, including when catalogue
    # access fails before any generation request can be attempted.
    GeminiProvider.generation_state = {
        "ok": False,
        "model": settings.gemini_model,
        "status": "verification_pending",
    }
    profile = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "requested_generation": settings.gemini_model,
        "requested_embedding": settings.embedding_model,
        "selected_generation": None,
        "selected_embedding": None,
        "generation_verified": False,
        "embedding_verified": False,
        "diagnostics": [],
    }
    settings.model_configuration = profile
    if not (settings.gemini_key and settings.terms_reviewed):
        GeminiProvider.generation_state["status"] = "not_ready"
        profile["diagnostics"].append(
            "Backend key or operator terms acknowledgement missing; no transmission attempted."
        )
        return profile
    p = GeminiProvider()
    try:
        models = p.models()
    except ProviderUnavailable as exc:
        GeminiProvider.generation_state["status"] = "catalogue_unavailable"
        profile["diagnostics"].append(str(exc))
        return profile
    available = {
        m.get("name", "").removeprefix("models/"): m.get(
            "supportedGenerationMethods", []
        )
        for m in models
    }
    candidates = list(dict.fromkeys([settings.gemini_model, GENERATION_FALLBACK]))
    for candidate in candidates:
        if "generateContent" not in available.get(candidate, []):
            profile["diagnostics"].append(
                f"Configured/listed generation candidate {candidate!r} does not support generateContent."
            )
            continue
        settings.gemini_model = candidate
        try:
            result = p.generate(
                "Return status ok. This is a synthetic connectivity check, not a legal question.",
                {"fictional_test": True},
                ModelProbe,
            )
            profile["generation_verified"] = result.status == "ok"
            profile["selected_generation"] = candidate
            break
        except ProviderUnavailable as exc:
            profile["diagnostics"].append(f"{candidate}: " + str(exc))
            if exc.http_status in (401, 403, 429):
                break
    if not profile["generation_verified"]:
        profile["selected_generation"] = settings.gemini_model
        profile["diagnostics"].append(
            "No startup generation succeeded. The selected candidate is not live-verified; explicit retry or configuration repair is required."
        )
        return _save(profile)
    embeddings = list(dict.fromkeys([settings.embedding_model, EMBEDDING_FALLBACK]))
    original_embedding = settings.embedding_model
    for candidate in embeddings:
        if "embedContent" not in available.get(candidate, []):
            profile["diagnostics"].append(
                f"Embedding candidate {candidate!r} is absent or unsupported."
            )
            continue
        settings.embedding_model = candidate
        try:
            vector = p.embed(["Synthetic consumer-demonstration connectivity check"])[0]
            profile["selected_embedding"] = candidate
            profile["embedding_verified"] = True
            profile["embedding_dimensions"] = len(vector)
            break
        except ProviderUnavailable as exc:
            profile["diagnostics"].append(f"{candidate}: " + str(exc))
    if not profile["embedding_verified"]:
        settings.embedding_model = original_embedding
    if profile["selected_generation"] != profile["requested_generation"]:
        profile["diagnostics"].append(
            "Using the explicitly reported, live-verified audit model in memory; saved environment variables were not rewritten."
        )
    return _save(profile)


def _save(profile):
    settings.runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = settings.runtime / "provider-status.json"
    path.write_text(json.dumps(profile, indent=2) + "\n")
    path.chmod(0o600)
    return profile
