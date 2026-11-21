# NyaySaathi: detailed solution explanation

Prepared on 22 November 2026 (Asia/Kolkata) from the existing implementation, its recorded tests, the user's narrative and the supplied ten-page project presentation. This explains the product and its limits; it is not legal guidance for a real dispute.

## 1. The problem and the first useful outcome

A person experiencing a dispute may not know what facts matter, what to preserve or how to explain the sequence to someone who can help. An unstructured chat can sound reassuring while still leaving the person with no reliable record, missing evidence and an unclear next step.

NyaySaathi's immediate outcome is a persistent, reviewable case-preparation workspace. It should help answer: What did the user actually say? What is still unknown? What documents are available? What questions should be investigated? What can be prepared for a seller or human professional?

The founder's examples of bullying, scam threats, harassment, domestic violence and uncertainty abroad explain the broader motivation. They are not evidence that the current consumer prototype can safely analyse those domains. The initial supported research area is Indian consumer protection. Unsupported jurisdictions/categories are qualified or referred onward instead of receiving invented statutory advice.

## 2. The actual user journey

Consider a **fictional example**, not a judgment or tested legal conclusion:

> I ordered a phone online from Demo Seller for INR 18,000. The parcel arrived on 2026-11-10 with an empty box. I have the order confirmation, payment receipt and a delivery photograph. On 2026-11-12 I asked the seller to return my payment; it refused and told me to contact the courier. What information should I organise?

The system should organise the alleged transaction and disputed payment return without deciding who is liable. Missing questions may concern the platform, packaging/unboxing record, seller's exact response, delivery details and the user's requested resolution. The invoice amount and dates must come from the narrative/documents, not a plausible model completion.

The user can correct the narrative, add supporting documents, review suggested evidence, prepare an editable seller representation and download a packet. A separate action can share a snapshot with the demonstration recipient. None of these actions proves an allegation, establishes an entitlement, engages an advocate or files a government complaint.

## 3. Intake is structured understanding, not just a chat response

The frontend calls a real FastAPI endpoint. Privacy/scope gates run before external processing. Gemini is used only when configuration, operator acknowledgement, case consent and fictional-data conditions permit it; unsupported/sensitive input and provider failure remain qualified.

The multi-issue review asks the model to examine eight factual families separately: defective goods, disputed money return, marketing representations, subscription billing, express cover/warranty promises, digital transaction context, purchased-service shortfalls and another distinct consumer concern. Each receives present, unclear or not-stated status. This reduces the tendency to compress a faulty product plus a cover dispute into one label.

A positive finding needs original narrative segment IDs, a case-specific explanation, evidence suggestions and research terms. The backend resolves IDs to the user's exact words. Unknown IDs, inconsistent scope and missing review families fail validation. An incomplete individual finding can be withheld without discarding other grounded concerns.

This protects provenance, not truth or perfect classification. A model can still attach an unsupported category to a real quotation. The recorded refund-inference failure illustrates why factual evaluation and human correction remain necessary. No benchmark case ID or expected answer is supplied to the runtime prompt.

## 4. State, chronology and corrections

Pydantic validates the response structures. SQLite stores the case, full redacted narrative, relevant entities, facts, events, questions, evidence and conversation. New fields have defaults so previously saved cases remain readable.

Explicit dates and a small supported relative-date vocabulary are reconstructed against a visible case reference/timezone; ambiguous dates remain questions. This is not a general natural-language date parser or a limitation-period calculator. A selected entity must appear in its cited narrative segment. Paraphrased model summaries are not promoted into original user facts, and a refund/replacement request is not inferred merely because a purchase went wrong.

Context and evidence-analysis fingerprints are separate. Uploading a document can update preparation findings without erasing the previously grounded understanding of a novel issue. Reading a saved assessment also rechecks source eligibility rather than keeping an expired citation alive indefinitely.

## 5. The legal RAG design and the closed gate

Retrieval-augmented generation means retrieving external material and supplying it as context to a general model at request time. It is different from training or fine-tuning a model on judgments. This project has not trained a legal predictor or fine-tuned Gemini on case outcomes.

The existing retrieval path combines SQLite FTS5 lexical ranking with optional Gemini document/query embeddings and rank fusion. Research is decomposed by factual issue so one long allegation does not dominate the entire source pack. The workflow bounds the final pack at up to eight passages. Embedding vectors are cached by source content/version and model; a new approved corpus can enter that path without rebuilding the UI or retrieval engine.

A genuine source record needs the exact passage, authoritative document URL, jurisdiction, effective version/validity, review information, artifact checksum and established reuse basis. The private offline workflow stages only candidates; provenance, version and reuse reviews plus selected-passage approval must be recorded before explicit atomic admission. A local hash confirms consistency, not official origin. Source approval and permission are not generated by software.

**Current approved legal passages: zero.** The old Act candidate is invalid HTML, migrated official access has been blocked, and no authentic rights-cleared artifact has been supplied. The new project presentation is not law. Consequently the real-law branch is not demonstrated, and the app withholds statutory conclusions/citations instead of filling it with remembered sections or synthetic records.

The positive retrieval tests use clearly synthetic fixtures in temporary directories. They test mechanics, not a real Indian statute or correct legal advice.

## 6. Grounded explanation and verification after admission

When genuinely reviewed, relevant material is available, Gemini can propose conditional explanations using the retrieved source pack. Each legal claim must identify source IDs and exact supporting quotations, connect its application to stated narrative excerpts, disclose conditions/unknowns and avoid fabricated deadlines or guaranteed outcomes.

The backend independently checks reference existence, exact-quote inclusion, jurisdiction and narrative provenance. A separate Gemini prompt checks support for the proposed interpretation. Unsupported or missing verdicts lead to withholding. The interface distinguishes an AI interpretation from a professional conclusion.

There are three different questions: Is the source authentic/current/reusable? Does the quotation actually occur there? Does that source legally support this conclusion for these facts? A checksum or matching string cannot answer all three. A second AI response cannot substitute for qualified independent legal review. That substantive review remains unperformed without the authentic corpus.

## 7. Evidence, OCR and preparation readiness

PDF/TXT extraction and local Tesseract OCR for supported images can surface dates, amounts, references and relevant excerpts. Size/type/pixel/time limits bound processing. A discrepancy is something to reconcile with the user, not a finding of fraud. A scan can be incomplete or misread; extraction does not authenticate its contents.

Evidence suggestions depend on the issue. A recurring-charge dispute might need cancellation acknowledgments and debit records; a fault/cover dispute might need purchase terms, photographs and service sheets. These are preparation suggestions, not an exhaustive or verified official filing checklist.

Readiness summarises completeness of facts, available readable material, unresolved gaps and relevant coverage/review findings. It does not measure merits or odds of winning. Missing law remains visible, and four uploaded file categories alone do not justify Strong readiness.

## 8. Stories, documents and handoff

Sixteen original bilingual scenarios provide fictional learning examples. They are selected by context/category and labelled as fictional. An analogy neither becomes precedent nor makes unsupported legal advice safe or legally exempt. Law-grounded story comparisons still depend on approved sources.

Six editable templates cover seller representation, refund/replacement request, grievance summary, chronology, evidence inventory and lawyer brief. The user reviews placeholders, allegations and requested resolution. HTML-based PDF export includes preparation records and limitations, with external resource loading disabled. These documents are not commission pleadings, bail applications or proof of filing.

Sharing is voluntary and separate from processing consent. The backend gives a distinct demo-lawyer role access to a snapshot, records receipt and supports revocation. Existing downloaded copies cannot be recalled. The implementation does not verify advocates, match by success rate, run live consultations or submit a complaint to NCH/e-Jagriti. Official portal links are starting points; current procedures still need direct validation.

## 9. Privacy and deployment reality

Implemented controls include private guest sessions, owner/role checks, same-origin/CSRF protection, separate consent, bounded uploads, protected/signed downloads, private runtime permissions, an ordinary database audit trail, expiry and deletion. Redaction helps minimise some identifiers but does not prove anonymity. Losing a guest cookie can mean losing access.

The demonstration does not provide end-to-end encryption, encrypted SQLite by default, immutable/blockchain logging or certified compliance. Deployment TLS, disk/backup encryption, robust account recovery, provider contracts, abuse protection and security/privacy assessment are still needed before real-user use. Consent checkboxes alone do not authorise processing real confidential narratives on an unsuitable provider plan.

The cloud app binds loopback. A successful cloud startup does not create a public test link, and the cloud's localhost is not the user's laptop. Native Windows/macOS setup needs the documented platform dependencies; Linux results do not establish native-platform tests.

## 10. Evidence of progress and honest next steps

The latest recorded full suite passed 140 tests on Linux. The fresh 30-case cohort achieved 26 strict passes and 17 exact label sets; replaying the same cohort after general fixes achieved 28 strict passes and 22 exact sets. The replay was not another unseen evaluation. Additional tags and provider failures remain explicit. These are factual-triage/preparation tests, not legal-accuracy or litigation-success rates.

The preparation/browser journey has passed, including evidence, editable documents, PDF and consent-based demo handoff. The strict authentic-source browser gate remains blocked. No real judgment retrieval, outcome model or independent legal-applicability pass is claimed.

The next priority is a rights-cleared, version-reviewed consumer-law/rules/guidance corpus, followed by independent legal evaluation and precision improvements. Real advocate onboarding, voice accessibility, other jurisdictions and integrations should follow their own legal/privacy/security and acceptance checks. Outcome prediction, federated learning, emotion inference and legal digital twins are research proposals, not prerequisites for demonstrating useful preparation today.

## Code map

| Responsibility | Existing implementation |
|---|---|
| Frontend and styles | `index.html`, `app.js`, `style.css` |
| Routes, sessions and case operations | `backend/app.py`, `backend/db.py`, `backend/security.py` |
| Orchestration and validated state | `backend/engine.py`, `backend/schemas.py` |
| Facts, rubric and issue research | `backend/services/case_state.py`, `issue_taxonomy.py`, `retrieval.py` |
| Gemini/source adapters and startup checks | `backend/providers.py`, `backend/services/model_configuration.py` |
| Claim support checks | `backend/services/citation_verification.py` |
| Evidence, stories, drafts and export | `backend/services/evidence_analysis.py`, `scenario_engine.py`, `document_generation.py`, `backend/packet.py` |
| Private offline review/admission | `scripts/offline_sources.py`, `scripts/import_offline_source.py`, `backend/services/offline_review.py` |

See README.md, OFFLINE_INGESTION.md and the actual test reports for commands, metadata requirements and unresolved gates.
