# Legal source manifest — 2026-11-14

**Approved legal passages: 0. Independently reviewed judgments: 0.** The legal-intelligence acceptance gate remains blocked. Neither generated text nor synthetic test fixtures have been inserted into `knowledge/reviewed_sources.json`.

## Actual source investigations

| Resource | Observed result | Decision |
|---|---|---|
| Old India Code homepage, https://www.indiacode.nic.in/ | HTTP 200 HTML announces migration to https://indiacode.gov.in/ | Retained research evidence outside corpus; link is not an Act |
| Previously configured CPA PDF URL, `/bitstream/123456789/15256/1/a2019-35.pdf` | HTTP 200 **HTML**, title “Invalid URL or Argument(s)”; PDF parser correctly rejects it | Excluded; HTTP success alone is insufficient |
| https://indiacode.gov.in/ | Proxy CONNECT 403; migrated domain absent from running policy | New domain addition saved in draft, not applied/published by agent |
| https://consumeraffairs.nic.in/ and legacy CPA document link | HTTP 503 | No statute or reuse conditions verified |
| NCH https://consumerhelpline.gov.in/public/ and `/public/knowledgebase` | HTTP 200; individual pages inspected, links point to Department site | Useful portal/link validation only; copyrighted guidance not indexed without rights review |
| NCH link to https://consumeraffairs.gov.in/ | Identifies current Department domain | New official domain addition saved in draft; no content assumed |
| Older India Code alternate PDF and search | Timed out | Excluded; no unchanged retry loop |

New requested domains preserve existing grants: `indiacode.gov.in`, `www.indiacode.gov.in`, `consumeraffairs.gov.in`, `www.consumeraffairs.gov.in`, and `aistudio.google.com` (current Gemini terms/pricing redirect). No publication occurred. These additions need application through environment settings before a fresh connection can establish access.

## Corpus metadata contract

Every approved passage must retain `source_id`, title, provision, **exact_text**, authoritative URL, jurisdiction, effective version, valid-from/until dates, retrieval/check timestamps, artifact checksum and MIME, source type, documented reuse basis, reviewer/verification method, and evidence of provenance. The provider rechecks the artifact checksum, exact text, jurisdiction, dates and 90-day freshness. Retrieval also filters explicit case dates. Approval does not establish substantive legal correctness.

`knowledge/review_queue.json` contains **36 unapproved review targets**, not 36 legal sources. Relevant current rules, e-commerce requirements and procedural guidance still need to be added after authentic source and rights review. No qualified human legal reviewer has assessed the new interpretations, and none is implied.

## Online and offline review paths

Online: obtain a specific artifact and review version/rights; run the existing individual `scripts.review_source` importer. It uses verified HTTPS and restricted official hosts. Never bulk scrape or index a site's copyrighted guidance merely because the page is public.

Offline: a reviewer may supply an authentic official PDF/HTML acquired through an authorised environment. Prepare a record with all fields above plus `expected_sha256`, `provenance_attestation`, `provenance_evidence`, `reviewed_by`, `retrieved_at` and `source_type`. Then:

```bash
.venv/bin/python -m scripts.import_offline_source /private/review-record.json /private/official-artifact.pdf --attest-official-provenance-and-rights
```

The flag is an attestation by the identified reviewer, **not** automated authentication. The importer rejects absent provenance, future/naive retrieval times, checksum mismatches, unsupported formats and passages absent from the artifact. A local filename or plausible URL is insufficient evidence of authenticity.

Section-aware candidate preparation is available without approving anything:

```bash
.venv/bin/python -m scripts.prepare_passages /private/official-artifact.pdf --mime application/pdf --output /private/review-candidates.json
```

It preserves exact text and section boundaries and marks every candidate pending. A long indivisible clause is not silently truncated. A human must verify content, exceptions, commencement/amendments, reuse and applicability before import.

## Interpretation boundary

Legal explanations now require structured source/quote mappings, fact provenance, qualified applicability and a **separate Gemini support-evaluation call**. Unsupported citations, invented facts, outcome guarantees and failed/unavailable support verdicts are rejected. This independent prompt is still an AI check; it does not replace independent legal review or prove statutory entailment. This path is tested with explicitly synthetic fixtures and remains **unverified with authentic law** until the corpus exists.

Authentic precedent providers (India and future UK) remain disabled. The 16 original scenario cards are fictional learning material, never judgments. The 306 legacy records remain quarantined.

## Current source/reuse recheck

On this iteration the migrated India Code request still failed at proxy CONNECT 403; its already-saved draft domain remains unapplied. The legacy candidate returns invalid HTML, not an Act. The legacy Department endpoint returns 503. Recovered workspace/upload locations contained no supplied authentic official PDF to use as an offline substitute.

NCH's actual disclaimer was inspected at https://consumerhelpline.gov.in/public/disclaimer and requires prior reproduction permission. NALSA's https://nalsa.gov.in/website-policies/ similarly requires prior permission and excludes third-party rights from any grant. These findings, timestamps and response hashes are recorded in `knowledge/source_access_reviews.json`; their content has not been inserted into legal retrieval. The importer/provider now reject these portal sources without an explicit documented grant/evidence. A public page is not silently treated as licensed.

`docs/SOURCE_REUSE_REQUEST.md` contains a concrete request draft for the operator to review; **it was not sent**. For a statute obtained from another authoritative publisher, separately establish its actual reproduction basis and compilation conditions. Applying a network grant does not itself clear reuse, amendments, commencement or legal interpretation.

The source count remains **0**. Independent legal applicability assessment is consequently **NOT PERFORMED**. Current claim checks provide deterministic provenance safeguards plus a separately prompted AI support signal; that signal is explicitly not professional legal review or proof of legal correctness.
