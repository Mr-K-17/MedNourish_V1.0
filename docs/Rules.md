# MEDNOURISH — Rules for Humans and AI Coding Tools

| Field | Value |
|---|---|
| Version | 1.3-draft (owner decisions of 2026-10-11 applied; change summary in `Memory.md` section 12.3, entry S-004) |
| Date | 2026-10-11 |
| Status | Draft for owner review |
| Audience | The project owner and AI coding tools (Antigravity, Codex, Cursor) |
| Companion documents | `PRD.md` · `Architecture.md` · `Phases.md` · `Design.md` · `Memory.md` |
| This document answers | What must always, and must never, be done — and what must be verified first |

Status terms (Confirmed, Proposed, Pending, Unverified) are defined in `Memory.md`.

Keywords: **MUST** and **MUST NOT** are mandatory. **SHOULD** is a strong default that needs a recorded reason to depart from.

---

## 0. How to use this file

1. At the start of every session, read `Memory.md` sections 0 to 6 and 11 (status, decisions, registers, next actions; the other sections as needed), then this file, then only the parts of `PRD.md`, `Architecture.md`, `Phases.md` and `Design.md` that the task touches.
2. If documents disagree, **stop and ask the owner**. Do not choose silently. Safety rules in section 2 take precedence over everything else.
3. If a task touches an item in section 9 (verification gates), complete the verification first or stop and report what is missing.
4. At the end of every session, update `Memory.md` (section 7).
5. Tool-specific instruction files (for example `AGENTS.md`, `.cursor/rules`, or equivalents) are **not** part of these six documents. Each tool's current conventions are Unverified; if such files are created, they must only point to these documents and must not duplicate or contradict them.

## 1. Project guardrails

| ID | Rule |
|---|---|
| GR-01 | MUST NOT modify, move, rename or delete anything in `datasets/`. Work on copies elsewhere (`knowledge/`, `ml/`). |
| GR-02 | MUST NOT start model training, large downloads or any long-running job without explicit owner approval recorded in `Memory.md`. |
| GR-03 | MUST NOT invent datasets, sources, statistics, accuracy figures, dates, prices or medical facts. Every number must trace to a file, command output or cited source. "Unknown" is a valid answer. |
| GR-04 | MUST NOT claim any model is trained, validated or clinically accurate without recorded evidence (model card plus evaluation report). |
| GR-05 | MUST NOT hard-code country-specific emergency numbers, hospital services, laws or regulations. Use region configuration; the default is "not configured" (C-05). |
| GR-06 | MUST NOT remove or alter an agreed module, feature or workflow. Changes require owner approval and a decision-log entry in `Memory.md`. |
| GR-07 | MUST NOT write application code before the owner confirms Phase 0 exit (see `Phases.md`). This version of the documents contains no application code. |
| GR-08 | MUST NOT use real people's health data in development, tests, prompts or demos. Fictional data only. |
| GR-09 | MUST NOT commit secrets, API keys, service-account files, real user data, images, or large model files to the repository. |
| GR-10 | MUST keep file names exactly as in the document set: `PRD.md`, `Architecture.md`, `Rules.md`, `Phases.md`, `Design.md`, `Memory.md` (never `.md.txt`). |
| GR-11 | Phase 1 is local only (C-14). MUST NOT create a cloud project, enable billing, deploy anywhere public, or use real health information. Use the Firebase emulators with fictional accounts and data. |
| GR-12 | Datasets, secrets, environment files, emulator data and large files MUST NOT be added to new Git commits. MUST NOT push datasets to any remote (C-16). Before the first commit, check whether any such file is already tracked and report the result to the owner (PV-18). Dataset provenance and redistribution rights are Unknown. |
| GR-13 | MUST NOT integrate an LLM in Phase 1 (C-15). MUST NOT add any paid API, service or subscription without the owner's explicit approval. |
| GR-14 | MUST NOT arrange testing with human participants until the owner has checked the institution's ethics and supervisor requirements (C-24, PV-19). |

## 2. Medical safety rules

These implement confirmed decision C-08.

| ID | Rule |
|---|---|
| SAF-01 | Outputs are **reference-table matches and general education**, never diagnoses, risk assessments, predictions or probabilities. |
| SAF-02 | MUST NOT recommend, name for use, or give doses of medicines or supplements, and MUST NOT tell anyone to start, stop or change a medicine. Allowed: food sources, lifestyle information, and "talk to a qualified clinician about whether testing or treatment is appropriate". |
| SAF-03 | Emergency guidance MUST come from fixed, reviewed wording, MUST direct users to local emergency services, and MUST NOT depend on an AI prediction, an LLM, the backend or a signed-in session. In Phase 1 it is a static page bundled with the frontend that works signed out and offline and is reachable from every screen (C-20). |
| SAF-04 | Emergency numbers and support resources come only from region configuration. If not configured, show "contact your local emergency services" without a number. |
| SAF-05 | Wording: use "may be associated with", "possible", "worth discussing with a clinician". MUST NOT write "you have", "you are deficient", "you are fine" or "no problem". |
| SAF-06 | When information is limited, show **Insufficient information**; MUST NOT reassure. MUST NOT show "no red flags found" or any other all-clear wording anywhere (C-20). |
| SAF-07 | Show a short disclaimer on every result screen and in every report view. |
| SAF-08 | User-facing urgency tiers, severity and specific timeframes MUST come from clinically reviewed content (PV-17). While content is unreviewed, MUST NOT show any of them and MUST NOT infer urgency from a table match; use only the general prompt to consult a qualified clinician if concerned. |
| SAF-09 | In the MVP, non-nutritional disease classes MUST NOT be displayed to users at all (C-18). They may stay in the cleaned data, flagged, and are never merged into nutritional results. Any later display needs a new owner decision and review. |
| SAF-10 | Version 1 was adults 18+ only (C-21). **Amended by C-33**: Onboarding now collects age (integer 1-120, demo purposes), gender, height, weight, blood type, and medical conditions (multi-select of 18 + None/Other). The 18+ gate is replaced by a demo-consent checkbox. Under-18 users see: 'Reference content is written for adults; demo only.' |
| SAF-11 | Phase 1 has no free-text health input that the app analyses, so there is no automated self-harm detection. The static emergency page carries supportive wording and points to local emergency and support services (C-20). Automated detection is required before any free-text health input is analysed (see SAF-15). |
| SAF-12 | ML-derived output MUST be labelled "experimental" until gates G1–G6 (`Architecture.md`) are passed and recorded. |
| SAF-13 | Medical content, any red-flag list, any future scoring specification and any urgency wording need clinical review before any public release (PV-17). Until then, label them "unreviewed draft" in internal tooling and in the demo banner. |
| SAF-14 | NurseBot safety boundaries (C-08, C-15, C-23). **Amended by C-36**: NurseBot may show internet-sourced vitamin/medication information from allowlisted NIH/MedlinePlus sources with a visible disclaimer; personal diagnosis/prescriptions remain strictly refused. CarePlan and reports still never contain medicines, supplements or doses. |
| SAF-15 | Phase 1 MUST NOT include an automated emergency-triage or red-flag detection engine (C-20). Candidate red flags found in the CSV content are inputs to clinical review only. Such an engine is required, with a reviewed rule list, before any free-text health input is analysed. |
| SAF-16 | MUST NOT display unreviewed treatment, supplement, drug, dose, timeframe, severity, urgency or advice content (C-17). Until a qualified reviewer is recorded, all existing nutritional mappings and routines are unreviewed drafts. |
| SAF-17 | User-facing labels and wording (C-18, C-19). **Amended by C-34 and C-35**: Percentages are allowed across features when clearly labelled by kind ('Reference match %', 'Model %', 'Image model %'; never medical probabilities). Demo risk bands (High/Moderate/Low) are allowed when labelled 'Demo risk band (heuristic, not clinical)'; reports say 'screened'/'probable pattern', never 'diagnosed'/'tested'. |

**Phrasing examples.**
- Acceptable: "Your answers have some patterns that are sometimes linked to low vitamin B12 intake. This is not a diagnosis. A clinician can tell you whether a blood test makes sense."
- Not acceptable: "You have a B12 deficiency. Take a B12 supplement."

## 3. Data and ML rules

| ID | Rule |
|---|---|
| DAT-01 | Before using any dataset, record: source and provenance, licence, labelling method, row/image counts, class distribution, missing values, duplicates, leakage risks, relevance to the task. Mark anything unverifiable as **Unknown**. |
| DAT-02 | Keep unrelated diseases and conditions as separate classes. MUST NOT fold them into vitamin labels. |
| DAT-03 | The 13 `MedBot_datasets` CSVs are **reference tables**. MUST NOT treat their rows or synthetic variants as patient records, clinical labels, or evidence of predictive performance. They may power a transparent lookup after cleaning and review. |
| DAT-04 | Clean by creating copies in `knowledge/` with a CHANGELOG; never edit originals. Every change is logged with its tier. **Tier 1, mechanical:** CSV quoting and delimiter repair, whitespace, encoding, header normalisation, adding IDs and a review-status field. **Tier 2, meaning:** any change to a symptom term, tag, class or nutrient label, any split, merge or rename of tags, any synonym, any typo correction that could change a symptom's meaning, any adult/child or nutritional/non-nutritional classification, and any exclusion of a class. Tier 2 changes need the owner's approval (and the clinical reviewer's once one exists) and stay "unreviewed draft" until then. An AI tool MUST NOT make Tier 2 changes on its own. |
| DAT-12 | No ML training of any kind in Phase 1 (C-12). Synthetic rows generated from the mapping tables may be used only to test software plumbing, never as evidence, and not before the ML evaluation track in Phase 2. |
| DAT-05 | Remove duplicates and near-duplicates **before** splitting; verify no overlap between train, validation and test (including across folders such as `dataset/` and the body-region folders — PV-05). |
| DAT-06 | Never tune on the test set. Set evaluation thresholds with the clinical reviewer **before** testing; do not invent thresholds. |
| DAT-07 | Report per-class results and a confusion matrix; evaluate subgroups (age, gender, skin tone, lighting); include Normal, Other and "unclear" outcomes. |
| DAT-08 | Phase 2 only (C-12). Compare XGBoost and LightGBM against simple baselines; the model must beat them. Calibrate scores; do not present model output as risk bands, percentages or probabilities unless the owner and the clinical reviewer approve the wording. |
| DAT-09 | Record data hashes, random seeds, library versions and run commands for every experiment. |
| DAT-10 | Write a model card for every model, including known limitations and what the model must not be used for. |
| DAT-11 | If evidence is insufficient for a prediction, document the limitation and use a safe alternative (transparent reference lookup, broad groups, guided capture without AI, or withhold). |

## 4. Privacy and security rules

| ID | Rule |
|---|---|
| SEC-01 | Every API route (except the public health check) MUST verify the Firebase ID token and check ownership of the data it touches. |
| SEC-02 | Database access rules MUST deny by default, with strict ownership checks. Direct client database writes are prohibited; all writes to MySQL and MongoDB go through the authenticated FastAPI service (C-14, OD-16). Firestore emulator remains available for legacy security-rule parity tests where applicable. |
| SEC-03 | Validate all inputs on the server (types, lengths, allowed values). |
| SEC-04 | Logs MUST NOT contain names, answers, symptoms, health details, tokens, image bytes or other personal data (C-23). |
| SEC-05 | Image uploads (Phase 2): validate type by content; allow-list JPEG, PNG, WebP; cap size and pixel dimensions; re-encode and strip metadata; random names; delete after processing unless explicitly saved (C-06). |
| SEC-06 | No LLM exists in Phase 1 (C-15). If one is later approved, requests MUST NOT include names, user IDs, contact details or photos, and the consent text must cover the processing. |
| SEC-07 | If an LLM is later approved: treat user text and retrieved content as untrusted (prompt-injection risk); the LLM has no tools and no direct data access. |
| SEC-08 | Pin dependency versions; review new dependencies for licence and maintenance (PV-09, PV-14). |
| SEC-09 | Consent MUST be explicit and versioned; users can delete their account and data. Own-data export is required before any real user data is introduced (real-data readiness gate, section 9). |
| SEC-10 | No paid service is used in Phase 1. If the owner later approves one, check whether its spending limit is a hard cap or only an alert, and set the limit and alert before enabling it. |

## 5. Engineering rules

| ID | Rule |
|---|---|
| ENG-01 | Use the architecture in `Architecture.md`: FastAPI, React, Vite, TypeScript, Firebase Authentication emulator, local MySQL 8.0+ for relational user data, and local MongoDB 9.0+ for versioned reference knowledge packages (C-07, C-14, OD-16). Cloud Storage is not used in Phase 1. Do not add Java or other languages for the MVP (C-03). The stack is subject to dependency and feasibility checks (PV-14). |
| ENG-02 | TypeScript strict mode; Python type hints; formatters and linters configured at scaffold time (tool choice Proposed; versions Pending PV-14). |
| ENG-03 | All user-facing text lives in translation files; no hard-coded strings (I18N-01). |
| ENG-04 | Accessibility is part of "done" for every milestone (see `Design.md`, section 10); the final audit in M1B.7 does not replace the per-milestone checks. |
| ENG-05 | Country-specific values come from configuration (SAF-04, GR-05). |
| ENG-06 | No LLM adapter is built in Phase 1 (C-15). If an LLM is later approved, it sits behind a provider-swappable adapter (OD-06). |
| ENG-07 | Small, focused changes; one task per branch; descriptive commit messages (Conventional Commits proposed). |
| ENG-08 | Document any decision that changes behaviour in `Memory.md` and update every affected document (see the cross-reference table in section 8). |
| ENG-09 | Keep the code simple and readable; the owner is a beginner. Prefer clear names, short functions and comments that explain *why*. |
| ENG-10 | Do not copy code or content from sources whose licence is unknown (PV-09). |

## 6. Testing rules and definition of done

A task is done only when:
1. It meets its requirement IDs in `PRD.md` and the acceptance criteria of its milestone in `Phases.md` section 3, and the owner's review of the milestone is recorded in `Memory.md`.
2. Tests exist and pass: unit (Python and TypeScript), API contract, and — for data access — Firebase security-rules tests with the emulator.
3. Safety checks pass for any feature that produces health content: a forbidden-wording scan (diagnosis, risk, prediction, probability, bands, all-clear wording), no medicine, supplement, dose or treatment text, no excluded content fields, Urgent help reachable from the screen, and out-of-scope requests handled by the scripted refusal. If an LLM is ever approved, add prompt-injection tests.
4. Accessibility checks pass for the screens touched (automated checker plus keyboard and screen-reader spot checks).
5. Image features: malformed, oversized, wrongly typed and metadata-bearing files are rejected or sanitised (Phase 2).
6. ML work: results are reproducible from recorded data hashes, seeds and versions.
7. No secrets, personal data or large files were committed.
8. `Memory.md` is updated.

Test data is fictional (GR-08).

## 7. Workflow rules for AI tools

**Start of session**
1. Read `Memory.md`; confirm the current phase and open blockers.
2. Check section 9 for gates relevant to the task; if a gate is open, report it and stop.
3. State the plan and the requirement IDs before changing files.

**During work**
- One tool edits a given branch or file at a time. Use a branch per task.
- Ask the owner when a decision is unclear; do not assume.
- Never present a guess as a fact. Say what is unverified.

**End of session**
- Update `Memory.md`: what changed, what was verified (and how), what is still pending, and any new open question.
- Add a session-log entry.

**Actions that always need explicit owner approval**
- Running model training or heavy computation.
- Touching `datasets/` (reading for an approved audit included). Originals are never changed.
- Adding a paid service, API or subscription, or enabling billing.
- Creating a cloud project or cloud resource, or deploying anywhere public.
- Any Git action that adds, tracks or pushes datasets or secrets (forbidden), and any change to Git configuration or ignore rules outside an approved milestone.
- Any Tier 2 data-cleaning change (DAT-04).
- Arranging testing with human participants.
- Changing a confirmed decision or removing a feature.
- Adding a dependency with a new licence type.
- Any step that sends data to a third party.
- Any wording of medical content that is not already approved.

## 8. Cross-reference table (what to update when something changes)

| If this changes | Also update |
|---|---|
| A requirement | `PRD.md`, and any milestone in `Phases.md` and screen in `Design.md` that cites its ID |
| Phase scope | `PRD.md` (section 5), `Phases.md`, `Architecture.md` (phase columns) |
| Technology choice | `Architecture.md`, `Rules.md` (ENG-01), `Memory.md` (decision log) |
| Safety wording or rule | `Rules.md` (section 2), `Design.md` (microcopy), `PRD.md` (SAFE requirements) |
| Retention or privacy rule | `Architecture.md` (11.1), `Rules.md` (section 4), `PRD.md` (PRIV, SCAN-05) |
| Any decision, assumption or verification status | `Memory.md` registers |

## 9. Verification gates: what must be checked before implementing affected features

Do not implement the feature in the left column until the listed items are closed, or the owner explicitly approves proceeding with the stated assumption.

| Feature / task | Verify first | How to verify | Unblocks |
|---|---|---|---|
| First commit and first code (M1A.1) | PV-18 Git tracking check · PV-14 dependency versions · Phase 0 exit | Read-only check, with owner approval, of whether any dataset, secret or environment file is already tracked and of the remote's visibility; record the result | Phase 1A |
| Any ML **training** | **Not allowed in Phase 1 (C-12).** In Phase 2: PV-01 main CSV · PV-02 ETL notebook · PV-17 · PV-09 · OD-17 | Verify source, labels, licence, input/target compatibility, leakage, independent split, clinical task approval and evaluation thresholds. If the available inputs do not match the verified target, do not train that task. Synthetic rows derived from mapping tables cannot satisfy this gate. | Phase 2 gated model work only |
| Any user-facing ML output on structured data (XGBoost, LightGBM), ML-assisted Symptom Reference Explorer or MedBot scoring | The row above plus G1 to G6 (`Architecture.md` 8.2) | Evaluation report, model card, owner approval | Later gated model work only |
| MedScan and any image model | PV-04 image folders · PV-05 duplicates · PV-06 annotation files · PV-09 licences · PV-17 | Folder counts, formats, label provenance, duplicate checks, quality review | Phase 2 image work |
| Reference package and Symptom Reference Explorer, MedBot content (M1B.1 onward) | PV-07 CSV provenance (may be recorded as Unknown) · OD-04 plan · OD-19 · PV-17 route | Record what is known about provenance and licence; create cleaned copies (DAT-04 tiers); exclude supplement, drug, timeframe, severity, urgency and treatment content; owner approves the matcher specification. Until reviewer sign-off, keep the build in educational-prototype mode with unreviewed-content status; no public advice release. | Phase 1B on local fictional data; public release remains gated |
| Risk Score | **Amended by C-35**: Demo risk band (High/Moderate/Low) allowed, strictly labelled 'Demo risk band (heuristic, not clinical)'; reports say 'screened'/'probable pattern', never 'diagnosed'/'tested'. | Owner amendment C-35 | Educational prototype |
| Static emergency help page (M1A.3) | PV-15 offline behaviour per platform | Test offline on target browsers; region text only through configuration | M1A.3 |
| Region-specific emergency information, red-flag rules | PV-10 target country · PV-17 · PV-12 | Region configuration filled and reviewed; any rule list approved | Region text; any automated red-flag detection |
| NurseBot LLM Q&A and MedBot Detailed mode | **Not in Phase 1 (C-15).** Later: PV-11 · OD-06 · explicit owner approval including any payment | Re-check current pricing, retention, training-use terms and limits from official sources, with date and URL; run a safety test set | LLM features |
| Cloud project, hosting, storage, backups, billing | **Not in Phase 1 (C-14).** Later: PV-13 · OD-08 · OD-11 · explicit owner approval | Check plan requirements, pricing, regions, request-size limits, backup behaviour, and whether a spending limit is a hard cap or an alert | Deployment |
| ML libraries and model export | PV-14 | Check version compatibility; choose export format | Training and serving |
| Push reminders, install prompts, read-aloud | PV-15 | Test per platform | Phase 3 reminders; A11Y-03 |
| Maps, Calendar, Tasks | PV-16 · PV-10 | Confirm billing, OAuth scope verification, Tasks time limitation, quotas | Phase 3 |
| Testing with human participants | PV-19 | Check the institution's ethics and supervisor requirements | User testing |
| Doctor chat, booking, DocExp | PV-12 · real clinician partners | Legal and regulatory review; clinician verification process | Phases 4–5 |
| **Real-data readiness gate:** any real user's health information, any shared or public deployment | OD-08 retention and deletion documented · own-data export built · PV-10 · PV-12 · PV-13 · PV-17 · PV-09 · PV-19 where applicable | Written retention and deletion rules; privacy and regulatory review; clinical review; licences; hosting checks; owner approval | Real users; public release |

## 10. Glossary (plain language)

- **Reference match summary:** an ordered list of reference-table entries whose listed symptom tags overlap the tags the user chose, showing the matched tags. It is a lookup result from an unreviewed table, not a diagnosis, a risk level or a probability.
- **Educational prototype:** the status of the MVP: a learning and demonstration build on fictional data, not a medical tool.
- **Retired terms (superseded by C-34/C-35):** "band" (Low/Moderate/High) is now permitted when explicitly labelled 'Demo risk band (heuristic, not clinical)'; percentages permitted when labelled by kind ('Reference match %', 'Model %', 'Image model %').
- **Data leakage:** accidentally letting the model see test answers (for example, the same photo in training and testing), which makes results look better than they are.
- **Baseline:** a very simple method a model must beat to be worth using.
- **Calibration:** making a model's scores behave like honest probabilities.
- **Shadow mode:** running a model quietly and comparing it with the rules without showing its output to users.

## 11. Owner Amendments Register (C-33..C-39)

| Amendment ID | Overrides / Amends | Specification |
|---|---|---|
| **C-33** | C-01, PROF-01 | Onboarding collects age (integer 1-120, demo purposes), gender, height, weight, blood type (A+, A-, B+, B-, AB+, AB-, O+, O-, Unknown) and medical conditions (multi-select of 18 + None/Other). 18+ gate replaced by demo-consent checkbox. Under-18 users see: 'Reference content is written for adults; demo only.' |
| **C-34** | C-18, SAF-17, C-30 | Percentages allowed across features, always labelled by kind: 'Reference match %', 'Model %', 'Image model %'; never described as a medical probability. |
| **C-35** | C-18, SAF-17 | Demo risk band High/Moderate/Low allowed, labelled 'Demo risk band (heuristic, not clinical)'; reports say 'screened'/'probable pattern', never 'diagnosed'/'tested'. |
| **C-36** | C-08 (NurseBot only) | NurseBot may show internet-sourced vitamin/medication information with a disclaimer from allowlisted sources (MedlinePlus/ODS). CarePlan and reports still never contain medicines, supplements or doses. |
| **C-37** | Architecture / MedScan | MedScan lists nutrient candidates with percentages (blended with region follow-up checklist). |
| **C-38** | CARE-02 / Reports | CarePlan auto-sync from reports for top nutrients >= 30% from curated dietary/lifestyle routine columns only (never supplements). |
| **C-39** | C-38 / CARE-02 | CarePlan includes a deterministic meal planner from a curated food guide: foods only; no medicines, supplements, doses, calories or nutrient amounts; amends C-38 for the food part. |

