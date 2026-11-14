# Demonstration script

## Preparation
Install and run with README commands. `python -m scripts.seed_demo` creates a database-backed fictional case/draft and stores private session material in `runtime/seed-session.json`, mode 0600. It also generates a private demo lawyer password in `runtime/demo-lawyer-password`. Do not commit or share either. `python -m scripts.run_demo` uses that password for the local demo inbox. Use a second browser profile for lawyer sign-in; enter the password locally, never in chat or recorded demo material.

The seeded record can be inspected with its private cookie via a local developer client; the normal UI creates a fresh consented case so no operator session credentials are exposed. The “Fill laptop demonstration” action pre-fills a fictional template but does **not** silently create a case or grant consent.

## User journey (local features verified)
1. Open the app in a local development browser. Explain the visible warning: verified law and live Gemini are unavailable until their release gates are met. This is an honest case-preparation demo, not a complete legal-intelligence release.
2. Choose English or हिंदी. Select **Fill laptop demonstration**. The narrative uses Demo Seller, INR 45,000 and explicitly supplied dates; these are fictional allegations.
3. Review and tick processing consent and fictional-data confirmation. Gemini opt-in is disabled until backend configuration is present. Select **Create confidential case**.
4. Read the follow-up questions. Add purchase/seller/platform details and seller correspondence dates. Only explicit ISO dates are reconstructed; missing facts are asked about rather than invented. The current local mode is clearly labelled.
5. Open **Case Summary**. Review user allegations, chronological timeline, missing facts, and readiness. Mentioning an invoice in chat does not mark an uploaded invoice as present.
6. Open **Legal References**. With the current empty reviewed corpus, show the explicit abstention and no fabricated sections. **Do not describe this as verified legal advice.** After actual source review and live Gemini validation, this screen will show exact retrieved passages with versions/check dates/official URLs and validated source references.
7. Open **Documents**. Upload four small synthetic UTF-8 text files, classified as invoice, fault, seller correspondence and warranty. Include no personal identifiers. Text extraction and date-discrepancy prompts are local; OCR and authenticity verification are not supported. Readiness changes from Needs information to Partial, and to Strong only with all four categories, explicit dates and no remaining required questions. It never measures odds of winning.
8. Open **Story Mode**. Read the explicitly fictional Asha laptop illustration. It is not a judgment, verified precedent or prediction of the user's outcome.
9. Open **Case Summary**, select **Prepare seller letter**. Review the allegations/placeholders, edit the text, and **Save edits**. This is a seller representation, not a commission pleading. No legal deadline or liability finding is invented.
10. **Download case packet PDF**. Open it and verify the facts, timeline, evidence inventory, missing information, draft and limitations. It includes source passages only when genuinely reviewed; otherwise it records unavailability. Hindi text is rendered with system Unicode fonts.
11. Open **Lawyers**. Review the packet first, tick separate sharing consent, then share. In the second profile sign in to the **demo** lawyer inbox. Download the shared PDF snapshot and acknowledge receipt. Return to the guest case: the demo acknowledgment appears. No verified advocate, professional legal review, email contact or government filing is claimed.
12. Select **Revoke inbox access**; refresh the lawyer inbox and confirm removal. Already downloaded copies cannot be recalled.
13. Open **Help & Filing** for National Consumer Helpline, e-Jagriti and NALSA starting points. Check current instructions directly; this app submits nothing to government portals.
14. Reload to demonstrate backend persistence. Review consent/share audit in Settings, then delete the case to demonstrate cascading evidence/handoff deletion.

## Completing the still-blocked AI/legal segment
- Apply the saved official-site/Gemini network domains and securely bind GEMINI_API_KEY in environment settings. Select a supported stable generation model from `python -m scripts.check_gemini`. Verify current provider pricing, quota and terms before setting GEMINI_TERMS_REVIEWED=true. Select a supported permitted embedding model separately if using hybrid retrieval.
- Complete manual provenance/rights/version review of 30–60 official passages, including current relevant rules and procedural guidance. Use the individual importer described in SOURCES_AND_RIGHTS.md, never the legacy case dataset.
- Rehearse the **live** Gemini opt-in intake and source-grounded reasoning with synthetic data. Validate relevance/applicability with independent legal review. Check provider failures, actual reference links and the complete packet/handoff. Until then, the full requested definition of done remains open.
