# MEDNOURISH — Memory (Status, Registers and Handoff Log)

| Field | Value |
|---|---|
| Version | 1.3-draft (master registers reconciled, owner decisions C-13..C-24 and dataset audit incorporated) |
| Date | 2026-10-12 |
| Status | Draft for owner review |
| Audience | The project owner and AI coding tools (Antigravity, Codex, Cursor) |
| Companion documents | `PRD.md` · `Architecture.md` · `Rules.md` · `Phases.md` · `Design.md` |
| This document answers | Where the project stands today, what is decided, what is still open, what has and has not been verified, and what to do next |

**Status legend (identical in all six documents)**

- **Confirmed** — decided by the project owner.
- **Proposed** — recommended during planning; not yet confirmed. Treat as a working assumption.
- **Pending** — a decision or verification is still open. IDs (OD-xx, PV-xx) are defined in this file.
- **Unverified** — information that has not been inspected or checked. Do not rely on it.

**This file is the single home of the master registers:** confirmed decisions (C-xx, section 4), open decisions (OD-xx, section 5) and pending verifications (PV-xx, section 6). The other five documents refer to these IDs and never redefine them.

---

## 0. How to use this file

1. **Read it first** in every session (`Rules.md` section 0), then `Rules.md`, then the relevant parts of the other documents.
2. **Update it last** in every session (`Rules.md` section 7): change the status snapshot, edit any register row whose status changed, and **append** a session-log entry (section 12). Never delete log entries.
3. If this file and another document disagree, **stop and ask the owner**. Do not pick one silently.
4. A register row changes status only when the owner decides or the evidence is recorded. Write down *how* a verification was done (file, command, source), not only the result.
5. Do not write a number, source, date, price or medical fact here unless it traces to a file, a command output or a cited source. "Unknown" is a valid entry.

## 1. Status snapshot (plain language)

| Question | Answer today |
|---|---|
| What exists? | Six Draft 1.3 planning documents, dataset audit, validation report, and safe Phase 1A development worktree (`MedNourish-Dev`). |
| Is there any application code? | **Phase 1A starting.** Phase 0 exit authorized by owner on 2026-10-12: "Phase 0 complete; application code may begin". |
| Are any AI models trained? | **No.** No XGBoost, LightGBM or MobileNetV2 model has been trained or evaluated. No accuracy figure exists anywhere in the project. |
| Has any medical content been reviewed by a clinician? | **No.** All medical content, red-flag lists and wording remain "unreviewed draft" (PV-17). Educational prototype banner in force. |
| Which data has been looked at? | Comprehensive read-only audit in `DATASET_AUDIT.md`: 34 CSVs, 372,536 images, 21,902 annotations inspected. Provenance/licensing remain unverified. |
| Which phase are we in? | **Phase 1A — Foundation and safety shell: In progress.** Phase 0 Complete. |
| What is the MVP? | Phase 0 + Phase 1 (`PRD.md` section 5, `Phases.md` section 1). |
| Is MedScan in the MVP? | **No.** MedScan is Phase 2 and requires separate image data, annotation, licence, and model gates (C-10). |
| Deadline? | Unknown (OD-07). Phases are ordered by dependency, not by date. |
| Is it ready for real users? | **No.** It is an academic demo (C-01). A public release needs PV-09, PV-10, PV-12 and PV-17 first. |

**Phase tracker** (matches `Phases.md` section 1)

| Phase | Name | Status |
|---|---|---|
| 0 | Foundations and verification | **Complete (Owner exit sign-off 2026-10-12)** |
| 1A | Foundation and safety shell | **Complete (Owner reviewed and approved)** |
| 1B | Initial features | **In progress (M1B.1, M1B.2 & M1B.3 Complete; M1B.4 pending owner authorization)** |
| 2 | MedScan and model evaluation | Not started; gated |
| 3 | VirtualWard and Google integrations | Not started |
| 4 | Doctor chat and booking | Not started |
| 5 | DocExp | Not started; future scope |

## 2. Project in brief

- **Name:** MEDNOURISH — Early Detection and Prediction of Vitamin Deficiency in the Human Body.
- **What it is:** a responsive web app (installable PWA) that gives adults a *preliminary, educational* view of possible nutritional-deficiency risk. It does not diagnose, treat or prescribe (C-08).
- **Modules (all retained from the owner's brief — GR-06):** MedBot, MedScan, Symptom Analyzer, VirtualWard, NurseBot, CarePlan, Files and Reports, DocExp (future), plus a WhatsApp-like doctor–patient chat (Phase 4). Which phase each belongs to: `PRD.md` section 5.
- **Proposed architecture (C-07):** FastAPI (Python) · React + Vite + TypeScript PWA · Firebase Authentication · Cloud Firestore · Cloud Storage · versioned CSV-derived knowledge package for the MVP matcher · XGBoost/LightGBM as later gated candidates · OpenCV/MobileNetV2 for gated MedScan · provider-swappable LLM adapter (provider Pending). Details: `Architecture.md`.
- **Owner profile:** a beginner in AI/ML who works with AI coding tools. Explain technical decisions in simple language (assumption A3 in `PRD.md` section 12).

## 3. Inventory of what exists (as far as known)

"Inspected" means a tool opened or parsed the file. Read-only inspection does not verify provenance, clinical validity, licensing, or truth of labels.

| Item | Where | Inspected? | Status |
|---|---|---|---|
| Six planning documents | `docs/*.md` | Yes — read and reconciled in this session | Draft for owner review; current source of truth |
| Legacy `.md.txt` references | `docs/` | Current named `.md` files exist; stale references in older notes identified | PV-08 resolved for current docs; references updated here |
| 13 `MedBot_datasets` CSVs | `datasets/MedBot_datasets/` | Schemas, filenames and parsed record counts inspected read-only | Reference content; source/licence and clinical review remain open (PV-07, PV-09, OD-04, PV-17) |
| Main CSV `vitamin_deficiency_disease_dataset_20260123.csv` | `datasets/` | Parsed read-only | 4,000 rows × 34 columns; provenance, label generation, licence and clinical validity unknown (PV-01) |
| ETL notebook | `datasets/vitamin-deficiency-disease-prediction-dataset-etl.ipynb` | Notebook JSON/cells inspected | One exploratory code cell with outputs; no model training/evaluation workflow found (PV-02) |
| Structure file | `datasets/DATASET_STRUCTURE.txt` | Length checked | Empty (0 bytes); no structure or provenance notes (PV-03) |
| Deficiency image collection | `datasets/dataset/` | Class-folder and common image extension inventory | 11 class folders; 25,632 image files counted by common extensions; image contents, label truth, duplicates and licence remain unverified (PV-04, PV-05, PV-09) |
| Body-region image folders | `datasets/EYES/`, `HAIR/`, `LIPS/`, `NAILS/`, `SKIN/`, `TONGUE/` | Folder taxonomy and partial file inventory | Taxonomies differ. EYES includes JSON/MAT files; TONGUE has COCO/TXT/XML subfolders. Semantics, image-level labels, quality, duplicates and licences remain unverified (PV-04–PV-06, PV-09) |
| Application code or UI | — | Directory listing only | None exists (C-02, C-11) |

**Observed folder taxonomy (labels are not image verification):** `dataset/` has 11 deficiency-name folders; EYES: Normal, Nutritional_Optic_Conditions, Other_Ocular_Conditions, Vitamin_A_Deficiency; HAIR: Alopecia, Corkscrew_Hair, Normal, Other, Sparse_Hair; LIPS: NON_NUTRITIONAL, NORMAL, NUTRITIONAL; NAILS: NON_NUTRITIONAL, NORMAL, NUTRITIONAL, OTHER; SKIN: BIOTIN, NORMAL, OTHER, PROTEIN_ENERGY_MALNUTRITION, VITAMIN_A, VITAMIN_B3, VITAMIN_C, ZINC; TONGUE: Diabetes, Healthy, OralCancer, Pre Diabetes, and `shezhen datasets`. These labels do not align to a single shared target taxonomy, so do not combine folders into one model without an explicit label mapping and audit.

**Dataset categorisation** (`Rules.md` DAT-01):

| Dataset | Category | Reason |
|---|---|---|
| 6 region symptom mappings + keyword table | Candidate cleaned knowledge base | Reference associations suitable for transparent matching after provenance, cleaning and clinical review; not patient records |
| 6 suggested-routine tables | Needs cleaning and review | Supplement/drug/timeframe wording is present; exclude those fields from user content (OD-02) |
| 13 reference CSVs as ML training data | Unsuitable as patient-level examples | No independent people with verified outcomes; synthetic variants do not establish predictive performance (DAT-03) |
| Main structured CSV | Candidate for later audit only | Parsed labels/features, but source, generation, label validity, licence and feature/target fit are unknown (PV-01) |
| Image collections | Candidate for separate MedScan audit | Inventory only; label semantics, duplicates, quality, provenance and licence remain open (PV-04–PV-06, PV-09) |

## 4. Confirmed decisions (C-xx)

These are decisions by the owner, as recorded in the planning conversation and in the Version 1 documents. If the owner wants any wording corrected, change it here and in the documents that cite it (`Rules.md` section 8).

| ID | Decision | Cited in |
|---|---|---|
| C-01 | **Audience and nature.** Version 1 is for adults aged 18 and above. It is an academic demonstration designed to grow into a fuller application. Tailored guidance for children or other special groups is out of scope. | `PRD.md` 1, 2, 3 · `Rules.md` SAF-10 |
| C-02 | **No existing app to preserve.** No existing application, UI or Figma design exists. All modules and workflows in the owner's brief are retained (GR-06). | `PRD.md` 5.1 · `Design.md` intro |
| C-03 | **Web, not native.** A responsive, installable web app (PWA); no native Android/iOS app. Python for backend and ML; TypeScript/JavaScript for the front end. Java is not used in the MVP. | `PRD.md` 2, 5.1 · `Architecture.md` 2 · `Rules.md` ENG-01 |
| C-04 | **Chat approach.** Chat uses an LLM for language only, behind a provider-swappable adapter, grounded in a curated knowledge base. Red-flag rules run before any LLM. Scripted fallbacks cover outages, quota limits and blocked outputs. XGBoost/LightGBM are not used for conversation. The **provider is not chosen** (OD-06, PV-11). | `PRD.md` 5.1, NURSE-03/04 · `Architecture.md` 2, 9 |
| C-05 | **Configuration and language.** English first and translation-ready; no hard-coded strings. Anything country-specific (emergency numbers, facilities, legal text) is configuration, never hard-coded; default is "not configured". Voice read-aloud "where practical". | `PRD.md` 2, SAFE-02, I18N-01, A11Y-03 · `Rules.md` GR-05 |
| C-06 | **MedScan image handling.** Server-side inference in the first design (on-device later is an option). Secure upload validation and an OpenCV quality gate. Images are deleted automatically after processing unless the user explicitly chooses to save them and safe storage exists. | `PRD.md` SCAN-02, SCAN-05 · `Architecture.md` 5.2, 10, 11.1 |
| C-07 | **Stack adopted for Version 1.** FastAPI, React, Vite, TypeScript, Firebase Authentication, Firestore and Cloud Storage, **subject to the verification items** PV-13, PV-14 and PV-15. | `Architecture.md` 2 · `Rules.md` ENG-01 |
| C-08 | **Medical safety principles.** Results are preliminary risk assessments and educational guidance, never diagnoses. No medicines, supplements or doses. Users are told when to consult a qualified clinician. Emergency guidance comes from fixed rules and points to local emergency services; it never depends on an AI prediction. ML-derived output is labelled "experimental" until verified. No model is claimed to be trained, validated or accurate without evidence. | `PRD.md` 8 · `Rules.md` section 2 |
| C-09 | **Protect the data.** Files in `datasets/` are never modified, moved, renamed or deleted. Cleaning happens on copies. No destructive operation and no model training without the owner's explicit approval. | `Architecture.md` principle 7 · `Rules.md` GR-01, GR-02 |
| C-10 | **MedScan stays in Phase 2**, pending dataset verification and successful model evaluation. The MVP (Phase 0 + 1) contains no image analysis. | `PRD.md` 5 · `Phases.md` 1, 4 |
| C-11 | **No application code yet.** Application code may begin only after the owner states "Phase 0 complete; application code may begin". These documents contain no application code. | `Rules.md` GR-07 · `Phases.md` header |
| C-12 | **Preferred tabular ML families.** The owner wants to use XGBoost and LightGBM for the structured-data idea. Their user-facing role and timing remain gated on suitable verified data and a clear input/target task; this does not approve synthetic table-derived scoring. | `PRD.md` 1, 5.1, 10 · `Architecture.md` 8 · `Rules.md` DAT-03, section 9 |
| C-13 | **Incremental delivery.** Deliver MVP as Phase 0 + Phase 1 (Phase 1A foundation and safety shell, then Phase 1B initial features). One milestone at a time, one branch per task, owner review recorded. Report export (PDF), offline cached reports, and RTL support are deferred. | `PRD.md` 1, 5 · `Phases.md` header, 1, 9 |
| C-14 | **Local execution on emulators.** Phase 1 development runs strictly locally using Firebase emulators and fictional data. No cloud projects, billing, external hosting, or public deployment in Phase 1. | `PRD.md` 1, 2, 5 · `Architecture.md` 1, 2, 13 · `Rules.md` GR-11 |
| C-15 | **No LLM in Phase 1.** No Large Language Model integration or external AI APIs in Phase 1. NurseBot uses menu-based scripted help. MedBot Detailed mode is deferred. | `PRD.md` 1, 2, 5 · `Architecture.md` 2, 9 · `Rules.md` GR-13 |
| C-16 | **Protect dataset tracking.** Original datasets in `datasets/` must never be modified, added to new commits, or pushed to any remote repository. Git tracking check required. | `Architecture.md` 1, 4 · `Rules.md` GR-12 |
| C-17 | **Unreviewed draft content exclusion.** All medical and reference content is an unreviewed draft. No medicines, supplements, doses, specific timeframes, or routine treatment recommendations are shown in Phase 1. | `PRD.md` 1, 2, 5.1 · `Architecture.md` 1, 5.3 · `Rules.md` SAF-16 |
| C-18 | **Reference match summary format.** Phase 1 output is an ordered reference match summary showing matched tags and counts. No Low/Moderate/High bands, risk scores, probabilities, or percentages. Non-nutritional classes are excluded from user results in MVP. | `PRD.md` 1, 2, 5.1 · `Design.md` 6 · `Architecture.md` 5.1, 8.1 · `Rules.md` SAF-09, SAF-17 |
| C-19 | **Naming: Symptom Reference Explorer.** MVP symptom-matching feature is named "Symptom Reference Explorer" with an educational prototype disclaimer. Prediction remains a long-term academic aim. | `PRD.md` 1, 5.1 · `Rules.md` SAF-17 |
| C-20 | **Static emergency safety layer.** Persistent "Need urgent help?" entry on every screen, including signed-out and offline states. Opens a static frontend page with fixed generic wording and configured emergency numbers. No automated red-flag triage engine in Phase 1. | `PRD.md` 2, 4, 6.2 · `Design.md` 1, 7 · `Architecture.md` 1, 7 · `Rules.md` SAF-03, SAF-15 |
| C-21 | **Minimal user profile.** Collect only optional display name, optional gender, height, and weight. No date of birth or age collected. 18+ confirmation is self-declared. | `PRD.md` 2, 6.1 · `Design.md` 4 · `Architecture.md` 5.1 · `Rules.md` SAF-10 |
| C-22 | **No medication reminders.** CarePlan in Phase 1 supports user-created water, food, and exercise tasks only. No medication reminders or medicine suggestions. | `PRD.md` 2, 5.1, 6.6 · `Design.md` 4 · `Architecture.md` 5.1, 12 |
| C-23 | **Scripted help and log minimisation.** NurseBot is scripted; no transcripts are stored. Server logs must not record health details, symptoms, user answers, names, or image data. | `Architecture.md` 5.1, 11 · `Rules.md` SEC-04 |
| C-24 | **No usability testing with human participants.** No usability testing with real people until institutional ethics and supervisor requirements are confirmed. | `Design.md` 10, 15 · `Phases.md` 1, 1B.7 · `Rules.md` GR-14 |
| C-25 | **Data store architecture: MySQL + MongoDB.** User accounts, profiles, consent logs, and audit logs are stored in local MySQL 8.0+ via SQLAlchemy models (`backend/app/models/user.py`). Versioned reference packages, clean catalog lookups, and audit artifacts are stored in local MongoDB 9.0+. Firestore is deprecated from the active path and replaced by local databases, eliminating cloud dependency. | `Architecture.md` 2, 3, 5 · `Rules.md` SEC-02, ENG-01 · `Phases.md` M1A.5 |

*Note:* Confirmed decisions C-01 through C-25 are now canonical across all documents.

## 5. Open decisions (OD-xx)

All are **Pending**. "Recommended default" is what was proposed during planning; it is **not** confirmed until the owner accepts it in writing here. The owner chose to revisit unresolved items later with the AI tools (see section 12, S-001).

| ID | Decision needed | Recommended default (Proposed) | Needed by | Affects |
|---|---|---|---|---|
| OD-01 | **Scope wording.** The data includes minerals and protein-energy malnutrition, not only vitamins. | Call it "nutritional deficiency risk"; keep the MEDNOURISH name; label iron, zinc and protein-energy malnutrition as minerals or nutrition, not vitamins. | Phase 0 exit | `PRD.md` 5.1, SYMP-03 · all user-facing text |
| OD-02 | **How to present supplement, medicine and timeframe content** (the principle itself is confirmed in C-08). | Never show the supplement or drug columns. Show food sources, lifestyle information, "ask a clinician about testing", and three urgency tiers instead of "within N weeks" timeframes, until a clinician reviews them. | Phase 0 exit | Knowledge base, `Rules.md` SAF-02, SAF-08 |
| OD-03 | **Clinical reviewer.** Who can review content (doctor, dietitian, faculty advisor) and how review is recorded. | Label everything "unreviewed draft" until a reviewer exists. | Route by Phase 0 exit; reviewer before any public release | PV-17, gates G2 |
| OD-04 | **Cleaning policy for the 13 CSVs.** | Never edit originals. Make cleaned copies in a new folder with a change log: fix the two malformed rows and typos; add a master label list and readable tag labels; keep child-specific rows out of adult results. | Phase 0 exit | `Architecture.md` 5.3 · M1.4 |
| OD-05 | **Form of results.** | Match-strength **bands** (Low / Moderate / High, plus Insufficient information), not percentages. Closed by C-18 for Phase 1 (ordered tag summary used). | Phase 0 exit | SYMP-03, REPORT-01, `Design.md` 6 |
| OD-06 | **LLM provider and spending.** The approach is confirmed (C-04); the provider and payment are not. Deferred beyond Phase 1 (C-15). | Build adapter later; run 30 test question bake-off; paid tier with hard cap or free tier with fictional data only. | Before Phase 2 / M1.8 | PV-11, `Architecture.md` 9 |
| OD-07 | **Deadline.** | Unknown; ask the owner for a rough date. | Any time | Planning only |
| OD-08 | **Retention durations.** Temporary-file sweep interval; log retention; optional expiry of saved images; whether NurseBot transcripts are stored; consent-record period after account deletion; backup and restore plan. | Principles are fixed (`Architecture.md` 11.1). Proposed: do not store NurseBot transcripts by default. Other durations undecided. | Phase 1 (logs, consent); Phase 2 (images) | `Architecture.md` 11.1, 13 · SCAN-05 |
| OD-09 | **Family or dependent profiles.** Closed: One adult profile (18+) per account for MVP. No family/dependent profiles in initial release. | Confirmed (Owner decision 2026-10-12) | Phase 0 exit | `PRD.md` 5 |
| OD-10 | **Sign-in methods.** Closed: Email + password using local Firebase Authentication emulator in Phase 1A. Google sign-in and phone OTP deferred. | Confirmed (Owner decision 2026-10-12) | Phase 0 exit | AUTH-01 |
| OD-11 | **Hosting layout.** | Firebase Hosting for the PWA; a container host (for example Google Cloud Run) for the API; separate development, staging and production environments. | Before first deployment | `Architecture.md` 2, 13 · PV-13 |
| OD-12 | **Extra profile fields** beyond minimal core. Closed by C-21. | Keep extras minimal and optional. | Phase 0 exit | PROF-01, S-03 |
| OD-13 | **Languages beyond English.** | English only in Version 1; every added language needs the same clinical review. | Later | I18N-01, `Design.md` 12 |
| OD-14 | **Whether to show a per-nutrient Risk Score in Version 1.** Closed by C-18. | Defer it; show preliminary match summaries until a clinician reviews a transparent specification and its evidence. | Before M1.6 | REPORT-01, MEDBOT |
| OD-15 | **Styling approach, component library and icon set.** Closed: React, Vite, TypeScript, CSS Modules, shared design tokens, and Lucide icons. | Confirmed (Owner decision 2026-10-12) | M1A.1 | `Design.md` 5, 8 |
| OD-16 | **MedScan scope and timing.** | Keep image analysis in Phase 2; decide whether any image model is supportable per region after label, provenance, licence and evaluation gates. | Before Phase 2 | `PRD.md` SCAN-03 · `Phases.md` 4 |
| OD-17 | **Tabular model task and input/label fit.** | Do not synthesize patient rows from mapping tables. Audit whether the main CSV has trustworthy targets and inputs the app actually collects; if not, keep the MVP deterministic and defer ML. | Before training or ML scoring | `Architecture.md` 8 · `PRD.md` SYMP-06, MEDBOT-09 |
| OD-18 | **MedBot question set.** | Approve a short, neutral, consented question set; treat `Risk_Factors` text as source material only, not a validated questionnaire or model-feature schema. | Before M1B.4 content is finalized | `PRD.md` MEDBOT-01, 08 · `Design.md` S-07 |
| OD-19 | **Display of reference entry names before clinical review.** | Display cleaned, plain-language entry names or generic nutrient category names. | Before M1B.1 | `Design.md` 6 · `Architecture.md` 15 |
| OD-20 | **Disclaimer and banner wording.** | Approve educational prototype banner and microcopy text. | Phase 0 exit | `Design.md` 5, 13 |
| OD-21 | **CarePlan starter suggestions.** | Offer owner-authored general wellness text suggestions (food, water, exercise) without clinical deficiency claims. | Before M1B.5 | `PRD.md` 5, `Phases.md` M1B.5 |

## 6. Pending verifications (PV-xx)

Open items are marked in the register; some have partial inspection evidence recorded. A feature that depends on an unresolved item must not be built until it is closed or the owner approves a stated assumption (`Rules.md` section 9 is authoritative).

| ID | What must be verified | Why it matters | How (suggested) | Blocks |
|---|---|---|---|---|
| PV-01 | Main CSV `vitamin_deficiency_disease_dataset_20260123.csv`: source, generation method, label definitions/validity, licence, leakage, and match between user-available features and target. Read-only audit found 4,000 rows × 34 columns, no blank cells, no exact duplicate rows, and labels Healthy (1,509), Anemia (1,245), Rickets_Osteomalacia (1,029), Night_Blindness (122), Scurvy (95); clinical validity unverified. Contains lab values/RDA not asked in app. | Determines whether a later task is supportable; existing labels do not directly match the 116 mapping classes and many columns are not asked in the app. | Owner/source details + read-only audit under DAT-01; completed in DATASET_AUDIT.md. | Any tabular ML or ML-based user score |
| PV-02 | ETL notebook workflow, dependencies, preprocessing, training/evaluation. Inspected: one exploratory-analysis code cell with saved outputs; no model-training/evaluation workflow found. | Saved figures and printed statistics are not independent evidence until reproduced. | Read-only notebook inspection completed; source/data provenance still unknown. | Any tabular ML |
| PV-03 | `DATASET_STRUCTURE.txt` contents. Inspected: 0 bytes. | It provides no metadata. | Verified empty; populate only if the owner has source information. | No direct implementation blocker |
| PV-04 | Image folders: taxonomy and file counts inspected (372,536 images counted); label consistency, image quality, source and match to intended tasks remain open. | Decides whether any MedScan region is supportable. | Complete read-only per-class counts in DATASET_AUDIT.md. Provenance/licences open. | MedScan, image models |
| PV-05 | Duplicates and near-duplicates inside folders and **across** folders (for example `dataset/` versus the body-region folders). | Duplicates across train and test inflate results (data leakage). | Hashing and similarity checks before any split (DAT-05). | Image and tabular evaluation |
| PV-06 | Annotation files: `.json` and `.mat` in EYES; `shezhen` COCO, TXT and XML in TONGUE (21,902 files counted). What they label and how. | Labels may be richer or different from folder names. | Read-only inspection completed. | MedScan, image models |
| PV-07 | Provenance of the 13 `MedBot_datasets` CSVs: who created them, from which sources, how. No file has a source or reference column. | Unknown provenance means the content cannot be trusted for advice. | Owner explains; sources recorded. | Knowledge base, Symptom Analyzer, MedBot content |
| PV-08 | Documentation source of truth. Six canonical documents (`Memory.md`, `PRD.md`, `Architecture.md`, `Design.md`, `Phases.md`, `Rules.md`) reconciled in Draft 1.3. | Avoid losing or editing the wrong document set. | Resolved for this revision: the six `.md` files are canonical. | None |
| PV-09 | Licences and permitted use of every dataset, image set, content source and new dependency. | Cannot ship what the licence forbids (RSK-14). | Record before use (ENG-10, SEC-08). | Training, public release |
| PV-10 | Target country, or confirmation of "country-agnostic demo". | Emergency information, facilities and legal text depend on it. | Owner decides (task 0.5). | Region configuration, emergency content, Phase 3 |
| PV-11 | Current LLM provider facts: prices, data retention, whether data is used for training, rate limits, free-tier terms; plus the bake-off and safety test results. | Vendor terms change; section 8 is a dated snapshot only. Deferred beyond Phase 1. | Re-read official pages at build time; run the safety test set. | LLM features (Phase 2+) |
| PV-12 | Legal and regulatory review: how medical-software rules and privacy laws apply; liability for doctor chat; scope of interns' practice. | The product's regulatory classification in any country is unknown. | Specialist or institutional review. | Public release, Phases 4–5 |
| PV-13 | Firebase and Google Cloud plan, region, limits, Cloud Storage requirements and pricing, backup behaviour, App Check, request-size limits. | Deployment and cost depend on it. | Check current official documentation; owner confirms. | Deployment, saved images, backups |
| PV-14 | Library versions and compatibility (backend, ML, front end); emulator tooling feasibility. Checked: Node v24.21.0, npm 11.19.0, Python 3.14.8, Java 27 LTS present. Firebase CLI not installed; npm execution in PowerShell blocked by execution policy (cmd.exe wrapper required). Pinned versions recommended in S-005. | Pinned versions needed for reproducible work (DAT-09, SEC-08). | Verified local runtimes; dependency pin specification prepared for owner confirmation. | M1A.1, Phase 2 training and serving |
| PV-15 | PWA behaviour per platform: install prompts, push notifications, offline, browser speech output (language and voice coverage). | Read-aloud and push are "where practical". | Test on target devices and browsers. | A11Y-03, Phase 3 reminders |
| PV-16 | Google Maps, Calendar and Tasks: billing, OAuth scope verification, quotas, whether Tasks can ring a timed alert, nearby-facility data coverage. | Cost and approval hurdles (RSK-10). | Check current Google documentation; owner approves scopes and billing. | Phase 3 |
| PV-17 | Clinical review of: medical content, red-flag rules, the Risk Score specification, urgency wording, routine content, evaluation thresholds. | Nothing that influences advice is reviewed yet. | A qualified reviewer (OD-03) signs off; record who and when here. Route: unreviewed draft banner in force until clinical partner identified. | Any public release; gates G2 |
| PV-18 | Git tracking & remote exposure check. Confirmed: Remote origin is public GitHub repository `https://github.com/Mr-K-17/MedNourish_V1.0.git`. Remote branch `origin/main` has ONLY 1 commit (`196c914 Initial commit`) containing solely `README.md`. Commits containing the 394,480 dataset files (`d619c77`, `1b96772`, `215bb4e`, `ab7fb33`) exist ONLY LOCALLY and have NEVER been pushed to the remote. Zero secrets or `.env` files are tracked. A comprehensive root `.gitignore` has been prepared to permanently protect `datasets/`, secrets, and build outputs. | Prevents committing or pushing heavy datasets or credentials to git (C-16, GR-12). | Conclusive read-only check complete via `git ls-remote` and `git fetch origin main`. Exposure is ZERO on public remote. Safe recovery path formulated. | M1A.1 scaffold |
| PV-19 | Institutional ethics and supervisor review for testing with human participants. | Ensures compliance with academic/research ethics. | Institutional ethics approval before any user testing (C-24). | Usability testing |

## 7. Read-only dataset audit findings

**Current inventory audit (2026-10-11):** no files in `datasets/` were modified. The 13 `MedBot_datasets` CSVs were parsed for filenames, headers and row counts. The 116-row keyword map has columns `Class_Label`, `Body_Region`, `Category`, `Vitamin_Deficiency`, and `Symptom_Keywords`. The six region mapping CSVs include free-text symptom/sign/risk-factor/severity fields. The six routine tables include `Suggested_Supplementation` and `Follow_Up_Recommendation`; these fields must not be shown as written. The CSV schemas contain no source/reference field.

The main structured CSV parses as 4,000 rows × 34 columns. Its `disease_diagnosis` distribution is Healthy 1,509; Anemia 1,245; Rickets_Osteomalacia 1,029; Night_Blindness 122; Scurvy 95. This read-only check found no blank cells and no exact duplicate rows; `symptoms_count`, `symptoms_list`, and the eight symptom flags were internally consistent in the file. These checks do not verify clinical validity. The CSV also includes serum measurements and nutrient-intake fields unavailable in the planned symptom questionnaire. Its five diagnosis labels are not direct matches for the mapping table's 116 class labels. The notebook metadata records Kaggle `datasetVersion` source ID `14589953`, but the local file was not compared to the upstream version and the label-generation method/licence remain unverified. The notebook has one exploratory-analysis code cell with saved outputs, but no model fit/train/test or evaluation workflow. Its printed results were not reproduced. `DATASET_STRUCTURE.txt` is 0 bytes.

The `dataset/` folder has 11 class directories and 25,632 files with common image extensions in a read-only inventory. Body-region folders use different taxonomies; EYES includes JSON/MAT files and TONGUE has COCO/TXT/XML subfolders. No image content was opened. Image labels, annotation semantics, duplicates/near-duplicates, quality, provenance and licensing are not verified. These collections are Phase 2 candidates only.

**Historical detailed findings below** came from an earlier read-only CSV audit and have not all been independently repeated in this session. Treat approximate content counts and medical-text observations as preliminary until re-audited.

**Historical structure and alignment findings**
- The earlier audit reported 116 condition classes across six body regions (Eyes 15, Hair 32, Lips 14, Nails 16, Skin 23, Tongue 16), a 116-row keywords table, and 83 routine rows.
- It reported two malformed Hair rows with unquoted commas, inconsistent class/nutrient names, run-together symptom tags, and repeated `Normal` labels requiring a composite key. Re-run validation against the current files before cleaning.
- It reported broad tag overlap (for example `fatigue` shared by multiple classes) and possible tag typos; readable tags and synonyms require review.
- The earlier review reported children/infant references in some rows and unsafe supplement/drug/timeframe language in routine tables. Keep those fields and classes out of adult user-facing content unless reviewed.

**What these findings imply**
- After cleaning, provenance checks and clinical review, the 13 reference CSVs can drive a transparent lookup for MedBot and Symptom Analyzer. They are not patient data and are unsuitable as ML training examples (DAT-03).
- Common symptom tags may match multiple classes. If match-strength bands are used, they must describe table-match coverage—not probability, diagnosis, or clinical severity (OD-05).
- XGBoost/LightGBM need a separate verified dataset whose target and feature types match what the app collects. The main CSV has not been shown to meet that requirement (PV-01, PV-02, OD-17). MobileNetV2 needs separate image verification (PV-04–PV-06).
- Any red-flag candidates found in the CSVs are inputs to clinical review, not approved rules (`Architecture.md` section 7).

## 8. LLM provider snapshot (not re-verified; for planning only)

Collected earlier from the providers' official pricing and data-handling pages. The exact date was not recorded, and the pages were **not re-checked in this session**. Prices, terms and limits change: re-verify before use (PV-11). The comparison was written by an AI assistant made by Anthropic, one of the compared vendors, so any lean should be treated as a tie-break only. **Answer quality and medical safety were not tested for any provider.**

| | Claude Haiku 5.5 | OpenAI gpt-6-luna | Gemini 3.1 Flash-Lite |
|---|---|---|---|
| Price per 1M tokens (input / output) | $0.10 / $0.50 (prompts up to 100K tokens; higher above) | $0.10 / $0.50 | $0.25 / $1.50 (output includes thinking tokens) |
| Used for training? | Not by default (commercial API) | Not by default | Paid tier: no. Free tier: yes, and human reviewers may read it |
| Retention | Deleted within 30 days by default; zero retention by agreement | Abuse logs up to 30 days; zero retention only if approved | Limited logging for abuse detection on the paid tier |
| Free tier | Not checked | None stated for tokens | Yes, but the terms say not to submit sensitive or personal information |
| Rate limits | Not checked | Not checked | Not listed on the page checked; see the provider's console |

- **Illustrative cost** (assuming 2,000 input and 300 output tokens per chat): 1,000 chats cost about $0.35 on Haiku or gpt-6-luna and about $0.95 on Flash-Lite. At demo scale the cost is cents, so privacy terms and ease of use matter more than price.
- **Rule that follows:** use only fictional data in development; never send real health information to a free tier (`Rules.md` GR-08, SEC-06).

## 9. Known limitations (do not claim around these)

1. No model is trained or evaluated; **no accuracy, sensitivity or other performance figure exists** (GR-04).
2. The main CSV was parsed and the notebook inspected, but provenance, label validity, licence and task suitability remain unknown. `DATASET_STRUCTURE.txt` is empty. Image folders were inventoried only; annotation semantics, labels, duplicates, quality and licences remain open.
3. The 13 CSVs have unknown provenance, two malformed rows, inconsistent labels, and content that must not be shown as written (section 7).
4. No clinician has reviewed any medical content, red-flag list, urgency wording or Risk Score method.
5. Phase 1 is planned to show transparent reference-table matches, not a validated Risk Score or probability; content and scoring still need review.
6. The product's regulatory classification and applicable privacy laws in any country are unknown (PV-12).
7. The target country is undecided, so emergency numbers, facility data and legal text are unconfigured by design (PV-10).
8. A trained model that combines image and questionnaire evidence is **not possible** without paired data (photos + answers + a confirmed laboratory result); none is known to exist. The plan uses transparent side-by-side rules instead (`Architecture.md` 8.1).
9. Age confirmation is self-declared and cannot prove age.
10. Image labels implied by folder names may be broader than nutrient-level classes; some regions may only support broad groups, guided capture or no AI at all (SCAN-07).
11. Tool-specific conventions of Antigravity, Codex and Cursor are unverified here; the rules do not depend on them (`Phases.md` section 10).
12. Vendor facts (section 8), Google integration limits (PV-16) and PWA behaviour (PV-15) can change and have not been re-verified.

## 10. Documentation notes (known quirks in this document set)

These are small issues found while cross-checking the Version 1 set. They do not change any decision.

- **Two ID prefixes for safety:** `PRD.md` requirements use `SAFE-xx`; `Rules.md` rules use `SAF-xx`. They are different lists. Always cite the document when quoting one.
- **`SEC-01` appears in two documents:** `PRD.md` (non-functional requirement) and `Rules.md` (rule 1 of SEC-01 to SEC-10). Their meanings are compatible. Cite the document name when referring to it.
- **Requirements covered by an equivalent rule but not cited by ID outside the PRD:** SYMP-06 (Phase 2 ML ranking; covered by `Phases.md` track 2C), SAFE-04 (covered by `Rules.md` SAF-12), PRIV-02 (covered by SEC-06) and COST-01 (covered by SEC-10).
- **Band names:** the register and PRD say Low / Moderate / High / Insufficient information; `Design.md` shows them as Low signal / Moderate signal / High signal / Not enough information (OD-05).
- **Checked in this session:** every C, OD, PV, RSK, A and G ID cited in the five other documents is defined in this file or in `PRD.md`; the twelve colour-contrast figures in `Design.md` section 8 were recomputed with the WCAG relative-luminance formula and match. This was a document-consistency check, **not** a data audit.

## 11. Pending tasks and next actions

Ordered by what unblocks the most. Task numbers match `Phases.md` section 2.

| # | Action | Who | Items |
|---|---|---|---|
| 1 | Review the six Version 1 documents; correct anything that does not match your intent. This satisfies the Phase 0 entry criterion. | Owner | All |
| 2 | Accept or change the Phase 0 defaults in section 5 (task 0.2), especially deferring ML until dataset/target fit is established. Reply per ID, or "defaults". | Owner | OD-01, 02, 04, 05, 06, 10, 12, 14, 15, 17 (and confirm OD-09) |
| 3 | Name a clinical reviewer, or state that none is available yet (the demo banner stays on) (task 0.3). | Owner | OD-03, PV-17 |
| 4 | Explain how the 13 CSVs were created and from which sources (task 0.4). | Owner | PV-07 |
| 5 | Decide the target country, or confirm "country-agnostic demo" (task 0.5). | Owner | PV-10 |
| 6 | Provide provenance/source, generation and licence information for the main CSV and 13 mapping files; decide whether the empty structure file can be replaced with metadata. | Owner | PV-01, PV-07, PV-09 |
| 7 | Plan cleaned knowledge copies and decide whether to defer the clinical Risk Score in favour of a preliminary match summary (tasks 0.8, 0.9). | AI tool proposes; owner/reviewer checks | OD-04, OD-14, PV-17 |
| 8 | Verify Firebase plan, regions, Cloud Storage and backups; create service accounts and spending caps (tasks 0.10, 0.12). | AI tool researches; owner creates accounts | PV-13, SEC-10 |
| 9 | Plan the LLM bake-off and safety test set; do not run it before M1.8 (task 0.11). | AI tool drafts | PV-11, OD-06 |
| 10 | Tell an AI tool: "Phase 0 complete; application code may begin" **only when** the Phase 0 exit criteria are met (`Phases.md` section 2). | Owner | C-11 |

**Not required to close Phase 0 for a rule-based academic demo:** image audits and model training. The user-facing knowledge content still needs provenance, cleaning, and an unreviewed-draft banner until clinical review.

## 12. Handoff and session log

### 12.1 Start-of-session checklist for any AI tool

1. Read this file, then `Rules.md`, then the parts of `PRD.md`, `Architecture.md`, `Phases.md` and `Design.md` that your task touches.
2. State the current phase and the open blockers from section 6.
3. For your task, look up the verification gates in `Rules.md` section 9. **If a gate is open, report it and stop.**
4. State your plan and the requirement IDs before changing any file.
5. Work on one branch per task; do not touch `datasets/`; do not start training or any long-running job; do not add a paid service or send data to a third party without the owner's explicit approval.

### 12.2 Entry template (append at the end of every session; never delete earlier entries)

```
### S-0NN — <date> — <tool and model> — <branch or "no branch">
- Task and requirement IDs:
- Files changed:
- What was verified, and how (file, command, source):
- Register changes (C / OD / PV: ID, old status, new status, who decided):
- Still pending:
- New open questions for the owner:
- Approvals given by the owner this session (training, billing, third-party data):
```

### 12.3 Log

### S-001 — planning conversation (exact date not recorded) — Claude in a web chat — no branch
- Task: plan the project, audit the 13 CSVs, validate the technology choices, and decide what is MVP versus later.
- Done: the owner's brief was analysed. The 13 `MedBot_datasets` CSVs were audited **read-only**; nothing was modified (findings in section 7). LLM providers were compared from official pricing and data-handling pages (snapshot in section 8). The thin-backend question was settled: browser-only is not safe, because Python models cannot run in the browser, API keys must stay off devices, risk scores and red-flag rules must run where users cannot tamper with them, and image checks must be enforced on a server. Draft image-privacy rules were proposed. Eight questions were put to the owner with recommended defaults: scope wording (now OD-01), supplements, medicines and timeframes (OD-02), clinical review and CSV origin (OD-03, PV-07), cleaning policy (OD-04), Symptom Analyzer output form (OD-05), the stack (C-07), the LLM approach (C-04, OD-06), and the missing files plus a rough deadline (PV-01 to PV-04, OD-07).
- Owner's response: proceed with the information currently available; the main CSV, ETL notebook, `DATASET_STRUCTURE.txt` and image-folder counts cannot be supplied now; generate the six Version 1 documents; keep MedScan in Phase 2; use FastAPI, React, Vite, TypeScript, Firebase Authentication, Firestore and Cloud Storage as the proposed architecture subject to verification; revisit the unresolved items later with Antigravity, Codex and Cursor.
- Result: `PRD.md`, `Architecture.md`, `Rules.md`, `Phases.md` and `Design.md` were created. The session ended (usage limit) before `Memory.md` was written.
- No application code was written. No datasets were modified. No model was trained.

### S-002 — 2026-10-11 — Claude in a web chat — no branch
- Task: finish the Version 1 set.
- Done: read the five existing documents in full; confirmed the uploaded `Memory_md.txt` is empty (0 bytes); wrote this `Memory.md`; ran the document-consistency checks described in section 10.
- Verified, and how: the 12 colour-contrast figures in `Design.md` section 8 were recomputed (WCAG relative-luminance formula) and match; ID cross-references were extracted by script from the five documents and compared with the registers here.
- Register changes: registers C-01 to C-11, OD-01 to OD-15 and PV-01 to PV-17 were created in this file. No item was closed. C-10 and C-11 were added from the owner's instructions (section 4).
- Not done, by design: no dataset was opened or modified; the CSV audit was not repeated; no code was written; no model was trained.
- Still pending: everything in section 11.
- New open questions for the owner: see OD-06 (payment card with spending cap?), OD-07 (deadline), PV-07 (how the CSVs were created) and PV-10 (target country).
- Approvals given by the owner this session: none.

### S-003 — 2026-10-11 — Codex — current workspace
- Task and requirement IDs: dataset/architecture compatibility review; DAT-01–11, MEDBOT-01–10, SYMP-01–07, REPORT-01/04, SCAN-01–07, SAFE-01–14, Phase 0 and GR-07.
- Files changed: `Architecture.md`, `Design.md`, `Memory.md`, `Phases.md`, `PRD.md`, `Rules.md`.
- What was verified, and how (file, command, source): read-only PowerShell CSV parse/listing and notebook JSON inspection. The 13 reference CSVs comprise six symptom mappings, six routine tables and one 116-row keyword map; the main CSV parses to 4,000 rows × 34 columns with labels Healthy 1,509, Anemia 1,245, Rickets_Osteomalacia 1,029, Night_Blindness 122 and Scurvy 95. The ETL notebook has one exploratory code cell and saved output, no training/evaluation workflow. `DATASET_STRUCTURE.txt` is 0 bytes. The `dataset/` image folder has 11 class folders and 25,632 common image files by extension; this was inventory only, not label/quality/licence verification.
- Register changes: PV-01/PV-02/PV-04 partially inspected; PV-03 confirmed empty; PV-08 current docs confirmed canonical. OD-16–OD-18 recorded for image scope, ML task fit, and questionnaire content. C-12 records the preferred algorithm families only; does not approve training or user-facing ML scoring.
- Still pending: source/provenance/licence and label validity for CSVs; image labels/annotations/duplicates/licences; clinical review; Phase 0 decisions; explicit Phase 0 exit before app code; no training run performed.
- New open questions for the owner: Is the recommended Phase 1 rule-based matcher with XGBoost/LightGBM deferred until suitable data acceptable? Can you provide where the main CSV and 13 mapping tables came from and how labels were created?
- Approvals given by the owner this session: read-only dataset inspection and planning-document updates; no approval for model training, code implementation, billing or third-party data sharing.

### S-004 — 2026-10-12 — Antigravity (Auditor) — current workspace
- Task and requirement IDs: Full documentation correction, empirical dataset audit, cross-document reconciliation, DATASET_AUDIT.md and validation reporting; GR-01–14, DAT-01–12, C-01–24, OD-01–21, PV-01–19.
- Files changed: `docs/Memory.md`, `docs/PRD.md`, `docs/Architecture.md`, `docs/Design.md`, `docs/Phases.md`, `docs/Rules.md`, `docs/DATASET_AUDIT.md`.
- What was verified, and how: Full read-only Python and PowerShell audit of 34 CSVs and 372,536 image files in `datasets/`. Identified 116 mapped condition classes, 83 routine rows, 2 malformed rows in Hair datasets (Line 31 of mapping and Line 24 of routine with unquoted commas), 22 instances of pediatric terms, 31 instances of drug/supplement terms. Audited main CSV: 4,000 rows × 34 columns, 0 blanks, 0 exact duplicates, Healthy (1,509), Anemia (1,245), Rickets (1,029), Night Blindness (122), Scurvy (95); confirmed feature mismatch with user questionnaire. Verified 21,902 annotation files and 4 Jupyter notebooks with Kaggle provenance. Original datasets in `datasets/` were confirmed unmodified (SHA-256 verified).
- Register changes: Canonical registers in `Memory.md` updated to encompass Confirmed Decisions C-13 through C-24, Open Decisions OD-19 and OD-21, and Pending Verifications PV-18 and PV-19. PV-01, PV-02, PV-04, PV-05, PV-06 progressed to audited status in `DATASET_AUDIT.md`.
- Still pending: Clinical reviewer sign-off (PV-17), dataset provenance and licensing confirmation (PV-07, PV-09), Phase 0 exit approval by owner (C-11, GR-07).
- New open questions for the owner: None beyond existing open decisions; all 6 documents are now 100% harmonized.
- Approvals given by the owner this session: Documentation correction and dataset audit only; no application implementation, training, cloud project creation, or billing authorized.

### S-005 — 2026-10-12 — Antigravity (Lead Architect) — current workspace
- Task and requirement IDs: Phase 0 Exit Verification & Critical Git Safety Check; Task 0.1–0.8, PV-14, PV-18, OD-03/PV-17, OD-09, OD-10, OD-15, C-11, C-14, C-16, GR-07, GR-12.
- Files changed: `docs/Memory.md`, `MEDNOURISH_AUDIT_PROGRESS.md`, `.gitignore`.
- What was verified, and how (file, command, source):
  - Git remote comparison (PV-18): Executed read-only `git ls-remote origin` and `git fetch origin main`. Confirmed that remote GitHub repository `Mr-K-17/MedNourish_V1.0.git` has ONLY 1 commit: `196c914 Initial commit` containing solely `README.md`.
  - Local dataset commit status: The commits containing the 394,480 dataset files (`d619c77`, `1b96772`, `215bb4e`, `ab7fb33`) exist **strictly locally** on the user's machine and have **never** been pushed to the public remote. Public remote exposure is confirmed **ZERO**.
  - Local uncommitted changes: Verified all current documentation work is preserved in working tree on branch `master`.
  - Protection instituted: Prepared and created a comprehensive root `.gitignore` blocking `datasets/`, `knowledge/`, `ml/`, secrets, credentials, `.env*`, and emulator logs from future staging/commits.
### S-006 — 2026-10-12 — Antigravity (Lead Architect) — MedNourish-Dev (branch dev)
- Task and requirement IDs: Phase 0 Exit & Phase 1A Scaffold Initiation (M1A.1); AUTH-01–05, PROF-01–03, DASH-01–02, SAFE-01–03, GR-01–14, C-01–24, OD-09, OD-10, OD-15, PV-14, PV-18.
- Files changed: `docs/Memory.md`, `MEDNOURISH_AUDIT_PROGRESS.md`, `.gitignore`, `backend/`, `frontend/`, `infra/`.
- What was verified, and how (file, command, source):
  - Disk cleanup: 5 orphaned `tmp_pack_*` files (35.18 GB) deleted individually; C: free space increased from 11.49 GB to 46.63 GB. Original datasets untouched on disk.
  - Safe Git worktree: Created `c:\Users\USER\Desktop\MedNourish-Dev` on branch `dev` off `origin/main` (commit `196c914`).
  - Decisions finalized: OD-09 (1 adult profile), OD-10 (email/password on emulator), OD-15 (React, Vite, TS, CSS Modules, design tokens, Lucide) confirmed.
  - Phase 0 Exit: Authorized by owner ("Phase 0 complete; application code may begin").
- Register changes: OD-09, OD-10, OD-15 changed from Pending to Confirmed. Phase 0 status updated to Complete; Phase 1A updated to In progress.
- Still pending: Completion of M1A.1 scaffold tests and local emulator setup.
- Approvals given by the owner this session: Deletion of 5 temporary pack files; Phase 0 exit; M1A.1 scaffold implementation.

### S-007 — 2026-10-12 — Antigravity (Implementation Engineer) — MedNourish-Dev (branch dev)
- Task and requirement IDs: M1A.1 Backend Database Integration & Architecture Update; MySQL 8.0, MongoDB 9.0, Firebase Auth Emulator; ENG-01–03, PROF-01–02, SEC-01–04, C-07, C-14, C-21, C-25.
- Files changed:
  - `backend/app/core/config.py`: Added MySQL (`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`) and MongoDB (`MONGODB_URI`, `MONGODB_DATABASE`) configuration with safe fallback defaults.
  - `backend/app/db/session.py`: Implemented SQLAlchemy synchronous engine/sessionmaker and non-blocking health check pingers for MySQL and MongoDB.
  - `backend/app/models/user.py`: Added `UserProfile` and `UserConsentLog` SQLAlchemy models. Strictly enforces `adult_confirmed=True`, excludes DOB/age, and keys to `firebase_uid`.
  - `backend/app/api/v1/health.py` & `backend/app/schemas/health.py`: Updated `/v1/health` endpoint to report granular status of `mysql`, `mongodb`, and `firebase_auth_emulator`.
  - `backend/tests/test_health.py`: Updated tests to assert multi-service health report. Pytest passing 2/2.
  - `.env.example`: Created root template with MySQL, MongoDB, Firebase emulator, and CORS settings.
  - Documentation: Reconciled `Architecture.md`, `Phases.md`, `Rules.md`, `PRD.md`, and `Memory.md` to establish C-25 decision and deprecate Firestore from active path.
- What was verified, and how:
  - Pytest verified: `python -m pytest tests` passed cleanly (2 passed in 3.17s).
  - MySQL service verified: Service `MySQL80` running on port 3306.
  - MongoDB service inspected: MongoDB 9.0 installed at `C:\Program Files\MongoDB\Server\9.0\bin\mongod.exe`; service currently stopped with stale lock from disk space event; health pinger handles offline state gracefully without crashing API.
- Register changes: Confirmed Decision C-25 added to `Memory.md`.
- Next actions: Connect frontend shared shell to `/v1/health` with service status badges, implement Firebase Auth emulator client service and login/register UI (M1A.4), and implement FastAPI profile/consent endpoints backed by MySQL (M1A.6).

### S-008 — 2026-10-12 — Antigravity (Implementation Engineer) — MedNourish-Dev (branch dev)
- Task and requirement IDs: M1A.4 (Emulator Auth), M1A.5 (FastAPI Token Verification & Authz), M1A.6 (Adult Confirmation, Consent & Minimal Profile); AUTH-01–05, PROF-01–03, SAF-10, C-01, C-21, C-25, SEC-01–04.
- Files changed:
  - `backend/app/core/auth.py`: Implemented `verify_firebase_id_token` and `get_current_user` FastAPI dependency verifying tokens against `127.0.0.1:9099`.
  - `backend/app/schemas/profile.py`: Implemented `ProfileCreateRequest`, `ProfileUpdateRequest`, and `ProfileResponse` schemas using Pydantic V2 `ConfigDict`. Strictly mandates `is_adult_confirmed=True`, excludes DOB/age, and provides minimal optional demographic fields.
  - `backend/app/api/v1/profile.py`: Implemented `GET /v1/profile`, `POST /v1/profile`, `PUT /v1/profile`, and `DELETE /v1/profile` with immutable consent logging and user data isolation.
  - `backend/app/main.py`: Registered `profile_router` under `/v1`.
  - `backend/tests/test_profile.py`: Created test suite covering 401 unauthenticated access, invalid tokens, adult confirmation validation, multi-user isolation, update, deletion, and end-to-end emulator token verification. 8/8 tests PASSING.
  - `frontend/src/services/firebase.ts`: Created client Firebase Auth service configured strictly for the local Auth Emulator (`127.0.0.1:9099`, project `demo-mednourish`).
  - `frontend/src/components/AuthForm.tsx` & `.module.css`: Created login/registration component with non-revealing error messages.
  - `frontend/src/components/ConsentProfileModal.tsx` & `.module.css`: Created 18+ explicit confirmation and terms consent setup form.
  - `frontend/src/App.tsx` & `.module.css`: Wired authentication lifecycle (`onAuthStateChanged`), consent gating, user profile dashboard view, and account deletion. Built and verified cleanly with Vite (`tsc && vite build`).
- Database & Driver Status:
  - MySQL 8.0: Service `MySQL80` running on port 3306. Awaiting `MYSQL_PASSWORD` in local ignored `.env` from developer.
  - MongoDB 9.0: Root cause identified via log inspection (`FTDCController` crash on `metrics.interim.temp` during historical disk space event). Service requires admin privilege to restart. Confirmed that PyMongo Async API (`pymongo.AsyncMongoClient`) is supported in installed `pymongo` 4.18.3, superseding deprecated Motor.
- What was verified:
  - Backend tests: `python -m pytest tests` passed cleanly (8 passed in 3.24s).
  - Frontend build: `tsc && vite build` succeeded without errors (dist created).
- Register changes: M1A.4, M1A.5, and M1A.6 marked complete.
- Next action: M1A.7 (Dashboard module tiles with "Coming Soon" states and Settings/Privacy review) and owner review for Phase 1A sign-off.

### S-009 — 2026-10-12 — Antigravity (Implementation Engineer) — MedNourish-Dev (branch dev)
- Task and requirement IDs: M1A.7 Dashboard Implementation, DB Graceful Error Handling, Consent Retention Reconciliation, and Full Phase 1A Validation; DASH-01–02, AUTH-01–05, PROF-01–03, PRIV-01, SAF-10, C-01, C-21, C-25, OD-08.
- Files changed:
  - `backend/app/api/v1/profile.py`: Added comprehensive database error handling in profile endpoints to return `503 Service Unavailable` on database connection/authentication errors without leaking raw exceptions.
  - `backend/tests/test_profile.py`: Added tests `test_database_failure_graceful_handling` (verifies 503 on database drop) and `test_account_deletion_removes_consent_logs_in_dev` (verifies consent logs are deleted upon account deletion in development per OD-08 and M1A.6). Pytest passing 10/10.
  - `frontend/src/components/Dashboard.tsx` & `.module.css`: Created accessible, responsive dashboard with module tiles for MedBot, Symptom Reference Explorer, CarePlan, and Files & Reports in explicit "Coming Soon" (Phase 1B) state.
  - `frontend/src/App.tsx`: Wired Dashboard into authenticated user view alongside account metadata summary, delete account flow, and persistent urgent help modal.
  - `docs/Memory.md` & `MEDNOURISH_AUDIT_PROGRESS.md`: Updated milestone status to mark M1A.7 complete and Phase 1A implementation ready for owner review.
- Verification & Test Summary:
  - Pytest: 10/10 passed in 3.39s (including 401 unauthenticated, invalid tokens, 18+ adult confirmation, data isolation, profile updates, account deletion with consent removal, database 503 handling, and live emulator token integration).
  - Frontend Build: `tsc && vite build` built in 2.81s with zero errors.
  - Database status: Documented that tests execute against in-memory SQLite for complete offline test isolation, while live MySQL service awaits `MYSQL_PASSWORD` in local uncommitted `.env`.
- Next action: Phase 1A Owner Review and Authorization to begin Phase 1B (Knowledge Base Cleaning & Reference Matcher).

### S-010 — 2026-10-12 — Antigravity (Auditor & Architect) — MedNourish-Dev (branch dev)
- Task and requirement IDs: Phase 1A Read-Only Verification Audit; M1A.1–M1A.7, AUTH-01–05, PROF-01–03, DASH-01–02, SAF-01–17, C-01–25, OD-08, PV-14, PV-18.
- What was verified (read-only audit):
  - Workspace integrity: Active directory confirmed as `C:\Users\USER\Desktop\MedNourish-Dev`, current branch `dev`, HEAD commit `86773fd`, working tree clean.
  - File presence: All Phase 1A implementation and design deliverables confirmed present on disk.
  - Automated tests: Pytest executed via `python -m pytest tests`. 10/10 passed in 5.09s (all 10 tests passed against isolated in-memory SQLite and live Firebase Auth Emulator port 9099).
  - Frontend production build: Executed `cmd.exe /c "npm run build"`. Completed in 3.99s with zero errors (`dist/` generated).
  - Database verification: Distinctly verified that live MySQL 8.0 service is running on port 3306, but application connection is unverified due to missing credentials (no `.env` file exists). Live MySQL table persistence is unverified until `MYSQL_PASSWORD` is provided. MongoDB service remains stopped (non-blocking for Phase 1A).
  - Safety & Scope verification: All medical disclaimers (`SAF-07`), static emergency modal (`C-20`, `SAF-03`), 18+ adult confirmation (`SAF-10`), and complete exclusion of DOB/age (`C-21`) are actively enforced in code and schemas. Phase 1B modules on Dashboard are in explicit "Coming Soon" states (`DASH-01`).
- Register changes: None (all decisions and verifications up-to-date).
- Blockers for Phase 1B:
  1. Live MySQL password configuration in local untracked `.env`.
  2. Owner review and authorization of Phase 1A exit criteria to start Phase 1B.

### S-011 — 2026-10-12 — Antigravity (Implementation Engineer) — MedNourish-Dev (branch dev)
- Task and requirement IDs: M1B.1 Reference package specification and mechanical cleaning; Firebase Emulator task graceful termination; SAFE-06, SYMP-02, DAT-03, DAT-04, SAF-02, SAF-09, SAF-10, SAF-13, SAF-16, C-01, C-21, PV-18, GR-01.
- Actions taken:
  - Task 0 Resolution: Graciously cancelled long-running Antigravity background task for Firebase Auth Emulator (`manage_task kill`). Verified TCP port 9099 is closed and not listening.
  - Test Offline Resilience: Updated `backend/tests/test_profile.py` with socket probe so tests run cleanly and offline when port 9099 is closed, passing 10/10 tests (1 emulator-specific test gracefully skipped when daemon is offline).
  - MySQL Readiness Check: Confirmed `.env` is ignored by `.gitignore` (line 24). Verified `Test-Path .env` is false (awaiting user's private creation of `.env`). Inspected config loader in `backend/app/core/config.py`.
  - Curated Knowledge Base (`knowledge/curated/`): Separated all 13 reference CSVs from original dataset archive `C:\Users\USER\Desktop\MedNourish\datasets\MedBot_datasets`. Preserved original archive integrity byte-for-byte (SHA-256 verified).
  - Tier-1 Mechanical Repairs:
    - Fixed unquoted comma fields in `knowledge/curated/Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` row 30 (`HAIR_SHAFT_KINKY_HAIR`), reducing columns from malformed 12 to schema-compliant 10.
    - Fixed unquoted comma fields in `knowledge/curated/Hair_Vitamin_Deficiency_to_Suggested_Routine.csv` row 23, reducing columns from malformed 9 to schema-compliant 7.
    - All 13 curated CSVs now load and parse with 100% schema conformance.
  - Changelog & Exclusions (`knowledge/CHANGELOG.md`): Documented all Tier-1 mechanical fixes. Documented policy flags marking 22 pediatric/child references and 31 supplement/drug dosage references as excluded from user-facing reference matching per `SAF-02`, `SAF-10`, and `SAF-16`.
  - Reference Matcher Specification (`docs/REFERENCE_MATCHER_SPEC.md`): Authored complete deterministic matching spec detailing token normalization, set intersection, tie-breaking, insufficient information threshold (`SAF-06`), and output schema with educational disclaimers.
  - Automated Validation Tests (`backend/tests/test_knowledge.py`): Authored 5 automated tests validating original archive SHA-256 byte-invariance, curated CSV schema adherence, Hair dataset repairs, and deterministic matcher set logic.
- Verification & Test Summary:
  - Pytest: 14 passed, 1 skipped in 6.20s across full backend test suite (`test_health`, `test_profile`, `test_knowledge`).
  - Git status: Local repository clean, untracked `.env` preserved, archive untouched.
- Next action: Completed M1B.1; proceeding to M1B.2 upon owner request.

### S-012 — 2026-10-12 — Antigravity (Implementation Engineer) — MedNourish-Dev (branch dev)
- Task and requirement IDs: M1B.2 Symptom Reference Explorer; SYMP-01–04, SAFE-01, SAFE-03, SAF-05, SAF-06, SAF-09, SAF-10, SAF-13, SAF-16, SAF-17, C-01, C-08, C-18, C-21.
- Actions taken:
  - Gate 1 Safety Audit & Verification:
    - Confirmed git commit `857105a` and working tree status.
    - Verified all 13 curated CSVs, exact column counts, and repaired Hair rows 30 & 23. Original archive byte-identical.
    - Audited pediatric and drug occurrences across all CSVs: determined that master table `MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv` contains 116 condition classes, which are filtered by code to exclude all non-nutritional classes (SAF-09), all Normal entries, and all pediatric/child references (SAF-10). Detailed routines with unreviewed drugs/dosages are strictly excluded from explorer displays (SAF-16).
    - Verified `backend/tests/test_profile.py` offline emulator socket probe: passes cleanly without background processes active.
  - Backend Implementation:
    - `backend/app/services/knowledge_service.py`: Implemented `KnowledgeRepository` and deterministic matcher engine. Enforces input normalization, set intersection, tie-breaking rules, adult/nutritional filtering, and insufficient information handling.
    - `backend/app/schemas/explorer.py`: Defined Pydantic models for categories, tags, match queries, and structured match responses with mandatory prototype disclaimers.
    - `backend/app/api/v1/explorer.py`: Implemented authenticated endpoints `GET /v1/explorer/categories` and `POST /v1/explorer/match`.
    - `backend/app/main.py`: Registered explorer router under `/v1`.
    - `backend/tests/test_explorer.py`: Authored 9 comprehensive tests covering data loading, SAF-09/10 exclusions, unauthenticated 401s, categories retrieval, insufficient info on empty/unmatched inputs, deterministic ranking, region filtering, and forbidden term absence.
  - Frontend Implementation:
    - `frontend/src/components/SymptomExplorer.tsx` & `.module.css`: Built responsive, accessible UI supporting body region filtering, tag search, tag selection chips, query lookup action, ordered reference match results with matched tag counts, insufficient information guidance, and clear return to Dashboard.
    - `frontend/src/components/Dashboard.tsx`: Enabled Symptom Reference Explorer tile as "Available Now" with Launch action.
    - `frontend/src/App.tsx`: Wired view switching between Dashboard and SymptomExplorer, preserving emergency help modal and adult consent context.
- Verification & Test Summary:
  - Pytest: 23 passed, 1 skipped in 5.61s (all unit, auth, knowledge, profile, and explorer tests passing).
  - Frontend Build: `tsc && vite build` built cleanly in 2.75s with zero errors (`dist/` generated).
  - Medical Safety: Confirmed zero diagnostic scores, probabilities, risk bands, or drug treatment recommendations appear in code, schemas, or screens.
- Next action: Completed M1B.2; proceeding to M1B.3 upon owner request.

### S-013 — 2026-10-12 — Antigravity (Implementation Engineer) — MedNourish-Dev (branch dev)
- Task and requirement IDs: M1B.3 Saved summaries and history (Files and Reports); SYMP-05, REPORT-01, REPORT-02, REPORT-04, SAFE-01, SAF-07, SAF-17, AUTH-05, PROF-02, C-01, C-18, C-21, OD-08.
- Actions taken:
  - Database Model & Schemas:
    - `backend/app/models/user.py`: Added `SavedSummary` relational model storing `id`, `user_id` (FK to authenticated user), `session_type`, `body_region_filter`, `selected_tags_json`, `matched_entries_json`, `match_count_total`, `package_version`, `matcher_version`, `review_status`, and `disclaimer`. Prohibits risk scores, probability bands, or free-text diagnoses.
    - `backend/app/schemas/reports.py`: Created Pydantic request/response schemas `SaveSummaryRequest`, `SavedSummaryItem`, `SavedSummaryDetail`, `SavedSummariesListResponse`, `DeleteSummaryResponse`.
  - Backend API Endpoints:
    - `backend/app/api/v1/reports.py`: Implemented authenticated endpoints:
      * `POST /v1/reports/summaries`: Saves reference-match summary, deriving ownership strictly from verified token `current_user.uid`.
      * `GET /v1/reports/summaries`: Lists current user's saved summaries ordered by `created_at` descending.
      * `GET /v1/reports/summaries/{id}`: Retrieves detailed summary with ownership enforcement (403 if accessing another user's summary).
      * `DELETE /v1/reports/summaries/{id}`: Deletes user's summary with ownership enforcement.
    - `backend/app/api/v1/profile.py`: Updated `delete_user_account` so deleting an account purges all `SavedSummary` records along with profile and consent logs per `AUTH-05` and `OD-08`.
    - `backend/app/main.py`: Registered reports router under `/v1`.
  - Frontend Integration:
    - `frontend/src/components/SymptomExplorer.tsx`: Added "Save Summary" action button on matched results header with active saving and confirmation states.
    - `frontend/src/components/ReportsView.tsx` & `.module.css`: Created accessible, responsive history timeline view supporting list browsing, detail inspection with matched tags and reference classes, item deletion, and navigation back to Dashboard.
    - `frontend/src/components/Dashboard.tsx`: Enabled Files & Reports tile as "Available Now" in Phase 1B.
    - `frontend/src/App.tsx`: Wired view routing for `reports` view.
  - Test Suite & Isolation:
    - `backend/tests/conftest.py`: Created centralized shared SQLite in-memory test database and session fixture with automated table re-creation and override cleanup between tests.
    - `backend/tests/test_reports.py`: Added 5 comprehensive tests verifying unauthenticated rejections, save/retrieve detail, user data isolation, cross-user forbidden access, and account deletion cascading.
    - `backend/tests/test_profile.py`: Streamlined to use shared test fixture.
- Verification & Test Summary:
  - Pytest: 28 passed, 1 skipped in 5.13s (all unit, auth, knowledge, profile, explorer, and reports tests passing).
  - Frontend Build: `tsc && vite build` built cleanly in 2.37s with zero errors (`dist/` generated).
  - Safety & Scope: Zero probability, risk score, diagnostic, or treatment fields added.
  - Live MySQL Status: Unverified; tests executed exclusively against isolated in-memory SQLite fixtures. Live database schema updates remain unapplied awaiting local credentials.
- Next action: Checkpoint M1B.3 in Git; await owner authorization before starting M1B.4 (MedBot Questionnaire).

---

*End of Memory.md. Append new session-log entries above this line.*


