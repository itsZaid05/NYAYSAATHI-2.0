# Repository audit — 2026-11-14

Target: `itsZaid05/NYAYSAATHI-2.0`, original HEAD `59e02877e928c5b53295bf60593ae4f3f3a790d5`; implementation branch `feature/india-consumer-workflow`.

## Observed baseline
- Frontend: one 1,927-line HTML page, 4,019-line stylesheet, 2,047-line JavaScript file. No React, Tailwind, package manifest, bundler or frontend tests. Purple/cream brand, welcome role selection, dashboard, intake, story, summary, lawyers, documents, AI insights, policies, settings and help navigation are reusable.
- All data lives in a JavaScript DemoData constant; uploads, lawyer connections, document extraction and generated advice report simulated successes. Analytics, lawyer win counts, ratings and response metrics are unsupported. No real chat/API connection.
- Backend: `main.py` interactive CLI, `models/hybrid_rag_model.py` eagerly creates SentenceTransformer, cross encoder, FAISS and BM25. No HTTP endpoints, authentication, database, sessions, persistence or migrations. No Gemini integration.
- Broken baseline: Pydantic 2.0.0 conflicts with FastAPI 0.103.0. Python 3.12 is incompatible with several old pins. RAG contains ambiguous NumPy truth-value tests, wrong tuple/list indexing and incorrect OpenAI response access. Embedded credential-like material in settings/model must be removed; its owner should rotate it, including any history exposure.
- Dataset: 106 consumer + 110 family + 90 property = **306** records. Metadata says 305. No independently validated judgment provenance. Entire dataset quarantined under `synthetic_demo/`, excluded from retrieval and static serving.
- `.env` tracked at baseline; values were not copied into docs. New code uses backend process environment only. No usable GEMINI_API_KEY, GEMINI_MODEL or demo lawyer password is present.
- No test suite, CI, migrations, deployment or build tooling found. No AGENTS.md found.

## Implementation decisions
Retain vanilla frontend and original CSS tokens/navigation rather than introduce React migration risk. One FastAPI process, SQLite with FTS5 (small demonstrator, no existing PostgreSQL to reuse), validated Pydantic contracts and disk persistence outside public assets. Optional real Gemini REST extraction and embeddings; local rule-based preparation explicitly labelled. No fake AI responses or invented legal citations. Only reviewed source records can enter retrieval; source availability/rights gates remain closed until reviewed official content can be obtained.

## External access observed
Git HTTPS read works. India Code PDF request returned proxy CONNECT 403. Official-law access, Gemini model availability/pricing/quota and credentials cannot currently be verified. These are release blockers for the complete grounded-AI demonstration, not evidence that fabricated or unreviewed content is acceptable. Remaining local workflows will be implemented and tested independently.
