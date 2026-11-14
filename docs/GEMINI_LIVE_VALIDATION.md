# Gemini live validation — 2026-11-14

All transmitted narratives and files were synthetic. The platform secret was used through the backend HTTPS route; no credential value was printed or committed. Real-user beta is gated.

## Actual account observations

| Check | Actual result |
|---|---|
| Model list with configured key | HTTP 200; adapter validation run received 50 model records |
| Configured `gemini-2.5-flash` generation | HTTP 404: provider says this model is not available to new users, despite listing it |
| Configured `gemini-embedding-2` | Absent from the observed model-list response |
| Listed `gemini-3.8-flash` minimal generation | HTTP 503, high demand; not claimed working |
| Listed stable `gemini-3.1-flash-lite` minimal generation | HTTP 200; JSON status response, 23 total tokens in the initial minimal check |
| Structured fictional intake via real adapter | PASS; seller and INR 45,000 extracted with exact provenance; supportive response and missing-date questions |
| Follow-up after supplied dates/platform | PASS; 3 timeline events; questions updated to remaining model/seller-response/evidence facts |
| Listed `gemini-embedding-001` | HTTP 200; direct output-dimension probe returned 768 values; adapter default returned **3072** values |
| Full browser → API → real Gemini intake/follow-up | PASS; persisted entities/history/timeline, generated lawyer brief and deletion exercised |
| Official-source grounded analysis | **BLOCKED**: no approved official passages; not substituted with synthetic law |
| Live hybrid retrieval over approved statutes | **BLOCKED** for the same reason; successful embedding alone is not hybrid RAG |
| Unsupported citation / entailment rejection | LOCAL VERIFIED with synthetic fixtures and mocked evaluator; not a live legal-correctness claim |
| Timeout / 429 Retry-After / embedding outage handling | LOCAL VERIFIED using controlled transport failures; real 503 observed separately |

## Reproducible commands

The saved environment variables were **not silently replaced**. These explicit runtime overrides select models that were actually exercised:

```bash
.venv/bin/python -m scripts.validate_live --model gemini-3.1-flash-lite --embedding-model gemini-embedding-001
.venv/bin/python -m scripts.run_demo --model gemini-3.1-flash-lite --embedding-model gemini-embedding-001 --port 8011
NYAY_TEST_URL=http://127.0.0.1:8011 node tests/live-browser.cjs
```

`runtime/live-validation/live-results.json` is the non-secret machine-readable result for model-list, minimal generation, structured intake, multi-turn follow-up and embeddings, with explicit blocked legal checks. The browser run used two real generation requests, not a mocked response. Screenshot: `runtime/live-intake-desktop.png` (local ignored artifact).

## Terms, pricing and quota

`GEMINI_TERMS_REVIEWED=true` is present as an operator acknowledgement, not independent proof of provider terms or an API quota entitlement. Public terms/pricing links now return HTTP 301 to `https://aistudio.google.com/docs/terms` and `/docs/pricing`; that destination is currently denied by the environment proxy. Its domain was added to the draft for review. No current price, paid plan, available account quota or consumer-subscription benefit is asserted.

Only minimal, explicitly authorised fictional testing was performed. Before expanding use, the operator must review current API data-handling terms, actual account billing and quotas. Demo session AI-context mutations are capped at 20 per hour independently of provider quota. Consent withdrawal/deletion remain possible when the budget is exhausted. No real confidential-data processing is enabled.

Hindi intake was also exercised against the real provider: it returned a supportive Hindi response, one seller, one amount, and Hindi purchase/delivery/fault-date questions. Native image OCR currently has only English/orientation language packs; this is separate from Gemini's bilingual conversation capability.
