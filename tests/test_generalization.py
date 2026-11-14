import json
from pathlib import Path
import pytest
from backend.config import settings
from backend.providers import GeminiProvider, ProviderUnavailable
from backend.schemas import Extracted, ConsumerIssue, ModelProbe
from backend.services.case_state import ground_dynamic_extraction, narrative_segments


def extraction(
    text, category="subscription_billing", title="Recurring charges after cancellation"
):
    return Extracted(
        scope="consumer",
        issue_details=[
            ConsumerIssue(
                id="new-issue",
                category=category,
                title=title,
                fact_segment_ids=["f0"],
                unresolved_facts=["Was cancellation acknowledged?"],
                evidence_needed=["Cancellation acknowledgment and payment history"],
                research_terms=["recurring payment consent cancellation"],
            )
        ],
        assistant_message="I can help organise this disputed transaction.",
        facts=[],
        timeline=[],
        unknowns=["When was cancellation acknowledged?"],
        follow_up="When was cancellation acknowledged?",
    )


def test_novel_consumer_issue_reaches_ai_before_keyword_fallback(client, monkeypatch):
    text = "Fictional: Demo Fit keeps drawing INR 799 after acknowledging that my membership ended."
    from backend.engine import classify

    assert classify(text, "IN") == "needs_clarification"
    monkeypatch.setattr(GeminiProvider, "extract", lambda *args: extraction(text))
    data = {
        "narrative": text,
        "jurisdiction": "IN",
        "consent": {"processing": True, "fictional_demo": True, "ai_processing": True},
    }
    r = client.post("/api/cases/intake", json=data)
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["category"] == "subscription_billing" and a["scope_status"] == "consumer"
    assert a["issue_details"][0]["fact_quotes"] == [text]
    assert "Gemini multi-issue" in a["understanding_method"]
    restored = client.get(f"/api/cases/{a['case_id']}/assessment").json()
    assert (
        restored["category"] == "subscription_billing"
        and restored["issue_details"] == a["issue_details"]
    )


def test_multi_issue_and_incidental_police_mention(client, monkeypatch):
    text = "Fictional: Demo Net kept drawing money after cancellation. A support agent mentioned police, but my question concerns the paid connection."
    result = extraction(text)
    result.issue_details.append(
        ConsumerIssue(
            id="delivery",
            category="service_deficiency",
            title="Paid connection not delivered",
            fact_segment_ids=["f0"],
            research_terms=["deficiency paid service"],
            evidence_needed=["Outage tickets"],
        )
    )
    monkeypatch.setattr(GeminiProvider, "extract", lambda *args: result)
    a = client.post(
        "/api/cases/intake",
        json={
            "narrative": text,
            "consent": {
                "processing": True,
                "fictional_demo": True,
                "ai_processing": True,
            },
        },
    ).json()
    assert len(a["issue_details"]) == 2 and a["scope_status"] == "consumer"
    assert {i["category"] for i in a["issue_details"]} == {
        "subscription_billing",
        "service_deficiency",
    }


def test_segment_provenance_drops_paraphrased_summary_and_rejects_unknown_ids():
    text = "Fictional: Demo Shop kept my INR 1200 deposit."
    r = extraction(text)
    r.facts = ["A hallucinated person paid INR 9000."]
    grounded = ground_dynamic_extraction(r, text)
    assert grounded.facts == [] and grounded.issue_details[0].fact_quotes == [text]
    r.issue_details[0].fact_segment_ids = ["made-up"]
    with pytest.raises(ValueError):
        ground_dynamic_extraction(r, text)


def test_research_queries_cover_each_issue():
    from backend.services.retrieval import retrieve_for_issues

    queried = []

    class Corpus:
        def search(self, query, **kwargs):
            queried.append(query)
            return [], "lexical only"

    issues = [
        extraction("x").issue_details[0],
        ConsumerIssue(
            id="ads",
            category="misleading_advertising",
            title="Disputed marketing representation",
            fact_quotes=["Synthetic marketing promise"],
            evidence_needed=["Saved listing"],
            research_terms=["misleading advertisement representation"],
        ),
    ]
    found, mode = retrieve_for_issues(
        Corpus(), "Fictional case", issues, semantic=False
    )
    assert not found and len(queried) == 2
    assert (
        "recurring payment" in queried[0] and "misleading advertisement" in queried[1]
    )
    assert "multi-issue" in mode


def test_configuration_fallback_is_verified_and_reported(client, monkeypatch):
    from backend.services.model_configuration import verify_runtime_models

    monkeypatch.setattr(settings, "gemini_key", "synthetic-unit-placeholder")
    monkeypatch.setattr(settings, "terms_reviewed", True)
    monkeypatch.setattr(settings, "gemini_model", "old-unusable")
    monkeypatch.setattr(settings, "embedding_model", "old-embedding")
    monkeypatch.setattr(
        GeminiProvider,
        "models",
        lambda self: [
            {
                "name": "models/" + m,
                "supportedGenerationMethods": ["generateContent"]
                if "embedding" not in m
                else ["embedContent"],
            }
            for m in ["old-unusable", "gemini-3.1-flash-lite", "gemini-embedding-001"]
        ],
    )

    def generation(*args):
        if settings.gemini_model == "old-unusable":
            raise ProviderUnavailable("HTTP 404", http_status=404)
        return ModelProbe(status="ok")

    monkeypatch.setattr(GeminiProvider, "generate", generation)
    monkeypatch.setattr(GeminiProvider, "embed", lambda *args, **kwargs: [[0.4, 0.6]])
    p = verify_runtime_models()
    assert p["requested_generation"] == "old-unusable"
    assert (
        p["selected_generation"] == "gemini-3.1-flash-lite" and p["generation_verified"]
    )
    assert p["selected_embedding"] == "gemini-embedding-001" and p["embedding_verified"]
    assert any("404" in d for d in p["diagnostics"])
    assert not "synthetic-unit-placeholder" in json.dumps(p)


def test_permission_required_portals_cannot_be_marked_approved_by_nonempty_text():
    from backend.services.source_rights import validate_reuse

    for url in [
        "https://consumerhelpline.gov.in/public/knowledgebase",
        "https://nalsa.gov.in/legal-aid/",
    ]:
        with pytest.raises(ValueError):
            validate_reuse({"official_url": url, "reuse_rights": "Publicly visible"})
    assert validate_reuse(
        {
            "official_url": "https://consumerhelpline.gov.in/public/knowledgebase",
            "reuse_status": "documented_permission",
            "rights_evidence": "Synthetic unit-test grant identifier; not actual permission",
        }
    )
    with pytest.raises(ValueError):
        validate_reuse(
            {
                "official_url": "https://www.indiacode.nic.in/test",
                "review_schema": 2,
                "reuse_status": "unknown",
            }
        )


def test_new_evaluation_set_is_disjoint_and_covers_requested_domains():
    cases = json.loads(Path("tests/evaluation/unseen_consumer_cases.json").read_text())
    old = json.loads(Path("synthetic_demo/evaluation_cases.json").read_text())
    assert len(cases) >= 25 and len({c["id"] for c in cases}) == len(cases)
    assert not ({c["narrative"] for c in cases} & {c["narrative"] for c in old})
    assert {
        "refund_refusal",
        "defective_product",
        "misleading_advertising",
        "subscription_billing",
        "warranty",
        "service_deficiency",
    } <= set(x for c in cases for x in c["expected_issue_categories"])


def test_evidence_upload_preserves_novel_issue_state_without_new_model_call(
    client, monkeypatch
):
    text = "Fictional: Demo Fit keeps drawing INR 799 after acknowledging that my membership ended."
    monkeypatch.setattr(GeminiProvider, "extract", lambda *args: extraction(text))
    a = client.post(
        "/api/cases/intake",
        json={
            "narrative": text,
            "consent": {
                "processing": True,
                "fictional_demo": True,
                "ai_processing": True,
            },
        },
    ).json()
    cid = a["case_id"]

    def forbidden(*args):
        pytest.fail("Evidence upload or GET unexpectedly invoked Gemini")

    monkeypatch.setattr(GeminiProvider, "extract", forbidden)
    result = client.post(
        f"/api/cases/{cid}/evidence",
        data={"kind": "communication"},
        files={
            "file": (
                "cancel.txt",
                "Synthetic Demo Fit cancellation acknowledgment INR 799",
                "text/plain",
            )
        },
    )
    assert result.status_code == 200, result.text
    updated = result.json()["assessment"]
    assert (
        updated["category"] == "subscription_billing"
        and updated["issue_details"] == a["issue_details"]
    )
    assert updated["evidence_analysis"]
    assert (
        client.post(
            f"/api/cases/{cid}/draft", json={"kind": "refund_request"}
        ).status_code
        == 200
    )
    assert client.get(f"/api/cases/{cid}/packet.pdf").content.startswith(b"%PDF-")
    assert (
        client.get(f"/api/cases/{cid}/assessment").json()["category"]
        == "subscription_billing"
    )


def test_decoder_schema_is_compact_but_backend_contract_is_still_strict():
    from backend.services.provider_schema import decoder_schema
    from backend.schemas import Extracted

    schema = decoder_schema(Extracted)
    text = json.dumps(schema)
    assert "$ref" not in text and "$defs" not in text
    assert "subscription_billing" in text and "required" in schema
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ConsumerIssue(
            id="bad",
            category="warranty",
            title="Test title",
            fact_quotes=["test"],
            research_terms=["cover"],
            evidence_needed=[],
        )


def test_unrequested_remedy_is_not_promoted_to_user_facts():
    text = "Fictional: My Demo Chair split at the leg. I kept the receipt."
    result = extraction(
        text, category="defective_product", title="Possible product fault"
    )
    result.desired_remedy = "Refund"
    result.remedy_quote = ""
    grounded = ground_dynamic_extraction(result, text)
    assert grounded.desired_remedy == "" and grounded.remedy_quote == ""


def test_rate_limit_circuit_breaker_avoids_immediate_repeated_network_calls(
    client, monkeypatch
):
    import httpx, time, hashlib
    from backend import providers

    monkeypatch.setattr(settings, "gemini_key", "synthetic-quota-test")
    monkeypatch.setattr(settings, "gemini_model", "test-model")
    monkeypatch.setattr(settings, "terms_reviewed", True)
    GeminiProvider.verified_models[
        (hashlib.sha256(b"synthetic-quota-test").hexdigest(), "test-model")
    ] = time.time()
    calls = []
    real = httpx.Client

    def respond(req):
        calls.append(req.url.path)
        return httpx.Response(429, json={"error": {"details": [{"retryDelay": "2s"}]}})

    monkeypatch.setattr(
        providers.httpx,
        "Client",
        lambda **kw: real(transport=httpx.MockTransport(respond), **kw),
    )
    for _ in range(2):
        with pytest.raises(ProviderUnavailable) as error:
            GeminiProvider().generate("Synthetic test", {}, ModelProbe)
        assert error.value.http_status == 429
    assert len(calls) == 1


def test_decoder_constrains_evidence_to_real_segment_ids():
    from backend.services.provider_schema import decoder_schema

    schema = decoder_schema(
        Extracted, {"narrative_segments": {"f0": "Synthetic account"}}
    )
    issue = schema["properties"]["issue_details"]["items"]
    assert "fact_segment_ids" in issue["required"]
    assert issue["properties"]["fact_segment_ids"]["items"]["enum"] == ["f0"]
    assert "fact_quotes" not in issue["properties"]


def test_subscription_story_selection_uses_the_new_issue_family(client):
    from backend.services.scenario_engine import ScenarioEngine

    scenarios = ScenarioEngine().select(
        "Fictional ongoing monthly membership debit", "subscription_billing", "en", []
    )
    assert scenarios[0].id == "subscription"
    assert all(s.label == "Fictional illustration — not a judgment" for s in scenarios)
