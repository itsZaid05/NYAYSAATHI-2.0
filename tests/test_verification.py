import hashlib
import json
from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError
from backend import providers
from backend.providers import (
    GeminiProvider,
    ProviderUnavailable,
    ReviewedLegalSources,
    UKCaseLawProvider,
)
from backend.schemas import (
    CaseAssessment,
    Extracted,
    Grounded,
    Option,
    Reasoning,
    Source,
)


@pytest.fixture
def reviewed(tmp_path, monkeypatch, client):
    root = tmp_path / "sources"
    (root / "knowledge/artifacts").mkdir(parents=True)
    text = "A TEST FIXTURE ONLY: consumer refund passage. This is not legal authority."
    data = text.encode()
    checksum = hashlib.sha256(data).hexdigest()
    (root / "knowledge/artifacts" / checksum).write_bytes(data)
    row = dict(
        source_id="TEST-ONLY",
        title="TEST ONLY — not a statute",
        provision="test fixture",
        exact_text=text,
        official_url="https://www.indiacode.nic.in/test-only-not-a-real-source",
        jurisdiction="IN",
        effective_version="fixture-v1",
        checked_at=datetime.now(timezone.utc).isoformat(),
        valid_from="2020-01-01",
        valid_until=None,
        reuse_rights="Synthetic test fixture only",
        status="reviewed",
        reviewed_by="automated fixture, not human legal review",
        artifact_sha256=checksum,
        artifact_mime="text/plain",
    )
    path = root / "knowledge/reviewed_sources.json"
    path.write_text(json.dumps([row]))
    monkeypatch.setattr(providers, "ROOT", root)
    return row, path


def test_exact_source_and_lexical_search(reviewed):
    row, path = reviewed
    p = ReviewedLegalSources()
    results, mode = p.search("refund consumer")
    assert len(results) == 1 and results[0].quote == row["exact_text"]
    assert "FTS5" in mode


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "pending"),
        ("reuse_rights", "pending review"),
        ("reviewed_by", ""),
        ("jurisdiction", "UK"),
        ("exact_text", "Fabricated content not in official artifact"),
        ("valid_from", "2099-01-01"),
        ("valid_until", "2000-01-01"),
        ("checked_at", "2000-01-01T00:00:00+00:00"),
        ("official_url", "https://evil.invalid/fake-law"),
        ("artifact_sha256", "0" * 64),
    ],
)
def test_bad_or_stale_sources_are_excluded(reviewed, field, value):
    row, path = reviewed
    row[field] = value
    path.write_text(json.dumps([row]))
    assert ReviewedLegalSources().search("consumer")[0] == []


def test_unknown_citation_and_paraphrase_are_rejected(client, intake_data):
    a = client.post("/api/cases/intake", json=intake_data).json()
    a["options"] = [
        dict(
            action="Read",
            conditions="test",
            caveats="test",
            source_ids=["made-up"],
            proposition="invented",
        )
    ]
    with pytest.raises(ValidationError):
        CaseAssessment.model_validate(a)
    a["sources"] = [
        dict(
            id="real-fixture",
            title="test",
            url="https://www.indiacode.nic.in/fixture",
            provision="test",
            version="fixture",
            checked_at=datetime.now(timezone.utc).isoformat(),
            quote="Exact test passage",
        )
    ]
    a["options"][0]["source_ids"] = ["real-fixture"]
    with pytest.raises(ValidationError):
        CaseAssessment.model_validate(a)


def test_gemini_grounding_and_hallucination_rejection(
    client, intake_data, reviewed, monkeypatch
):
    monkeypatch.setattr(
        GeminiProvider,
        "extract",
        lambda *args: Extracted(
            facts=[intake_data["narrative"]], timeline=[], unknowns=[], follow_up=""
        ),
    )
    monkeypatch.setattr(
        GeminiProvider,
        "reason",
        lambda *args: Reasoning(
            claims=[Grounded(source_id="fake", quote="invented legal claim")]
        ),
    )
    data = {**intake_data, "consent": {**intake_data["consent"], "ai_processing": True}}
    a = client.post("/api/cases/intake", json=data).json()
    assert a["sources"] and not a["options"]
    assert any("rejected" in f for f in a["safety_flags"])
    monkeypatch.setattr(
        GeminiProvider,
        "extract",
        lambda *args: Extracted(
            facts=["Invented purchase date"], timeline=[], unknowns=[], follow_up=""
        ),
    )
    a = client.post("/api/cases/intake", json=data).json()
    assert "Invented purchase date" not in str(a["facts"])
    assert "unavailable" in a["ai_status"]


def test_valid_gemini_claim_and_fake_claim_do_not_leak(
    client, intake_data, reviewed, monkeypatch
):
    row, _ = reviewed
    monkeypatch.setattr(
        GeminiProvider,
        "extract",
        lambda *args: Extracted(
            facts=[intake_data["narrative"]], timeline=[], unknowns=[], follow_up=""
        ),
    )
    monkeypatch.setattr(
        GeminiProvider,
        "reason",
        lambda *args: Reasoning(
            claims=[Grounded(source_id=row["source_id"], quote=row["exact_text"])]
        ),
    )
    data = {**intake_data, "consent": {**intake_data["consent"], "ai_processing": True}}
    a = client.post("/api/cases/intake", json=data).json()
    assert len(a["options"]) == 1
    assert a["options"][0]["proposition"] in a["sources"][0]["quote"]


def test_sensitive_input_never_calls_remote_model(client, intake_data, monkeypatch):
    def forbidden(*args):
        pytest.fail("Sensitive input reached Gemini")

    monkeypatch.setattr(GeminiProvider, "extract", forbidden)
    data = {
        **intake_data,
        "narrative": intake_data["narrative"] + " Email person@example.invalid",
        "consent": {**intake_data["consent"], "ai_processing": True},
    }
    assert client.post("/api/cases/intake", json=data).status_code == 200


def test_uk_provider_disabled():
    with pytest.raises(ProviderUnavailable):
        UKCaseLawProvider().search("anything")


def test_corrupt_manifest_abstains(reviewed):
    row, path = reviewed
    path.write_text("not valid json")
    assert ReviewedLegalSources().records == []


def test_real_gemini_adapter_with_mock_http_transport(client, monkeypatch):
    """Exercise actual request/parse paths; this is not a live Gemini account test."""
    import httpx
    from backend.config import settings

    monkeypatch.setattr(settings, "gemini_key", "synthetic-test-key")
    monkeypatch.setattr(settings, "gemini_model", "test-model")
    monkeypatch.setattr(settings, "terms_reviewed", True)
    monkeypatch.setattr(settings, "embedding_model", "test-embedding")
    GeminiProvider.verified_models.clear()
    calls = []

    def handle(request):
        calls.append(request.url.path)
        assert request.headers["x-goog-api-key"] == "synthetic-test-key"
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "name": "models/test-model",
                            "supportedGenerationMethods": ["generateContent"],
                        },
                        {
                            "name": "models/test-embedding",
                            "supportedGenerationMethods": ["embedContent"],
                        },
                    ]
                },
            )
        if "embedContent" in request.url.path:
            return httpx.Response(200, json={"embedding": {"values": [0.3, 0.4]}})
        data = json.loads(request.content)
        assert data["generationConfig"]["responseMimeType"] == "application/json"
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps(
                                        {
                                            "facts": ["Fictional refund"],
                                            "timeline": [],
                                            "unknowns": ["When?"],
                                            "follow_up": "When?",
                                        }
                                    )
                                }
                            ]
                        }
                    }
                ]
            },
        )

    real_client = httpx.Client
    monkeypatch.setattr(
        providers.httpx,
        "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handle), **kw),
    )
    p = GeminiProvider()
    result = p.extract("Fictional refund", "en", ["When?"])
    assert result.facts == ["Fictional refund"]
    assert p.embed(["test"]) == [[0.3, 0.4]]
    assert any("generateContent" in c for c in calls)

    def down(request):
        return httpx.Response(429, json={"error": "quota"})

    monkeypatch.setattr(
        providers.httpx,
        "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(down), **kw),
    )
    with pytest.raises(ProviderUnavailable):
        p.extract("test", "en", ["When?"])


def test_hybrid_retrieval_with_mock_embeddings(reviewed, monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "embedding_model", "test-embedding")
    monkeypatch.setattr(
        GeminiProvider,
        "embed",
        lambda self, texts, **kwargs: [[1.0, 0.5] for _ in texts],
    )
    results, mode = ReviewedLegalSources().search("refund", semantic=True)
    assert results and mode.startswith("hybrid")


def test_unsupported_request_does_not_invoke_ai(client, intake_data, monkeypatch):
    def forbidden(*args):
        pytest.fail("Unsupported jurisdiction/domain invoked Gemini")

    monkeypatch.setattr(GeminiProvider, "extract", forbidden)
    data = {
        **intake_data,
        "jurisdiction": "UK",
        "consent": {**intake_data["consent"], "ai_processing": True},
    }
    assert client.post("/api/cases/intake", json=data).json()["sources"] == []


def test_source_must_be_valid_for_stated_case_date(reviewed):
    provider = ReviewedLegalSources()
    assert provider.search("consumer refund", event_date="2010-01-01")[0] == []
    assert provider.search("consumer refund", event_date="2026-01-01")[0]


def test_embedding_outage_reports_lexical_fallback(reviewed, monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "embedding_model", "fixture-embedding")

    def unavailable(*args, **kwargs):
        raise ProviderUnavailable("Embedding timeout")

    monkeypatch.setattr(GeminiProvider, "embed", unavailable)
    results, mode = ReviewedLegalSources().search("consumer refund", semantic=True)
    assert results and mode.startswith("SQLite FTS5 lexical")
    assert "semantic service unavailable" in mode and not mode.startswith("hybrid")


def test_provider_timeout_and_rate_limit_keep_safe_error_details(client, monkeypatch):
    import httpx
    from backend.config import settings

    monkeypatch.setattr(settings, "gemini_key", "synthetic-test-key")
    monkeypatch.setattr(settings, "gemini_model", "test-model")
    monkeypatch.setattr(settings, "terms_reviewed", True)
    import hashlib, time

    GeminiProvider.verified_models[
        (hashlib.sha256(b"synthetic-test-key").hexdigest(), "test-model")
    ] = time.time()
    real_client = httpx.Client

    def limit(request):
        return httpx.Response(
            429,
            headers={"retry-after": "60"},
            json={"error": {"status": "RESOURCE_EXHAUSTED"}},
        )

    monkeypatch.setattr(
        providers.httpx,
        "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(limit), **kw),
    )
    with pytest.raises(ProviderUnavailable) as error:
        GeminiProvider().extract("Fictional laptop", "en", [])
    assert error.value.http_status == 429 and error.value.retry_after == "60"

    GeminiProvider.generation_cooldown_until = 0.0

    def timeout(request):
        raise httpx.ReadTimeout("synthetic transport timeout")

    monkeypatch.setattr(
        providers.httpx,
        "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(timeout), **kw),
    )
    with pytest.raises(ProviderUnavailable) as timeout_error:
        GeminiProvider().extract("Fictional laptop", "en", [])
    assert "ReadTimeout" in str(timeout_error.value)
    assert "synthetic transport timeout" not in str(timeout_error.value)
    assert GeminiProvider.generation_state["status"] == "transport_failure"
    assert GeminiProvider.generation_state["error_type"] == "ReadTimeout"
