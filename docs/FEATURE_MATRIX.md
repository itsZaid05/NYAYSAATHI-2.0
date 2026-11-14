# Feature gap matrix (audit before this implementation)

| Feature | Audit status | Gap / next implementation |
|---|---|---|
| Private cases, consent, handoff, PDFs | REAL AND TESTED | Preserve all working controls and regression coverage |
| Gemini generation | IMPLEMENTED BUT UNVERIFIED | Model list now succeeds; exercise generation, extraction and reasoning live |
| Legal corpus | BLOCKED | Empty; original candidate URL is invalid HTML; validate official artifacts/rights |
| Source ingestion | PARTIAL | Online exact-text importer only; add authenticated-provenance offline path and manifest |
| Hybrid retrieval | IMPLEMENTED BUT UNVERIFIED | Validate actual embeddings; configured embedding identifier absent from model list |
| Grounded legal explanations | NOT IMPLEMENTED | Existing code only selects exact passages; add supported, qualified propositions and independent evaluator |
| Conversational intake | PARTIAL | Fixed questions and literal snippets; add canonical entities, questions, history, corrections |
| Case workspace | PARTIAL | Case-specific overview/issues/actions/source links must update consistently |
| Stories | SIMULATED | One labelled fictional card; add original scenario library and relevant comparisons |
| Authentic precedent comparison | NOT IMPLEMENTED | Provider/UI boundary required; remain disabled without authorised verified judgments |
| Evidence | PARTIAL | TXT/PDF text only; add structured document provenance, contradictions and controlled OCR |
| Readiness | PARTIAL | Explain actual fact/evidence/source gaps instead of category-count proxy |
| Documents | PARTIAL | One seller template; add six preparation templates and independent text/PDF export |
| Bilingual/mobile UX | PARTIAL | Local labels and two tested paths; improve case-language persistence/loading/errors |
| Real-user beta | BLOCKED | Privacy/provider contracts, strong auth and legal/security review required |

This table will be replaced with final evidence-based delivery labels after validation. Audit labels are not claims that live legal integrations work.
