# Offline ingestion validation — 2026-11-14

Starting commit: `4d3d4ee`, branch `feature/generalized-consumer-analysis`. No authentic legal material or rights approval was supplied. The production registry remains **0 passages**, unchanged SHA-256 `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`.

## Actual results

| Check | Observed result |
|---|---|
| `XDG_CACHE_HOME=runtime/cache /workspace/nyay-consumer-venv/bin/python -m pytest -q` | **140 passed**, no skips, one upstream Starlette/AnyIO deprecation warning |
| `NYAY_TEST_URL=http://127.0.0.1:8011 node tests/browser.cjs` | PASS: original intake/follow-up, four evidence uploads, readiness, editable draft, PDF, story, persistent reload, consent-based separate demo-lawyer receipt/revocation, three viewports, Hindi and deletion; no page errors |
| Actual CLI `offline_sources stage` with a newly generated **synthetic, not-law PDF** | Exit **0**; one unapproved candidate; output created privately |
| Actual CLI `offline_sources check` on that pending pack | Exit **2**; blocked by missing provenance approval; `mutated_corpus=false` |
| Actual CLI `offline_sources import` on that pending pack | Exit **2**; no passage admitted; registry checksum unchanged |
| `https://indiacode.gov.in/home` | Actual proxy CONNECT **403**; migrated domain remains outside applied policy revision 1 |
| `/api/health` after tests | `status=ok`, `reviewed_sources=0`, `demo_only=true` |

The CLI rehearsal is retained privately at `runtime/offline-review-smoke-qwbu8dfo/smoke-result.json`. It contains only synthetic-workflow evidence; no real permission or law. The first test run caught two output-creation failures from an unsupported `Path.open` argument; the writer was corrected and private/exclusive-file tests subsequently passed.

## What is tested

The 33 additional test instances use clearly synthetic PDFs and review attestations in temporary directories. They cover pending staging without index mutation, exclusive 0600 output, HTML masquerading as PDF, malformed/empty/image-only/encrypted/oversized inputs, missing/rejected/stale/future reviews, unknown origin, missing title/version, invalid effective dates, quote tampering, duplicate IDs, changed PDF checksum, missing passage approval, unknown source type, invalid page hints and absent external-use permission.

A complete synthetic pack is validated without writes, then batch-imported only into a temporary checkout. The existing provider loads those rows without pipeline changes, returns FTS5 matches, and uses a **mocked synthetic embedding adapter** to establish hybrid ranking and vector-cache reuse. These are not authentic sources, actual embedding calls or legal-correctness results. Other tests establish approved-subset selection, explicit CLI attestation, duplicate-ID rejection, original-registry preservation on a simulated disk failure, no lost records during concurrent operator imports, and no extension of manual-review freshness when an importer is rerun.

The real registry was not populated and the existing project PDFs/invalid HTML candidate were not used as authority. No staged law was transmitted to Gemini. No source-grounded legal accuracy claim or independent professional legal review is made.

See [OFFLINE_INGESTION.md](OFFLINE_INGESTION.md) for the future operator workflow. Source acquisition, independent provenance/version review and appropriate reuse rights remain prerequisites. Parsing/reviewer-metadata checks alone do not establish any of them.
