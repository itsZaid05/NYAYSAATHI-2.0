"""Canonical state, support verification, document/OCR and offline provenance contracts."""

import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import pytest
from PIL import Image, ImageDraw, ImageFont
from pydantic import ValidationError
from backend.providers import GeminiProvider, ProviderUnavailable
from backend.schemas import (
    Entity,
    IntakeIntelligence,
    LegalAnalysis,
    LegalClaim,
    ClaimVerdict,
    SupportEvaluation,
)
from backend.services.case_state import structured_local, validate_intelligence
from backend.services.citation_verification import verify
from backend.services.scenario_engine import ScenarioEngine
from scripts.import_offline_source import import_reviewed


def test_provenance_and_relative_dates():
    ref = datetime(2026, 11, 14, 10, tzinfo=timezone.utc)
    text = "Fictional: I bought a laptop from Demo Seller for INR 45000 last Tuesday. It failed yesterday."
    context, timeline = structured_local(text, "en", ref)
    assert context.parties[0].value == "Demo Seller"
    assert context.amounts[0].value == "INR 45000"
    assert [x.date for x in timeline] == ["2026-11-10", "2026-11-13"]
    assert all("Asia/Kolkata" in x.date_basis for x in timeline)
    invalid = IntakeIntelligence(
        assistant_message="Test",
        parties=[Entity(value="Invented Seller", quote="Invented Seller")],
    )
    with pytest.raises(ValueError):
        validate_intelligence(invalid, text)


def test_corrections_conversation_language_and_withdrawal(
    client, intake_data, monkeypatch
):
    a = client.post("/api/cases/intake", json=intake_data).json()
    cid = a["case_id"]
    assert len(a["conversation"]) == 2
    corrected = "Fictional: I bought a laptop from Corrected Seller on 2026-10-02 for INR 45000. It failed on 2026-10-05. I want a refund."
    r = client.patch(
        f"/api/cases/{cid}/context", json={"narrative": corrected, "language": "hi"}
    )
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["language"] == "hi"
    assert a["parties"][0]["value"] == "Corrected Seller"
    assert a["timeline"][0]["date"] == "2026-10-02"
    assert a["conversation"][-1]["role"] == "correction"
    assert client.get(f"/api/cases/{cid}/assessment").json()["parties"] == a["parties"]
    r = client.patch(f"/api/cases/{cid}/consent", json={"ai_processing": False})
    assert r.status_code == 200 and r.json()["consent"]["ai_processing"] is False
    assert client.post(f"/api/cases/{cid}/analyse").status_code == 422


@pytest.mark.parametrize(
    "kind",
    [
        "seller_representation",
        "refund_request",
        "grievance_summary",
        "chronology",
        "evidence_inventory",
        "lawyer_brief",
    ],
)
def test_six_editable_document_templates(client, intake_data, kind):
    cid = client.post("/api/cases/intake", json=intake_data).json()["case_id"]
    r = client.post(f"/api/cases/{cid}/draft", json={"kind": kind})
    assert r.status_code == 200, r.text
    draft = next(d for d in r.json()["drafts"] if d["kind"] == kind)
    assert "NOT FILED" in draft["content"]
    assert client.get(f"/api/cases/{cid}/drafts/{draft['id']}.txt").status_code == 200
    assert client.get(f"/api/cases/{cid}/drafts/{draft['id']}.pdf").content.startswith(
        b"%PDF-"
    )
    r = client.post(
        f"/api/cases/{cid}/draft",
        json={"kind": kind, "content": "Edited fictional text for " + kind},
    )
    assert next(d for d in r.json()["drafts"] if d["kind"] == kind)[
        "content"
    ].startswith("Edited")


def test_documents_are_preserved_by_kind(client, intake_data):
    cid = client.post("/api/cases/intake", json=intake_data).json()["case_id"]
    client.post(f"/api/cases/{cid}/draft", json={"kind": "chronology"})
    r = client.post(f"/api/cases/{cid}/draft", json={"kind": "evidence_inventory"})
    assert {d["kind"] for d in r.json()["drafts"]} == {
        "chronology",
        "evidence_inventory",
    }


def test_original_scenarios_are_relevant_and_labelled(client):
    rows = json.loads(Path("knowledge/scenarios/consumer.json").read_text())
    assert 12 <= len(rows) <= 20 and len({r["id"] for r in rows}) == len(rows)
    laptop = ScenarioEngine().select(
        "Fictional laptop will not start", "defective_product", "en", []
    )[0]
    delivery = ScenarioEngine().select(
        "Order delivery marked delivered parcel missing", "online_shopping", "hi", []
    )[0]
    assert laptop.id == "laptop" and delivery.id == "delivery"
    assert laptop.id != delivery.id
    assert all(
        s.label == "Fictional illustration — not a judgment" for s in [laptop, delivery]
    )
    assert not laptop.source_ids
    assert client.get("/api/precedents/status").json()["enabled"] is False


def test_local_ocr_and_evidence_provenance(client, intake_data):
    import shutil

    if not shutil.which("tesseract"):
        pytest.skip("Tesseract is an optional native OCR capability")
    cid = client.post("/api/cases/intake", json=intake_data).json()["case_id"]
    image = Image.new("RGB", (1500, 400), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    draw.text(
        (40, 40),
        "FICTIONAL INVOICE\nOrder: DEMO-101\nINR 45000\n2026-10-01",
        font=font,
        fill="black",
    )
    data = io.BytesIO()
    image.save(data, format="PNG")
    r = client.post(
        f"/api/cases/{cid}/evidence",
        data={"kind": "invoice"},
        files={"file": ("fictional.png", data.getvalue(), "image/png")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["extraction"] == "local OCR"
    a = r.json()["assessment"]
    doc = a["evidence_analysis"][0]
    assert "DEMO-101" in " ".join(doc["transaction_references"])
    assert "45000" in " ".join(doc["amounts"])
    assert any(
        f["document_id"] == doc["document_id"]
        for f in a["facts"]
        if f["origin"] == "document_excerpt"
    )
    assert "not a probability" in " ".join(a["readiness_flags"])


def test_offline_import_requires_authenticated_provenance(tmp_path):
    artifact = tmp_path / "fixture.txt"
    artifact.write_text(
        "TEST ONLY legislative passage: refund terms. Not real legal authority."
    )
    row = dict(
        source_id="OFFLINE-TEST",
        title="Synthetic importer test",
        provision="fixture",
        exact_text=artifact.read_text(),
        official_url="https://www.indiacode.nic.in/test-only",
        jurisdiction="IN",
        effective_version="fixture",
        valid_from="2020-01-01",
        reuse_rights="Synthetic test only",
        reviewed_by="Test reviewer",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        source_type="statute",
        provenance_attestation="Synthetic test attestation only",
        provenance_evidence="Test fixture, not an official source",
        expected_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
        artifact_mime="text/plain",
    )
    root = tmp_path / "checkout"
    (root / "knowledge").mkdir(parents=True)
    imported = import_reviewed(row, artifact, root)
    assert imported["artifact_sha256"] == row["expected_sha256"]
    row["expected_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        import_reviewed(row, artifact, root)
    row.pop("provenance_attestation")
    with pytest.raises(ValueError):
        import_reviewed(row, artifact, root)


def test_entailment_rejects_quote_matching_but_unsupported_application(client):
    from backend.schemas import Source

    source = Source(
        id="test-only",
        title="Synthetic fixture",
        url="https://www.indiacode.nic.in/test-only",
        provision="test",
        version="fixture",
        checked_at=datetime.now(timezone.utc),
        quote="TEST ONLY: a consumer may ask for a response. This is not law.",
    )
    claim = LegalClaim(
        id="bad",
        proposition="The consumer is guaranteed a full refund.",
        source_ids=["test-only"],
        supporting_quotes=["a consumer may ask for a response"],
        application="A refund is guaranteed.",
        fact_quotes=["Fictional laptop"],
        conditions=["None"],
        unknowns=[],
        suggested_action="Demand guaranteed payment",
        qualification="This is only a test fixture, not real legal advice.",
    )

    class Evaluator:
        def evaluate_support(self, *args):
            return SupportEvaluation(
                verdicts=[
                    ClaimVerdict(
                        claim_id="bad",
                        supported=False,
                        reason="The quote does not guarantee a remedy",
                    )
                ]
            )

    accepted, verdicts = verify(
        LegalAnalysis(overview="Test", claims=[claim]),
        [source],
        "Fictional laptop",
        Evaluator(),
    )
    assert not accepted.claims and not verdicts[0].supported
    claim.fact_quotes = ["invented fact"]

    class Forbidden:
        def evaluate_support(self, *args):
            pytest.fail("Invalid provenance reached evaluator")

    assert not verify(
        LegalAnalysis(overview="Test", claims=[claim]),
        [source],
        "Fictional laptop",
        Forbidden(),
    )[0].claims


def test_model_timeout_and_embedding_failure_are_explicit(
    client, intake_data, monkeypatch
):
    def timeout(*args):
        raise ProviderUnavailable("Gemini timeout; no AI output accepted")

    monkeypatch.setattr(GeminiProvider, "extract", timeout)
    data = {**intake_data, "consent": {**intake_data["consent"], "ai_processing": True}}
    a = client.post("/api/cases/intake", json=data).json()
    assert "unavailable" in a["ai_status"] and any(
        "timeout" in s for s in a["safety_flags"]
    )


def test_section_candidates_do_not_become_approved_law():
    from backend.services.source_chunking import section_candidates

    text = "1. Test title\nTEST ONLY first provision.\n\n2. Another test title\nTEST ONLY second provision."
    candidates = section_candidates(text)
    assert len(candidates) == 2
    assert all(c["status"] == "pending_manual_review" for c in candidates)
    assert all(c["exact_text"] in text for c in candidates)


def test_real_user_beta_cannot_be_silently_enabled(client, intake_data, monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "processing_mode", "real-user-beta")
    assert client.post("/api/cases/intake", json=intake_data).status_code == 503
