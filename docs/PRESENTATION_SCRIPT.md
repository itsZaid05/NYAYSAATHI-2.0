# NyaySaathi presentation script

For **23 November 2026, Asia/Kolkata**. Written as a first-person draft for the presenter, based on the user's experiences and the existing prototype. The broader personal motivation is distinct from the consumer-only demonstration. Approximate delivery time: five minutes, depending on pace.

## Main spoken script

Good morning everyone.

Growing up, I often saw people facing difficult situations without knowing where to begin. A classmate was afraid to speak about bullying. A relative received a threatening scam call from someone pretending to be a police officer. In my family, legal questions often meant calling the one person who understood the process.

One example stayed with me: a neighbour ordered a phone online and received an empty box. Beyond the money, the immediate problem was confusion. What should they preserve? How should they explain what happened? Who should they approach?

These experiences inspired NyaySaathi. Our long-term vision is that no one should feel alone or lost when they need legal help. For our working prototype, we have chosen a focused starting point: Indian consumer disputes.

NyaySaathi is an AI-assisted case-preparation companion. It helps a user explain a problem, organise facts, identify evidence gaps, prepare editable documents and decide whether to share a case packet with a human recipient.

Let me explain the journey with a fictional online-shopping dispute.

The user first gives consent and describes what happened in ordinary English or Hindi. When live AI is available and the user opts in, Gemini asks relevant factual follow-up questions. The backend structures the narrative into parties, amounts, events and possible consumer issues.

We do not want a system that simply picks one keyword. A dispute can involve a product problem, a cover promise and a refused payment return at the same time. Our intake reviews multiple issue families, and each positive finding must refer back to the user's actual words. Missing facts remain questions; allegations are not treated as proven facts.

Next, the workspace helps organise evidence. It can extract information from supported documents and use local OCR for supported images when Tesseract is installed. It suggests what may still be missing, such as the order record, payment proof, packaging photographs or seller correspondence. Extraction helps preparation; it does not prove that a document is authentic.

The user can also explore a clearly fictional story to understand the kind of situation being discussed. That story is a learning aid, not a judgment or a prediction.

Then the system creates editable preparation documents and a downloadable PDF case packet. With separate consent, a snapshot can be shared with a clearly labelled demo lawyer account. In this prototype, that demonstrates the handoff process; it is not advocate verification, live legal representation or an official filing.

Our architecture uses the existing web interface, a FastAPI backend, Pydantic validation, SQLite persistence and Gemini. We have also implemented a hybrid retrieval path combining keyword search with semantic embeddings.

There is an important limit I want to state clearly. We currently have no approved authentic legal passages in the corpus. We will not replace them with invented statutes or unverified cases. Until official documents pass provenance, version and reuse review, the application withholds legal conclusions and statutory citations. A separate AI support check would still not replace independent professional legal review.

Our preparation workflow has passed the recorded Linux test suite of 140 tests. A fresh thirty-case triage evaluation and its later replay also exposed remaining label errors and provider failures. We report those results openly; we do not turn them into a legal-accuracy claim or a probability of winning.

Privacy is part of the design through consent, access controls, private storage permissions, protected downloads and deletion. Real confidential-user processing remains disabled pending the additional privacy, security and provider requirements. We are not claiming end-to-end encryption or blockchain auditing.

Our next priorities are verified consumer-law sources, independent legal evaluation and better multi-issue precision. Further plans include accessible voice interaction, responsible advocate onboarding and other jurisdictions only after the required checks.

NyaySaathi's purpose is to make the first step clearer: helping a person explain their situation, preserve useful information and reach appropriate human help with better preparation.

Thank you.

## Short backup version

NyaySaathi began with a simple observation: when people face a legal problem, they often do not know where to begin. My experiences of people dealing with scam threats, family legal questions and online-shopping disputes inspired this project.

Our working prototype focuses on fictional Indian consumer disputes. With consent, it helps organise a narrative into facts, dates, possible issues and missing questions. Gemini can provide contextual intake when available; supported documents and local OCR help organise evidence. Users can create editable preparation documents, download a PDF packet and voluntarily share a snapshot with a clearly identified demo lawyer account.

The limits matter. We do not have an approved authentic legal corpus yet, so the application withholds statutory conclusions and citations. It does not predict winning chances, verify advocates or file complaints. Real confidential-data use remains gated.

Our next step is verified legal-source integration and independent legal evaluation. The broader vision is accessible, understandable legal support, beginning with a practical goal today: help people take a more informed first step.

## Rehearsal guidance

- Personal examples are motivation, not claims that the demo supports criminal, family or foreign law.
- Say “demo lawyer account”, “fictional scenario”, “editable draft” and “evidence completeness”.
- If the AI is unavailable during the demo, identify the failure and demonstrate local preparation with its visible fallback label. Do not imply that local output came from live Gemini.
- Show source abstention as an intentional release gate, not a completed legal analysis.
- Use synthetic documents and fictional identities. Do not expose credentials, private recipient passwords or real personal stories in a screen recording.
- Keep detailed market statistics out until dated sources and measurement definitions are checked.
