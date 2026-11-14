Current offline workflow: [OFFLINE_INGESTION.md](OFFLINE_INGESTION.md). All staged candidates remain pending. New imports require review schema 2, recorded provenance/version/rights evidence and explicit clearance for every pipeline use. There is still no authentic approved corpus.

# Sources, rights and verification

## Legal authority inventory
**No official legal passage has been successfully fetched and manually reviewed in this environment.** `knowledge/reviewed_sources.json` is deliberately empty. The application abstains from statutory conclusions. `knowledge/review_queue.json` lists 36 provision-review targets, not verified law; empty quote/version/review fields cannot be indexed.

India Code's candidate Consumer Protection Act PDF request (`https://www.indiacode.nic.in/bitstream/123456789/15256/1/a2019-35.pdf`) returned proxy CONNECT 403. Its document contents and current amendments/commencement have not been independently verified. Do not interpret the candidate URL or provision-topic checklist as a validated source pack.

Official starting points (links only, no ingested content):

| Portal | Purpose | Content / rights status |
|---|---|---|
| https://www.indiacode.nic.in/ | Statutes, amendments and official legal texts | Individual document, version, commencement and reproduction review required |
| https://consumerhelpline.gov.in/ | National Consumer Helpline information | Current guidance and website reuse terms need review |
| https://e-jagriti.gov.in/ | Consumer commission portal | Forms, jurisdiction rules and current procedures need direct review |
| https://consumeraffairs.nic.in/ | Department guidance, rules and notifications | Specific artifact and reuse review required |
| https://nalsa.gov.in/ | Legal-aid information/referral | Current eligibility and guidance need direct review |

No portal has been bulk scraped, indexed for model training or treated as automatically licensed. No automated live judgment provider is enabled. `UKCaseLawProvider.enabled=False` until applicable licensing, provider terms and jurisdiction requirements are approved.

## Review workflow
1. An appropriately qualified reviewer identifies a specific official artifact and the applicable version, commencement, amendments and validity period. Record reproduction permission or the actual legal/contractual basis; do not just write “public website”.
2. Copy a short exact passage into an individual JSON record. Required fields: `source_id`, `title`, `provision`, `exact_text`, `official_url`, `jurisdiction` (IN), `effective_version`, `valid_from` (ISO date), optional `valid_until`, `reuse_rights` (documented rationale/conditions), `reviewed_by`, `reviewed_at`, `retrieved_at`, `source_type`, `review_schema: 2`, `provenance_attestation`, `provenance_evidence`, `version_evidence`, `reuse_status`, `rights_evidence`, and `permitted_uses` covering retention, local search, external embeddings, LLM context and quoted exports. Offline records also require `expected_sha256` and `artifact_mime`. Prefer the generated review pack to assembling these fields manually. The script supplies `checked_at`, `artifact_sha256`, `artifact_mime` and `status` after checks.
3. Run `python -m scripts.review_source /private/path/record.json --confirm-manual-review`. This performs an individual size-limited HTTPS fetch, checks each redirect against approved official hosts, rejects non-matching exact text, and saves the source artifact by checksum. It never grants rights automatically. Review this source/control change in Git.
4. The provider reads the registry on its next request; no frontend or RAG rebuild is needed. Sources must have correct jurisdiction, nonempty reviewer/rights, exact text matching retained artifact, valid dates and a check within the past 90 days. Stale, future, altered, missing or unreviewed sources are excluded, including on assessment reads and packet generation. Retrieval also excludes passages whose recorded validity period does not include the earliest explicitly stated case event date. This conservative filter cannot establish substantive temporal applicability.
5. Collect approximately 30–60 reviewed passages covering relevant definitions, remedies, procedures and applicable current rules/notifications. The current 36-item Act review queue alone is insufficient: add verified rules and procedural guidance before release. Validate each output's applicability and legal explanation with independent review.

`Option.source_ids` must resolve to actual retrieved sources. Legal propositions are restricted to exact substrings of a retrieved passage. This is a conservative traceability guard, **not a legal entailment, interpretation or applicability guarantee**. Gemini cannot introduce a new section or unsupported legal paraphrase. Current reasoning selects relevant exact passages; richer legal interpretation remains deliberately limited.

## Synthetic material
The legacy JSON is quarantined under `synthetic_demo/legacy_unverified_cases.json`: 306 actual records vs 305 metadata. Generic names, missing source URLs and unsupported outcome/cost/duration metrics make it unsuitable as authority. No authentic judgment reuse rights are established. Do not ingest it. New evaluation cases and story cards are labelled fictional, and synthetic test-only “source” fixtures are confined to temporary test directories. Unit verification tests do not establish genuine legal correctness.

## Gemini and privacy (current validation)

The published environment now supplies a ready Gemini binding and model/terms variables. Actual generation and embeddings were exercised using fictional data with explicit runtime model overrides; the saved model settings were not silently replaced. See GEMINI_LIVE_VALIDATION.md for provider errors, successful calls, exact commands and current terms/pricing access limitations. Source-grounded legal reasoning still has no genuine approved corpus and is not claimed live verified.

The separate support evaluator provides another AI check, not qualified human legal review. No pricing amount or account quota entitlement has been inferred from a consumer subscription. Use fictional narratives and synthetic documents only. Checkbox consent, provenance checks and regex screening cannot prove that material is fictional or fully anonymous. Real-user beta remains gated. See LEGAL_SOURCE_MANIFEST.md for the current source investigation and reviewer-controlled offline artifact import; the earlier domain-denial notes above describe the initial onboarding attempt.
