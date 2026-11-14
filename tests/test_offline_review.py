"""All documents and review attestations here are SYNTHETIC, in temporary roots only."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pypdf import PdfWriter
from weasyprint import HTML

from backend import providers
from backend.providers import GeminiProvider, ReviewedLegalSources
from backend.services.offline_review import (
    ReviewPack,
    check_pack,
    inspect_pdf,
    prepare_records,
    stage_pdf,
    write_new_json,
)
from scripts.import_offline_source import import_reviewed_batch


@pytest.fixture
def synthetic_pdf(tmp_path, monkeypatch):
    # No real law, actual provenance approval or provider traffic is used by these tests.
    def no_ai(*args, **kwargs):
        raise AssertionError("Offline review must never transmit to Gemini")

    for method in ["models", "generate", "embed"]:
        monkeypatch.setattr(GeminiProvider, method, no_ai)
    path = tmp_path / "synthetic-only.pdf"
    HTML(
        string="<h1>1. TEST ONLY refund records</h1><p>This fictional fixture describes organising refund paperwork. It is not law.</p><h1>2. TEST ONLY service records</h1><p>This fictional fixture describes keeping service correspondence. It is not law.</p>"
    ).write_pdf(path)
    return path


def approved_pack(path):
    pack = stage_pdf(path)
    now = datetime.now(timezone.utc)
    pack.document.title = "SYNTHETIC TEST PDF - NOT LAW"
    pack.document.official_url = (
        "https://indiacode.gov.in/test-only-not-an-official-document"
    )
    pack.document.source_type = "statute"
    pack.document.effective_version = "SYNTHETIC TEST VERSION - NOT A REAL STATUTE"
    pack.document.valid_from = now.date() - timedelta(days=3)
    pack.document.retrieved_at = now - timedelta(minutes=1)
    pack.document.reuse_status = "reviewed_statutory_basis"
    pack.document.reuse_rights = "Synthetic test fixture; not genuine rights clearance"
    pack.document.permitted_uses = [
        "retention",
        "local_search",
        "external_embeddings",
        "llm_context",
        "quotation_and_export",
    ]
    for review in [pack.provenance, pack.version, pack.reuse] + [
        p.review for p in pack.passages
    ]:
        review.status = "approved"
        review.reviewed_by = "SYNTHETIC TEST REVIEWER - NOT A LEGAL REVIEW"
        review.reviewed_at = now
        review.evidence = "Synthetic fixture evidence only; never authentic source or permission evidence."
    return pack


def test_stage_private_pending_pack_without_index_mutation(synthetic_pdf, tmp_path):
    pack = stage_pdf(synthetic_pdf)
    assert len(pack.passages) == 2
    assert (
        pack.artifact.sha256 == hashlib.sha256(synthetic_pdf.read_bytes()).hexdigest()
    )
    assert all(
        p.review.status == "pending" and p.page_hints == [1] for p in pack.passages
    )
    assert pack.document.reuse_status == "pending_review"
    target = tmp_path / "private" / "review.json"
    write_new_json(target, pack.model_dump(mode="json"))
    assert target.stat().st_mode & 0o777 == 0o600
    assert ReviewPack.model_validate_json(target.read_text()) == pack
    with pytest.raises(FileExistsError):
        write_new_json(target, {"overwrite": "forbidden"})
    root = tmp_path / "empty-root"
    result = check_pack(pack, synthetic_pdf, root)
    assert result["ready"] is False and result["mutated_corpus"] is False
    assert not root.exists()


@pytest.mark.parametrize(
    "kind", ["html", "broken_pdf", "empty", "image_only", "encrypted"]
)
def test_invalid_pdf_rejected_before_staging(tmp_path, kind):
    path = tmp_path / "invalid.pdf"
    if kind == "html":
        path.write_text("<html>Error page, not a statute</html>")
    elif kind == "broken_pdf":
        path.write_bytes(b"%PDF-1.7\nbroken")
    elif kind == "empty":
        path.write_bytes(b"")
    else:
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        if kind == "encrypted":
            writer.encrypt("synthetic-secret")
        with path.open("wb") as f:
            writer.write(f)
    with pytest.raises(ValueError):
        inspect_pdf(path)


def test_oversized_input_rejected_before_reading(tmp_path):
    path = tmp_path / "too-large.pdf"
    with path.open("wb") as f:
        f.truncate(20 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="20 MB"):
        inspect_pdf(path)


@pytest.mark.parametrize(
    "defect",
    [
        "rights_pending",
        "reuse_rejected",
        "version_pending",
        "missing_provenance",
        "naive_review",
        "stale_review",
        "future_review",
        "unknown_origin",
        "missing_title",
        "missing_version",
        "future_version",
        "inverted_dates",
        "quote_absent",
        "duplicate_ids",
        "artifact_changed",
        "missing_passage_review",
        "unknown_document_type",
        "wrong_page_hint",
        "unreviewed_external_use",
    ],
)
def test_incomplete_or_invalid_review_never_changes_corpus(
    synthetic_pdf, tmp_path, defect
):
    pack = approved_pack(synthetic_pdf)
    now = datetime.now(timezone.utc)
    if defect == "rights_pending":
        pack.document.reuse_status = "pending_review"
    elif defect == "reuse_rejected":
        pack.reuse.status = "rejected"
    elif defect == "version_pending":
        pack.version.status = "pending"
    elif defect == "missing_provenance":
        pack.provenance.evidence = ""
    elif defect == "naive_review":
        pack.version.reviewed_at = now.replace(tzinfo=None)
    elif defect == "stale_review":
        pack.version.reviewed_at = now - timedelta(days=91)
    elif defect == "future_review":
        pack.version.reviewed_at = now + timedelta(days=1)
    elif defect == "unknown_origin":
        pack.document.official_url = "https://example.invalid/not-authority"
    elif defect == "missing_title":
        pack.document.title = ""
    elif defect == "missing_version":
        pack.document.effective_version = ""
    elif defect == "future_version":
        pack.document.valid_from = now.date() + timedelta(days=1)
    elif defect == "inverted_dates":
        pack.document.valid_until = pack.document.valid_from - timedelta(days=1)
    elif defect == "quote_absent":
        pack.passages[
            0
        ].exact_text = "This passage was invented and does not occur in the PDF."
    elif defect == "duplicate_ids":
        pack.passages[1].source_id = pack.passages[0].source_id
    elif defect == "artifact_changed":
        pack.artifact.sha256 = "0" * 64
    elif defect == "missing_passage_review":
        for p in pack.passages:
            p.review.status = "pending"
    elif defect == "unknown_document_type":
        pack.document.source_type = "unspecified"
    elif defect == "wrong_page_hint":
        pack.passages[0].page_hints = [200]
    elif defect == "unreviewed_external_use":
        pack.document.permitted_uses = ["retention", "local_search"]
    root = tmp_path / "target"
    result = check_pack(pack, synthetic_pdf, root)
    assert not result["ready"] and not result["mutated_corpus"]
    assert result["errors"] and not root.exists()


def test_validation_does_not_expose_raw_invalid_source_field(synthetic_pdf, tmp_path):
    pack = approved_pack(synthetic_pdf)
    pack.document.official_url = "https://private-review-phrase.example.invalid/"
    result = check_pack(pack, synthetic_pdf, tmp_path / "target")
    assert not result["ready"]
    assert "private-review-phrase" not in json.dumps(result)


def test_dry_run_and_batch_admission_feed_existing_hybrid_pipeline(
    synthetic_pdf, tmp_path, monkeypatch, client
):
    pack = approved_pack(synthetic_pdf)
    root = tmp_path / "source-checkout"
    report = check_pack(pack, synthetic_pdf, root)
    assert report["ready"] and report["counts"]["approved"] == 2 and not root.exists()
    rows = prepare_records(pack, synthetic_pdf)
    # Entire batch is validated before anything reaches the retained corpus.
    rows[-1]["exact_text"] = (
        "This fabricated passage does not occur in the synthetic artifact."
    )
    with pytest.raises(ValueError):
        import_reviewed_batch(rows, synthetic_pdf, root)
    assert not root.exists()
    rows = prepare_records(pack, synthetic_pdf)
    admitted = import_reviewed_batch(rows, synthetic_pdf, root)
    registry = root / "knowledge/reviewed_sources.json"
    before = registry.read_bytes()
    assert len(admitted) == 2 and registry.stat().st_mode & 0o777 == 0o600
    monkeypatch.setattr(providers, "ROOT", root)
    loader = ReviewedLegalSources()
    assert len(loader.records) == 2
    sources, mode = loader.search("refund")
    assert sources and "refund" in sources[0].quote.lower() and "FTS5" in mode
    assert sources[0].title.startswith("SYNTHETIC")
    calls = []

    def fixture_embed(self, texts, **kwargs):
        calls.extend(texts)
        return [[1.0, 0.0] if "refund" in t.lower() else [0.0, 1.0] for t in texts]

    monkeypatch.setattr(GeminiProvider, "embed", fixture_embed)
    sources, mode = loader.search("refund", semantic=True)
    assert "hybrid" in mode and "refund" in sources[0].quote.lower()
    assert (
        len(calls) == 3
    )  # Two document vectors and one query, in the private test database.
    loader.search("refund", semantic=True)
    assert (
        len(calls) == 4
    )  # Documents cached, query remains live in the adapter contract.
    assert registry.read_bytes() == before
    with pytest.raises(ValueError, match="already exists"):
        import_reviewed_batch(rows, synthetic_pdf, root)
    assert registry.read_bytes() == before


def test_only_approved_nonexcluded_passages_are_admitted(synthetic_pdf, tmp_path):
    pack = approved_pack(synthetic_pdf)
    pack.passages[1].excluded = True
    rows = prepare_records(pack, synthetic_pdf)
    assert len(rows) == 1
    root = tmp_path / "target"
    import_reviewed_batch(rows, synthetic_pdf, root)
    assert len(json.loads((root / "knowledge/reviewed_sources.json").read_text())) == 1


def test_atomic_registry_failure_preserves_prior_registry(
    synthetic_pdf, tmp_path, monkeypatch
):
    import scripts.import_offline_source as importer

    root = tmp_path / "target"
    (root / "knowledge").mkdir(parents=True)
    registry = root / "knowledge/reviewed_sources.json"
    registry.write_text("[]\n")
    before = registry.read_bytes()
    original = importer.os.replace

    def fail_registry(source, destination):
        if Path(destination) == registry:
            raise OSError("Synthetic disk failure")
        return original(source, destination)

    monkeypatch.setattr(importer.os, "replace", fail_registry)
    with pytest.raises(OSError, match="Synthetic disk failure"):
        import_reviewed_batch(
            prepare_records(approved_pack(synthetic_pdf), synthetic_pdf),
            synthetic_pdf,
            root,
        )
    assert registry.read_bytes() == before
    assert not list((root / "knowledge").glob(".source-*"))


def test_cli_check_is_nonmutating_and_import_needs_attestation(
    synthetic_pdf, tmp_path, monkeypatch, capsys
):
    from scripts import offline_sources

    pack = approved_pack(synthetic_pdf)
    path = tmp_path / "approved-test-pack.json"
    write_new_json(path, pack.model_dump(mode="json"))
    root = tmp_path / "target"
    monkeypatch.setattr(offline_sources, "ROOT", root)
    monkeypatch.setattr(
        "sys.argv", ["offline_sources", "check", str(path), str(synthetic_pdf)]
    )
    assert offline_sources.main() == 0 and not root.exists()
    monkeypatch.setattr(
        "sys.argv", ["offline_sources", "import", str(path), str(synthetic_pdf)]
    )
    with pytest.raises(SystemExit) as error:
        offline_sources.main()
    assert error.value.code == 2 and not root.exists()
    monkeypatch.setattr(
        "sys.argv",
        [
            "offline_sources",
            "import",
            str(path),
            str(synthetic_pdf),
            "--attest-reviewed-provenance-version-and-rights",
        ],
    )
    assert offline_sources.main() == 0
    assert len(json.loads((root / "knowledge/reviewed_sources.json").read_text())) == 2


def test_concurrent_operator_batches_do_not_lose_reviewed_records(
    synthetic_pdf, tmp_path
):
    from concurrent.futures import ThreadPoolExecutor

    root = tmp_path / "target"
    rows = prepare_records(approved_pack(synthetic_pdf), synthetic_pdf)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(import_reviewed_batch, [row], synthetic_pdf, root)
            for row in rows
        ]
        for future in futures:
            assert len(future.result()) == 1
    stored = json.loads((root / "knowledge/reviewed_sources.json").read_text())
    assert {row["source_id"] for row in stored} == {row["source_id"] for row in rows}
    assert len(list((root / "knowledge/artifacts").iterdir())) == 1


def test_import_does_not_extend_manual_review_freshness(synthetic_pdf, tmp_path):
    pack = approved_pack(synthetic_pdf)
    previous_review = datetime.now(timezone.utc) - timedelta(days=89)
    for review in [pack.provenance, pack.version, pack.reuse] + [
        p.review for p in pack.passages
    ]:
        review.reviewed_at = previous_review
    rows = import_reviewed_batch(
        prepare_records(pack, synthetic_pdf), synthetic_pdf, tmp_path / "target"
    )
    assert all(
        datetime.fromisoformat(row["checked_at"]) == previous_review for row in rows
    )
    assert all(
        datetime.fromisoformat(row["artifact_checked_at"]) > previous_review
        for row in rows
    )
