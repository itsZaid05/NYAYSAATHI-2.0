# Current Gemini live validation — 2026-11-14

Actual calls used the securely injected backend key and synthetic data only. No API key value was printed or committed. `GEMINI_TERMS_REVIEWED` is the operator's acknowledgement; current terms, paid-plan entitlement and quota availability are not inferred from a consumer subscription.

## Configuration and startup

Ordinary `python -m scripts.run_demo --port 8011` now verifies actual account access with a synthetic startup probe, rather than relying on manual flags or model-list presence:

- The saved generation setting `gemini-2.5-flash` appears in the catalogue but actual generation returns HTTP 404 for this account.
- The previously exercised stable audit fallback `gemini-3.1-flash-lite` passed actual generation and is selected **with visible diagnosis**, in memory. Saved environment variables are not rewritten.
- Catalogue pagination revealed `gemini-embedding-2` beyond the original first-page result. Actual current embedding calls succeeded with 3072-dimensional vectors, so the operator's working embedding setting is retained. The previous report's “absent” observation was only first-page visibility, not proof of account-wide unavailability. `gemini-embedding-001` remains the previously verified fallback and an explicit evaluation option.
- `/api/health` separates configuration, actual observations, current quota cooldown and live availability. Its model configuration is also saved without secrets to private `runtime/provider-status.json`. A missing key/terms acknowledgement causes no model transmission; failed probes do not become readiness claims.

`GEMINI_VERIFY_ON_START=true` is the default. Set false only to deliberately skip live probing for a local/offline environment; it does not verify a model. A restarted process must establish fresh observations rather than assuming old connections survive.

## Actual live testing

Thirty new consumer narratives were sent to the provider, including Hindi, mixed issues, subscriptions and misleading representations. The frozen expectations were never included in prompts. Initial failures exposed fact-paraphrase, ungrounded-remedy and JSON-shape defects. The final implementation:

1. Uses a compact, inlined provider decoder schema (the initial complex schema returned HTTP 400).
2. Keeps full Pydantic type/bound checks after generation.
3. Constrains issue/entity source-segment IDs to the actual narrative; backend reconstructs exact provenance.
4. Discards model summaries as canonical facts and does not infer a requested remedy without its excerpt.
5. Requires case-specific evidence suggestions and multi-issue research terms.

Live full rounds scored 9/30 then 20/30 on all strict checks; the targeted recheck produced the final latest-per-case total **23/30** strict passes, with **30/30** dynamic understanding/provenance/evidence-suggestion checks. Seven secondary-label misses remain. This is not legal-correctness validation; see UNSEEN_EVALUATION.md.

A separately entered gardening-plan billing narrative passed actual frontend → Gemini → context/evidence → document/PDF → authenticated demo recipient → persistence/revocation/deletion checks. It did not use a predefined example button. The law segment remains blocked because the approved legal corpus is empty.

## Failure behavior and quotas

Actual HTTP 429 free-tier throttling and a transient HTTP 503 occurred. The provider now reads Retry-After/RetryInfo, activates a bounded cooldown and avoids immediate duplicate generation attempts. Evaluation stops its sequential run at quota cooldown instead of claiming unattempted cases passed. Controlled tests cover timeout, malformed JSON, quota handling and embedding outage. No unbounded retry loop or verification bypass was introduced.

The public terms/pricing URLs redirect to `aistudio.google.com`, still outside the applied allowlist. Its grant is already saved in the draft. No current price or guaranteed account capacity is asserted. Consult the operator account and provider terms before expanding traffic or processing anything other than fictional data.

## Reproduce

```bash
.venv/bin/python -m scripts.run_demo --port 8011
.venv/bin/python -m scripts.evaluate_unseen --live --workers 1 --model gemini-3.1-flash-lite --embedding-model gemini-embedding-001 --output runtime/unseen-recheck.json
NYAY_TEST_URL=http://127.0.0.1:8011 node tests/generalized-browser.cjs
```

Hybrid retrieval, grounded legal explanations and legal applicability over authentic reviewed statutes are **BLOCKED**, not credited by successful embeddings or AI self-agreement.

The authenticated provider-recheck endpoint was actually exercised: HTTP 200 with successful generation and embedding probes. A prior startup 503 and its failed browser attempt remain recorded as failures; a later complete live browser journey passed. Current availability now uses the latest completed request status, rather than allowing an old success observation to mask a failed new probe.

One later intake request failed with the then-combined transport/response-envelope diagnostic despite successful connectivity probes. Its exact cause cannot be reconstructed from that safe summary. Reporting now separates transport exception class from malformed response without retaining sensitive error text. The final complete unseen browser rerun passed afterward; all failures remain explicitly recorded in TEST_REPORT.md. A minimal successful connectivity check does not guarantee every subsequent request succeeds.
