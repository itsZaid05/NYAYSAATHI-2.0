# Offline official-PDF review and ingestion

The legal-source gate remains closed: **zero approved passages**. There is no rights-cleared official Act/rules PDF available, and the existing project PDFs and invalid HTML candidate are not authority. The user-supplied `https://indiacode.gov.in/home` is an official starting point, not a verified document. Its request still returned proxy CONNECT 403 under the currently applied environment policy. No access settings were published or changed.

This workflow prepares an operator to add an independently verified official PDF later. It uses the existing source registry, artifact checks, FTS5, Gemini embedding cache and claim-verification pipeline. It adds no public ingestion endpoint, external fetch, automatic source approval or Gemini transmission. All commands below run from the repository root with the project's existing virtual environment.

## 1. Stage a candidate privately

When an authorised candidate PDF becomes available, use a private directory under ignored `runtime/`:

```bash
.venv/bin/python -m scripts.offline_sources stage /private/official-document.pdf --output runtime/source-review/document-v1.json
```

The command checks the PDF header, size, parseability, encryption, page count and searchable text. It calculates a consistency checksum and prepares exact section candidates with advisory page hints. Non-numbered guidance falls back to page candidates with blank provisions. Every passage and every document review starts **pending**. It does not copy anything into `knowledge/artifacts/` or `knowledge/reviewed_sources.json`. JSON output is private (0600) and existing output files are never overwritten.

A checksum calculated from the local PDF proves consistency, not authenticity. A `.pdf` filename, government-looking URL, project PDF or successful parse does not establish law. Image-only or encrypted PDFs are rejected. Automatic OCR is not used to establish legal text. Candidates can cross pages or include imperfect section boundaries: the reviewer must correct them against the original. Long indivisible clauses are preserved, not silently truncated; approved source quotes must fit the existing 16,000-character source limit.

## 2. Record independent review

Edit the generated JSON; never approve a pack merely to clear validation errors. Leave the gate closed when evidence is unavailable.

| Field/group | Required review |
|---|---|
| `artifact` | Independently authenticate the official artifact and compare its recorded checksum; do not change the generated hash to conceal a file substitution. |
| `document` | Supply the actual title, specific authoritative document URL, IN jurisdiction, source type, effective version, validity dates and timezone-aware retrieval time. A portal homepage alone is insufficient provenance evidence. |
| `provenance` | Record an identified reviewer, approval, timezone-aware review time and evidence of official origin/acquisition. |
| `version` | Record approval, reviewer/time and evidence covering commencement, amendments, consolidation status, relevant exceptions and temporal applicability. Do not assume an original Act PDF is current. |
| `reuse` | Record approval, reviewer/time and the actual permission, licence or independently reviewed statutory reproduction basis. Public accessibility alone is insufficient. |
| `document.reuse_status` / `reuse_rights` | Choose the established basis and document its conditions. Do not assume the software grants or interprets rights. |
| `document.permitted_uses` | Explicitly clear `retention`, `local_search`, `external_embeddings`, `llm_context`, and `quotation_and_export`. The current pipeline needs all five; a local-only grant cannot silently enable Gemini transmission or PDF quotation. If any use remains unclear, keep the pack pending. |
| Each selected `passages[].review` | Verify the exact complete passage/provision, context, exceptions and relevance; record approval, reviewer/time and substantive review evidence. Set `excluded: true` for unwanted candidates. Pending, rejected and excluded passages are not imported. |

Reviews require nonblank reviewer identities and substantive evidence, timezone-aware timestamps, and review within the past 90 days. Re-running an import does not refresh a manual review: the source check date remains the earliest applicable review time, with a separate artifact-check timestamp. Future reviews, stale reviews, missing metadata, invalid/inverted/expired/future validity intervals, duplicate IDs and text absent from the retained PDF fail validation. These checks verify consistency and recorded attestations; they cannot establish authenticity, legal correctness, rights or professional qualifications by themselves. Use versioned, unique source IDs; an existing ID is blocked rather than overwritten automatically.

The review evidence/rights conditions may be sensitive: keep the pack and associated proof in authorised private storage. Corpus records retain the review text and decisions for operator audit, so supply appropriate references/summaries rather than private credentials or entire confidential permission documents.

## 3. Validate without changing retrieval

```bash
.venv/bin/python -m scripts.offline_sources check runtime/source-review/document-v1.json /private/official-document.pdf --report runtime/source-review/document-v1-check.json
```

`check` does not write to the corpus, artifact store, FTS index, embedding cache or Gemini. A requested report is a new private file; choose a new report filename on subsequent runs. Exit 0 means technical checks and recorded approvals are complete; **it does not grant rights or certify law**. Exit 2 means the gate remains closed. Reports show approved/pending/excluded counts and the blocking condition; fix it and check again. Pending candidates may remain in the pack while a reviewed subset is selected.

## 4. Import only after genuine approval exists

Only the responsible reviewer, after the independent checks above, should run:

```bash
.venv/bin/python -m scripts.offline_sources import runtime/source-review/document-v1.json /private/official-document.pdf --attest-reviewed-provenance-version-and-rights --report runtime/source-review/document-v1-import-check.json
```

**Do not run this now with project PDFs or synthetic demonstration records.** The flag is an explicit attestation, not an approval bypass. Import revalidates the artifact and every selected passage, then serialises concurrent operator imports, retains the checksum-named artifact and atomically replaces the registry. A rejected passage batch cannot partially enter the corpus. If the registry replacement fails after an artifact write, an unreferenced artifact can remain; it is never indexed without an approved registry record. Disk/backup durability and parsing isolation remain operational responsibilities.

On its next request the existing provider reads the updated registry, checks exact text/checksum/rights/version freshness, and rebuilds FTS5. No frontend or RAG rebuild is necessary. Semantic document vectors are generated lazily through the existing adapter only when AI processing is actually authorised/configured, and are cached by model/content/version. Claim verification and uncertainty gates remain in place. Source admission is not approval of an AI interpretation.

The existing `scripts.import_offline_source` single-record command remains available with `--dry-run`; new imports now require review schema 2, provenance/version/reuse evidence, explicit pipeline-use clearance, and current review timestamps. The individual online importer uses those same admission checks. Previously retained records are not silently reapproved or rewritten by this change. For corrections/new versions, prepare new versioned IDs and review how older records should be withdrawn; this workflow does not automatically decide supersession.

## Verify after genuine admission

Check `/api/health` and individual `/api/sources/{id}` records, then run the authentic-source acceptance gate:

```bash
NYAY_TEST_URL=http://127.0.0.1:8011 node tests/generalized-browser.cjs --require-grounded
```

It currently remains blocked with zero approved passages. Once real material is admitted it requires accepted claims, matching artifact hashes and source/quote/fact references, frontend official links, evidence guidance, documents/PDF and demo handoff. Independent substantive legal review is still required; AI self-agreement and exact quotations alone do not prove correct applicability.
