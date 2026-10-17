# Repository Audit (2026-10-17)
## Stack
Static SPA: `index.html`(1927 lines), `app.js`(2047), `style.css`(4019), no build, Chart.js+FontAwesome CDN, en-IN formatting. Python: `main.py` CLI only (no web server despite fastapi in requirements), `models/hybrid_rag_model.py` (FAISS+BM25+CrossEncoder+OpenAI), `config/settings.py`. No tests, no DB, no auth, no migrations.
## Execution path
Login is cosmetic (`startDemo`) → SPA pages (dashboard, intake, story-mode, case-summary, marketplace, documents, analytics, ai-insights, policies, settings, help) → all data from hardcoded `DemoData`/`AppState` in app.js, `simulateApiDelay`, toasts. **Frontend never calls the Python RAG** — no fetch() to any backend. Python path: CLI → loads 306 Indian cases → FAISS/BM25 → OpenAI `gpt-4o-mini`.
## Critical findings
1. **Leaked credential**: a Google-format API key (`AIza...`, mislabelled OPENAI_API_KEY) hardcoded in `.env`, `config/settings.py` (as env fallback), `models/hybrid_rag_model.py:61`. **Must be revoked/rotated by owner; it is in git history — removal from HEAD does not purge history.**
2. Fabricated-looking dataset (see DATASET_AUDIT.md): success_percentage, lawyer_success_rate, estimated costs presented as fact.
3. Fake lawyers (Indian, ₹ fees, "cases_won"), fake analytics KPIs, hardcoded intake verdict ("workplace harassment, medium risk") regardless of input.
4. Claims: "end-to-end encryption", "no data stored" — unimplemented. XSS risk: user text interpolated into innerHTML in chat.
5. Analytics page = user-facing demo analytics → **removed per spec §4** (operational audit logging kept server-side, content-free).
6. requirements.txt pins heavy/unused deps (langchain, transformers, faiss) unused by web app; old model broken-by-design (semantic score normalisation bug: `1-d/max` with first distance, sorted() on tuples reverse lexicographic).
## Preserved
Visual design, page hierarchy, intake chat pattern, case-summary tabs, story mode, marketplace & documents UI shells — re-wired to real API, UK content.
