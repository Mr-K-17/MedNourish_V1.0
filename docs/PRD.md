# MEDNOURISH — Product Requirements Document (PRD)

| Field | Value |
|---|---|
| Version | 1.3-draft (owner decisions of 2026-10-11 applied; change summary in `Memory.md` section 12.3, entry S-004) |
| Date | 2026-10-11 |
| Status | Draft for owner review |
| Project | MEDNOURISH: Early Detection and Prediction of Vitamin Deficiency in the Human Body |
| Companion documents | `Architecture.md` · `Rules.md` · `Phases.md` · `Design.md` · `Memory.md` |
| This document answers | What the product must do, for whom, and in which phase |

Status terms (Confirmed, Proposed, Pending, Unverified) are defined in `Memory.md`.

**Master registers.** Confirmed decisions (C-xx), open decisions (OD-xx) and pending verifications (PV-xx) are defined once, in `Memory.md`. This PRD refers to them by ID and does not redefine them. Requirement-to-milestone mapping and acceptance criteria are in `Phases.md` section 3.3; a "Phase 1" entry in a table below means Phase 1A or 1B as shown there.

---

## 1. Product summary

MEDNOURISH is a responsive web application (installable as a Progressive Web App) that, in its first version, is an **educational prototype**: it lets adults explore which symptom tags match entries in a reference table about nutritional deficiencies, starting with vitamins, and shows the matched tags. It combines a questionnaire bot (MedBot), a symptom selector (Symptom Analyzer, shown to users as the **Symptom Reference Explorer** in the MVP; C-19), report tracking (Files and Reports), a personal wellness-task planner (CarePlan) and scripted app help (NurseBot). Later phases add photo analysis (MedScan), severity guidance and hospital/doctor connections (VirtualWard), a doctor–patient chat, and a platform for medical interns (DocExp).

**Primary aim of Version 1.** Deliver a safe academic demo of the questionnaire and symptom-matching workflows, built incrementally and locally (C-13, C-14). MedBot gathers guided answers; the Symptom Reference Explorer lets users select symptoms directly. Both use the same transparent matcher over a cleaned, versioned reference package whose content is an **unreviewed draft** (C-17) and show an ordered reference match summary with the matched tags (C-18). Phase 1 contains **no ML training** and **no LLM** (C-12, C-15). The project should ultimately evaluate ML models (XGBoost and LightGBM remain the owner's preferred families), but that happens only in the gated Phase 2 evaluation track, and the current data does not yet establish a valid patient-level training task. Models must not be generated from the reference tables and presented as deficiency-prediction evidence. Any model shown in a demo remains clearly experimental and separate from clinical claims.

The product is an **academic demonstration designed to grow into a fuller application** (C-01).

**What MEDNOURISH is not.** It does not diagnose, treat, prescribe, or replace a qualified health professional. It gives reference matches and general education only, with no risk levels, probabilities or predictions. Its regulatory classification in any country is unknown and must be reviewed before any public release (PV-12).

**Naming (Confirmed, C-19).** The academic project title stays "MEDNOURISH: Early Detection and Prediction of Vitamin Deficiency in the Human Body". The word "prediction" in that title describes a long-term aim. In the MVP interface the symptom-matching feature is labelled "Symptom Reference Explorer", with an educational-prototype disclaimer, and user-facing text avoids unsubstantiated risk or prediction claims. A model cannot be described as predictive until it has been evaluated on suitable, verified, independent data (see section 10 and `Rules.md`).

## 2. Goals and non-goals

### Goals
Goal IDs use the prefix GOAL- so that they are not confused with the verification gates G1–G6 in `Architecture.md` section 8.2.

- GOAL-1. Let anyone aged 18+ explore, in plain language, which symptom tags match entries in a reference table about nutritional deficiencies, and be pointed to a clinician for any health concern.
- GOAL-2. Work for very different users: people who prefer minimal reading, people with little health interest, and people with medical knowledge (section 3).
- GOAL-3. Keep every user's data private and separated by profile (a profile is the unique key for everything a user does), collecting only the minimum (C-21).
- GOAL-4. Support simple, customisable daily wellness tasks (CarePlan).
- GOAL-5. Be honest about uncertainty: label model output as experimental, and never present unverified models or unreviewed content as accurate.
- GOAL-6. Provide a clean, simple, mobile-friendly, accessible interface.

### Non-goals (Version 1)
- Diagnosing any disease or deficiency, or interpreting results as a diagnosis.
- Recommending medicines, supplements or doses; displaying unreviewed treatment recommendations (C-17).
- Using an AI prediction to decide whether something is an emergency; building an automated emergency-triage engine in Phase 1 (C-20).
- Showing Low/Moderate/High bands, probability percentages, risk scores or non-nutritional disease classes to users (C-18).
- ML training, an LLM, paid APIs or subscriptions, cloud resources, public deployment or real health information in Phase 1 (C-12, C-14, C-15).
- Medication reminders (C-22).
- Users under 18; tailored guidance for children or other special groups (C-01).
- A native Android/iOS app (C-03).
- Real clinician consultations before Phase 4.
- Hard-coding any country's emergency numbers, hospital services or regulations (C-05).

## 3. Target users

Target audience as written in the original brief: illiterates, literates, working employees with zero health interest, people with medical-field knowledge ("all humans as potential customers"). Version 1 limits this to **adults aged 18 and above** (C-01).

| Segment | Needs | Product response |
|---|---|---|
| People who prefer minimal reading or typing | Very simple questions, large buttons, icons, spoken text | MedBot **Simple mode** (yes/no); icon + text labels; voice read-aloud where practical (A11Y-03) |
| Literate users | Clear choices, short flows, understandable results | MedBot **Standard mode** (multiple choice); plain-language results |
| Working employees with little health interest | Very low effort, clear benefit, gentle reminders | Short check-ins, quick results, CarePlan reminders |
| People with medical knowledge | More detail, rationale, ability to question results | In Phase 1 the matched tags and the package version are shown. **Detailed mode** (LLM-assisted) and report export are deferred (`Phases.md` section 9) |

## 4. End-to-end workflow

1. **Authentication page** → user signs up or signs in (AUTH-01).
2. First time only: explicit 18+ confirmation and health-data consent (AUTH-03), then a **minimal profile** (optional display name; optional gender, height and weight; no date of birth) (PROF-01, C-21).
3. **Dashboard** with tiles for every module; not-yet-built modules are visible as "coming soon" (DASH-01).
4. User completes **MedBot** and/or the **Symptom Reference Explorer**. Each sends the collected symptom tags to the shared deterministic matcher over the cleaned reference package. ML scoring is not part of Phase 1. **MedScan** is Phase 2 (C-10).
5. The **reference match summary** (an ordered list showing the matched tags) is saved to the user's profile and appears in **Files and Reports** with its package and matcher versions and a check-in history. It is not a risk score, probability or diagnosis (C-18).
6. Users can add their own wellness tasks in **CarePlan** and tick them off. Food and routine suggestions from the reference content are not shown until reviewed content exists (C-17).
7. **NurseBot** gives scripted, menu-based help about using the app. It does not answer nutrition or medical questions in Phase 1 (C-15).
8. An **Urgent help** page is reachable from every screen, including when signed out or offline, and does not depend on the backend (DASH-02, SAFE-02). The app never says "no red flags found".
9. Later phases: **VirtualWard** (severity guidance, nearby facilities, calendar/tasks), doctor chat and booking, DocExp.

## 5. Scope: MVP versus later phases

**MVP = Phase 0 + Phase 1 (1A foundation and safety shell, then 1B initial features; C-13).** Phase names are identical in `Phases.md`. Phase 1 runs locally on the Firebase emulators with fictional data (C-14).

| Module / capability | Phase 0–1 (MVP) | Later |
|---|---|---|
| Authentication page → Dashboard | Yes, email + password on the emulator (1A) | Google sign-in, phone OTP (OD-10) |
| Profile (data is exclusive to each profile) | Yes, minimal (1A) | Family profiles not planned (OD-09) |
| Safety layer | Disclaimers and a static Urgent help page reachable everywhere, including signed-out and offline (1A). No automated red-flag or triage engine | Reviewed, automated red-flag and crisis rules before any free-text health input is analysed |
| Symptom Analyzer (shown to users as "Symptom Reference Explorer") | Tag search + multi-select; ordered reference match summary showing matched tags (1B); no bands, percentages or probabilities; no non-nutritional classes | ML ranking evaluation in Phase 2 only if verified labels and user-available features support it |
| MedBot | Simple and Standard scripted questionnaire; the same matcher and output as the Explorer (1B). Optional lifestyle questions only if approved (OD-18) and never altering results | Detailed LLM mode (deferred; C-15); follow-up questions after MedScan (Phase 2) |
| Files and Reports | Saved reference match summaries and check-in history, in-app (1B) | PDF export and own-data export (deferred; own-data export is required before real user data); MedScan and VirtualWard data |
| CarePlan | User-created general wellness tasks, completion history, in-app reminders while the app is open (1B). No medication reminders (C-22) | Starter suggestions from reviewed content (OD-21); push notifications and Google Calendar/Tasks sync (Phase 3) |
| NurseBot | Scripted, menu-based app help; no free text, no LLM, no stored transcripts (1B) | LLM Q&A only with explicit owner approval, a reviewed knowledge base and the gates in `Rules.md` section 9 |
| MedScan | — | **Phase 2** (C-10; timing and the scope of deep learning under discussion, OD-16), only after dataset verification and successful model evaluation (gates in `Architecture.md` section 8.2) |
| VirtualWard | — (emergency guidance is part of the MVP safety layer, not VirtualWard) | **Phase 3**: severity guidance, nearby facilities (Maps), calendar/tasks, booking requests |
| Doctor–patient chat (WhatsApp-like) and online consultation | — | **Phase 4**; needs real verified clinicians and legal review |
| Hospital booking | — | Request-level in Phase 3; real booking in Phase 4 |
| DocExp (platform for medical interns) | Placeholder tile only | **Phase 5** |
| Languages | English; translation-ready | More languages later (OD-13) |

### 5.1 Deviations and clarifications relative to the original brief

The original brief is preserved; these are the places where the blueprint refines it and why.

| Original brief | Version 1 blueprint | Why | Status |
|---|---|---|---|
| "Pure Python, Java, JavaScript" | Python (backend, ML) + TypeScript/JavaScript (React); Java dropped from MVP | Simpler, consistent stack | Confirmed (C-03) |
| XGBoost and LightGBM as the main algorithms, including for "communication" | XGBoost/LightGBM are candidate structured-data models for the gated Phase 2 evaluation track (the project should ultimately evaluate ML models, C-12); no ML training in Phase 1; the 13 mapping CSVs drive transparent matching, not patient-style model training; chat is scripted in Phase 1, with no LLM (C-15) | Boosted trees cannot read images or hold a conversation, and the current mapping tables do not contain independent patient outcomes | Confirmed (C-12, C-15); data and task gates open |
| MobileNetV2 with TensorFlow Lite on-device | MobileNetV2 with server-side inference (Phase 2 per C-10; deep-learning timing under discussion, OD-16); on-device later | Web app; server-side chosen for the first design | Confirmed (C-06); timing Pending (OD-16) |
| "Possibility percentage" for conditions | An ordered reference match summary showing matched tags; no percentages, no Low/Moderate/High bands, no risk score | The mapping is not a calibrated probability model, and bands could imply severity or reassurance | Confirmed (C-18) |
| Medications "if needed" | No medicines, supplements, doses or unreviewed treatment recommendations; "ask a clinician" guidance; no medication reminders | Medical safety rule | Confirmed (C-08, C-17, C-22) |
| "Recognise disease/conditions" | Reference matches for nutritional entries only; non-nutritional disease classes are not displayed to users in the MVP | Scope and safety | Confirmed (C-18) |
| "Predict possible deficiency in the future" | Reference associations only; predictive wording requires a suitable verified dataset and evaluation | Current sources do not establish real-world predictive validity | Confirmed (C-19) |
| MedBot collects lifestyle information | Optional answers, only if approved (OD-18); they do not alter results and no suggestions are derived from them in Phase 1 | The mapping tables do not link these answers to verified outcomes, and routine content is unreviewed | Proposed; input list needs review |
| "Without changing any functions and design" | No existing app or design exists; all modules retained | New build | Confirmed (C-02) |
| VirtualWard contacts hospitals, books, consults online | Phased: guidance and nearby facilities (3), chat and booking (4) | Cost, legal and partner dependencies | Proposed |
| Google Tasks alerts | In-app reminders in the MVP; Google Tasks/Calendar in Phase 3 | Integration limits to be verified (PV-16) | Proposed |

## 6. Functional requirements

Requirement IDs are stable and referenced by `Phases.md`, `Design.md` and `Architecture.md`.

### 6.1 Authentication and profile

| ID | Requirement | Phase | Status |
|---|---|---|---|
| AUTH-01 | Authentication page (sign up, sign in) using Firebase Authentication on the local emulator with fictional accounts. Phase 1A method: email + password. Google sign-in and phone OTP are later (OD-10). | 1 (1A) | Confirmed (C-07, C-14); methods Pending (OD-10) |
| AUTH-02 | Sign out, password reset, session expiry handling. | 1 (1A) | Proposed |
| AUTH-03 | Before any data collection: an explicit, not pre-ticked 18+ confirmation (self-declaration) and a versioned, explicit health-data consent. Declining blocks the app but leaves Urgent help reachable. | 1 (1A) | Confirmed (C-21) |
| AUTH-04 | After sign-in: first-time users go to the 18+ confirmation, consent and profile setup; returning users go to the Dashboard. | 1 (1A) | Confirmed (workflow in brief) |
| AUTH-05 | User can delete their account and all associated data. Whether a minimal consent record survives deletion, and for how long, must be decided before any real user data (OD-08); development deletes everything. | 1 (1A) | Proposed |
| PROF-01 | **Amended by C-33**: Onboarding collects age (integer 1-120, demo purposes), gender, height, weight, blood type (A+, A-, B+, B-, AB+, AB-, O+, O-, Unknown) and medical conditions (multi-select of 18 conditions + None and optional Other free text max 100 chars). The 18+ gate is replaced by a demo-consent checkbox. Under-18 users see: 'Reference content is written for adults; demo only.' | 1 (1A) / v2 | Amended (C-33) |
| PROF-02 | Every record in MySQL (`user_profiles`, `user_consent_logs`, `assessments`) is keyed to the user's Firebase user ID (`firebase_uid`); no user can read or write another user's data. | 1 (1A) | Confirmed (brief: "like a primary key", OD-16) |
| PROF-03 | Users can edit and clear their optional profile fields. | 1 (1A) | Proposed |

### 6.2 Dashboard

| ID | Requirement | Phase | Status |
|---|---|---|---|
| DASH-01 | Dashboard shows tiles for all modules (MedBot, MedScan, Symptom Analyzer, VirtualWard, NurseBot, CarePlan, Files and Reports, DocExp). Modules not yet built show "coming soon". | 1 | Confirmed (brief) |
| DASH-02 | A persistent "Need urgent help?" entry is reachable from every screen, including Welcome, sign-in and consent, when signed out and when offline. It opens a static page bundled with the frontend that is independent of the backend and any LLM. | 1 (1A) | Confirmed (C-20) |

### 6.3 MedBot (questionnaire bot)

| ID | Requirement | Phase | Status |
|---|---|---|---|
| MEDBOT-01 | Collect the approved questionnaire inputs in Simple or Standard mode. Symptom questions use tags from the cleaned reference package. Lifestyle questions (e.g. sleep, activity, work routine) are included only if the owner approves them (OD-18); they are optional and never change a result. | 1 (1B) | Proposed; final question set needs approval (OD-18) |
| MEDBOT-02 | Interaction modes: **Simple** (yes/no, large buttons) and **Standard** (multiple choice) in Phase 1. **Detailed/Conversational** (free text, LLM-assisted) is deferred beyond Phase 1 (C-15) and needs explicit owner approval, PV-11 and reviewed content. | 1 (1B): Simple, Standard; Detailed deferred | Confirmed (brief; C-15); mode names Proposed |
| MEDBOT-03 | Answers are saved to the user's profile, through the API, as a dated assessment with package and matcher versions. Only cleaned symptom tags feed the matcher. Phase 1 has no free-text input. | 1 (1B) | Proposed |
| MEDBOT-04 | Output: the **reference match summary** (ordered, showing matched tags) with the disclaimer. Food-intake and routine suggestions from the reference content are **not shown** until reviewed content exists (C-17). | 1 (1B) | Confirmed (C-17, C-18); amended from the brief |
| MEDBOT-05 | No medicine or supplement recommendations. Results carry a general prompt to speak with a qualified clinician; no testing, urgency or severity advice is shown until reviewed (SAF-08). | 1 (1B) | Confirmed (C-08, C-17) |
| MEDBOT-06 | Questions can be skipped or resumed; flow adapts to earlier answers. | 1 (1B) | Proposed |
| MEDBOT-07 | After MedScan results, MedBot asks follow-up questions, summarises, and combines evidence with transparent rules. | 2 | Confirmed (brief); gated |
| MEDBOT-08 | The mapping's `Risk_Factors` field is narrative reference content, not a validated questionnaire or model feature set. Convert only selected, owner-approved items into user questions after defining wording, eligibility, consent, and evidence. | 1 (1B) | Pending (OD-18, PV-17) |
| MEDBOT-09 | Phase 1 matching is transparent and rule-based over the unreviewed reference mappings. XGBoost/LightGBM may be evaluated in Phase 2 only if verified data supports the exact user-input/target task. Any presentation of model output needs pre-set evaluation and abstention criteria and separate approval (gate G5). | 1 (1B) rule-based; ML evaluation Phase 2, gated | Proposed; model specification Pending (OD-17, PV-17) |
| MEDBOT-10 | Any lifestyle questions are optional, consent-covered, minimally collected and neutrally worded. In Phase 1 they do not alter results and drive no suggestions. They are excluded from deficiency scoring unless a future evidence review supports a specific use. | 1 (1B) | Proposed; depends on OD-18 |

### 6.4 Symptom Analyzer

| ID | Requirement | Phase | Status |
|---|---|---|---|
| SYMP-01 | Multi-select symptoms, grouped by body region, with search by tag. | 1 | Confirmed (brief) |
| SYMP-02 | Tag vocabulary comes from the cleaned keywords knowledge base: typos fixed, human-readable labels, plain-language synonyms, icon and read-aloud text. | 1 | Proposed (OD-04) |
| SYMP-03 | Results list possible associations from the selected tags as an ordered reference match summary. **Amended by C-34**: Percentages allowed, labelled 'Reference match %' with one-line explanation (never medical probability). Non-nutritional classes are excluded from user results in the MVP (C-18). | 1 / v2 | Amended (C-18, C-34) |
| SYMP-04 | Selecting a result explains which tags matched and package version. Show general information and any severity/urgency content only after clinical review; no medicines or supplements (C-17). | 1 | Proposed; content gated by PV-17 |
| SYMP-05 | Results can be saved to Files and Reports. | 1 | Proposed |
| SYMP-06 | Optional XGBoost/LightGBM ranking experiment, only if an audited dataset supplies suitable independent examples, targets, and the same feature types the app collects. The Phase 1 rule-based matcher remains the user-facing fallback. Do not generate synthetic table-derived rows as evidence of predictive performance. | Later, gated | Pending (OD-17, PV-01, PV-02, PV-17) |
| SYMP-07 | Evaluate any candidate model on independent, verified data with a task-specific model card; release only after all gates in `Architecture.md` section 8.2 pass. | Later, gated | Pending (PV-01, PV-02, PV-17) |

### 6.5 Files and Reports

| ID | Requirement | Phase | Status |
|---|---|---|---|
| REPORT-01 | **Nutritional match summary**: transparent summary of reference-table matches and limitations. **Amended by C-34 & C-35**: Percentages allowed by kind ('Reference match %', 'Model %', 'Image model %'); Demo risk bands (High/Moderate/Low) allowed, strictly labelled 'Demo risk band (heuristic, not clinical)'; reports say 'screened'/'probable pattern', never 'diagnosed'/'tested'. | 1 / v2 | Amended (C-18, C-34, C-35) |
| REPORT-02 | **Health Progress Tracker**: timeline of check-ins across MedBot and Symptom Reference Explorer (MedScan from Phase 2). | 1 | Confirmed (brief) |
| REPORT-03 | Report card in-app view for sharing with a clinician, including disclaimers and package version. PDF export is deferred beyond Phase 1. | 1 (view); export deferred | Proposed |
| REPORT-04 | Every report records the knowledge-base version, rules version and matcher version it used. | 1 | Proposed |

### 6.6 CarePlan

| ID | Requirement | Phase | Status |
|---|---|---|---|
| CARE-01 | Offer optional general wellness tasks (food, water, sleep, exercise) that the user accepts or edits. Suggestions must not be framed as treatment for a predicted deficiency. | 1 | Proposed |
| CARE-02 | Custom tasks and alerts: water, food, exercise. No medication reminders and no medicine or supplement suggestions (C-22, C-08). **Amended by C-38**: CarePlan auto-sync from reports for top nutrients >= 30% from curated dietary/lifestyle routine columns only (never supplements/drugs). | 1 / v2 | Confirmed (C-08, C-22, C-38) |
| CARE-03 | Mark tasks done; keep completion history. | 1 | Confirmed (brief) |
| CARE-04 | Reminders while the app is open (MVP). Background push, Google Tasks and Google Calendar sync in Phase 3. | 1 / 3 | Proposed (PV-15, PV-16) |
| CARE-05 | Automatic schedule from all modules, including VirtualWard and MedScan. | 3 | Confirmed (brief) |

### 6.7 NurseBot

| ID | Requirement | Phase | Status |
|---|---|---|---|
| NURSE-01 | Answers questions about how to use the app, plus scripted FAQs. No free text, no LLM, no stored transcripts in Phase 1 (C-15, C-23). | 1 | Confirmed (brief, C-15, C-23) |
| NURSE-02 | General nutrition education from a curated knowledge base: food alternatives, "what if" questions, long-term healthy-habit guidance. | Later (Phase 2+, gated by PV-11, PV-17) | Deferred; Confirmed (brief) |
| NURSE-03 | Safety boundaries: no personal diagnosis, prescriptions or doses. **Amended by C-36**: NurseBot may show internet-sourced vitamin/medication information with a disclaimer from allowlisted sources (MedlinePlus/ODS); personal diagnosis/prescriptions remain strictly refused. | 1 / v2 | Amended (C-04, C-08, C-36) |
| NURSE-04 | Scripted fallback responses when requests are out of scope. | 1 | Confirmed (C-04) |
| NURSE-05 | LLM access through a provider-swappable layer, with a safety test set run before launch. | Later (Phase 2+, gated by PV-11, OD-06) | Deferred; Proposed (OD-06) |

### 6.8 Safety and privacy (summary — authoritative text in `Rules.md`)

| ID | Requirement | Phase | Status |
|---|---|---|---|
| SAFE-01 | Every result screen carries a short disclaimer (preliminary, educational, not a diagnosis). | 1 | Confirmed (C-08) |
| SAFE-02 | Rule-based red-flag detection shows emergency guidance that points to local emergency services. Not AI-based. Numbers come from region configuration and are never hard-coded. | 1 | Confirmed (C-05, C-08); red-flag list Pending (PV-17) |
| SAFE-03 | When information is too limited, show "Insufficient information", never reassurance. | 1 | Proposed |
| SAFE-04 | Any future ML-derived output is labelled "Experimental" with a plain-language limitation note until all applicable model gates in `Architecture.md` section 8.2 pass. | Later, gated | Confirmed principle (C-08) |
| SAFE-05 | If a user expresses intent to harm themselves, stop the normal flow and show support and emergency guidance. | 1 | Proposed |
| SAFE-06 | Knowledge-base content carries a review status; unreviewed content is labelled in internal tooling and kept out of any public release (PV-17). | 1 | Proposed |
| PRIV-01 | Explicit, versioned consent (covering lifestyle answers); data minimisation; delete and export. | 1 | Proposed |
| PRIV-02 | No third-party sharing without explicit consent. LLM requests carry no names, IDs or photos. | 1 | Proposed |

### 6.9 MedScan (Phase 2)

| ID | Requirement | Phase | Status |
|---|---|---|---|
| SCAN-01 | Upload multiple images per session (eyes, nails, hands, lips, tongue, skin or infected areas) with capture guidance. | 2 | Confirmed (brief) |
| SCAN-02 | Secure upload validation and an OpenCV image-quality gate (blur, brightness, size) before analysis. | 2 | Confirmed (C-06) |
| SCAN-03 | Analysis by verified per-region models producing visual-pattern groups with a confidence band, including Normal, Other and "unclear — retake" outcomes. Never a diagnosis. | 2 | Pending (PV-04, PV-06, OD-16; gates in `Architecture.md` section 8.2) |
| SCAN-04 | Integrated with MedBot: asks follow-up questions, summarises, lists possible deficiencies and suggests lifestyle and food changes, with no medicines. | 2 | Confirmed (brief) |
| SCAN-05 | Server-side processing; images are deleted automatically after processing unless the user explicitly chooses to save them and safe storage exists (C-06). Retention rules in `Architecture.md`. | 2 | Confirmed (C-06); durations Pending (OD-08) |
| SCAN-06 | The user selects the body region (no automatic region detection in the first version). | 2 | Proposed |
| SCAN-07 | If verification or evaluation fails for a region, that region ships as guided photo capture plus questions without AI classification, or is withheld. | 2 | Proposed |

### 6.10 VirtualWard, doctor chat, DocExp (Phases 3–5)

| ID | Requirement | Phase | Status |
|---|---|---|---|
| WARD-01 | Severity guidance using MedBot, Symptom Analyzer and (if available) MedScan data. Rule-based; any ML only in shadow mode first. | 3 | Confirmed (brief); method Proposed |
| WARD-02 | Regular check-ups using MedBot. | 3 | Confirmed (brief) |
| WARD-03 | Find and contact nearby hospitals through Google Maps links (call, directions). Facility data availability Pending (PV-10, PV-16). | 3 | Confirmed (brief); feasibility Pending |
| WARD-04 | Appointment **requests** and reminders; real booking depends on a partner hospital. | 3 / 4 | Proposed |
| WARD-05 | Update CarePlan and, with consent, Google Calendar/Tasks. | 3 | Confirmed (brief); Pending (PV-16) |
| CHAT-01 | WhatsApp-like chat interface for doctors and patients. | 4 | Confirmed (brief) |
| CHAT-02 | Only verified clinicians; consent, retention and legal review before launch (PV-12). | 4 | Proposed |
| CHAT-03 | Online consultation by call or video; provider and cost Pending. | 4 | Confirmed (brief); Pending |
| DOCEXP-01 | Platform for medical interns to build a profile through patient sessions and reviews, integrated with VirtualWard. Needs ethical and regulatory review (interns' scope of practice). | 5 | Confirmed (brief, future scope) |

## 7. Non-functional requirements

| ID | Requirement | Status |
|---|---|---|
| A11Y-01 | Target WCAG 2.2 AA; see `Design.md`. | Proposed |
| A11Y-02 | Plain-language content; simple navigation; icons always paired with text. | Proposed |
| A11Y-03 | Voice read-aloud for questions and results where the platform supports it (PV-15). | Confirmed (C-05, "where practical") |
| I18N-01 | English first; all user-facing text in translation files; no hard-coded strings. | Confirmed (C-05) |
| I18N-02 | Right-to-left and text-expansion readiness. | Proposed |
| PWA-01 | Installable, responsive, mobile-first. | Confirmed (C-03) |
| SEC-01 | Authentication on every API route; deny-by-default data rules; secrets never in the repository or the browser. | Proposed |
| PERF-01 | Performance, availability and cost targets are Pending; set measurable targets in Phase 0. | Pending |
| COST-01 | Spending caps and budget alerts on every paid service. | Proposed |

## 8. Safety and compliance principles (summary)

Authoritative rules are in `Rules.md`. In short:

1. Results are **preliminary risk assessments and education**, never diagnoses.
2. **No medicines, supplements or doses.**
3. **Emergency guidance** comes from fixed rules and points to local emergency services; it never depends on an AI prediction.
4. **No claim** that any model is trained, validated or clinically accurate without a model card and an independent evaluation on verified, task-appropriate data. Synthetic examples derived from reference tables do not establish predictive validity.
5. **Country-specific** emergency numbers, hospital services and regulatory assumptions are flagged for review, never hard-coded (PV-10, PV-12).
6. Content and rules that influence advice need **clinical review** before any public release (PV-17).

## 9. Data and knowledge sources (status)

The following is a read-only inventory audit of the files currently in `datasets/`. It checks schemas, row counts, notebook contents and folder taxonomy; it does not verify source provenance, clinical validity, licensing, image labels or image quality. See `Memory.md` for the audit record.

| Item | Status | Notes |
|---|---|---|
| 13 `MedBot_datasets` CSVs (6 symptom mappings, 6 suggested routines, 1 keywords file) | Read-only schema/count audit completed; provenance and licence Unknown; content needs cleaning and clinical review | Reference tables for the deterministic matcher and content only; not patient records and not valid model training examples (PV-07, PV-09, OD-03, OD-04) |
| Main CSV `vitamin_deficiency_disease_dataset_20260123.csv` | Read-only audit: 4,000 rows × 34 columns, no blank cells or exact duplicate rows; source/label generation, label validity, licence and clinical relevance remain **Unverified** | Labels include Healthy, Anemia, Rickets_Osteomalacia, Night_Blindness and Scurvy; includes lab/nutrient measurements the app does not collect; targets do not directly match the 116 mapping classes. Notebook metadata cites Kaggle datasetVersion 14589953, not yet compared to upstream (PV-01) |
| ETL notebook `vitamin-deficiency-disease-prediction-dataset-etl.ipynb` | Read-only inspected | One exploratory-analysis code cell with saved outputs; no model training/evaluation workflow found. Saved figures/statistics are not independently verified (PV-02) |
| `datasets/DATASET_STRUCTURE.txt` | Present, 0 bytes | Provides no structure/provenance information (PV-03) |
| Image folders `dataset/`, `EYES/`, `HAIR/`, `LIPS/`, `NAILS/`, `SKIN/`, `TONGUE/` | Folder taxonomy and partial file inventory inspected; image content and label truth remain **Unverified** | `dataset/` has 11 class folders; body-region datasets use different taxonomies and include annotation files. Duplicate/near-duplicate, annotation meaning, provenance, quality and licence audits remain open (PV-04, PV-05, PV-06, PV-09) |
| Current planning docs `docs/*.md` | Read and reconciled for dataset compatibility | Current source of truth; stale `.md.txt` references corrected in this revision (PV-08) |

**Read-only findings from the current audit** (schema and inventory only; no images were opened and provenance/clinical truth were not established):
- The 13 CSVs hold 116 condition classes across six body regions, plus 83 suggested-routine rows and a 116-row keywords file. They have **no source or reference column**.
- Two rows are malformed (unquoted commas) and need cleaning; class names differ between files; some tags contain typos.
- Common symptom tags are shared by many nutrients (for example, the tag for fatigue appears in 19 classes), so results will often list several possible contributors.
- The suggested-routine files contain supplement and drug-treatment wording and specific follow-up timeframes that conflict with C-08 and need clinical review.
- Some rows concern children or infants and must stay out of adult results.
- The six region mapping files contain free-text `Risk_Factors` fields. These are source text, not a validated question bank or model input schema. Any questions derived from them need review (OD-18, PV-17). See `Memory.md` section 7.
- The mapping tables do not provide verified outcome links for sleep, working hours, snack habits or physical activity. Do not use these lifestyle answers as deficiency-model inputs on this evidence.
- Image folder names (from the directory tree only) suggest labels are broader than the nutrient-level classes in the mapping tables; the TONGUE folders do not correspond to the tongue mapping classes. This is unverified.

**What the data can support (preliminary):** after cleaning and review, transparent matching from selected symptom tags to reference classes. The main CSV is a candidate for investigation, not an approved training source; its labels and provenance are unknown and its features do not cleanly match app inputs. **Not yet supported:** a validated person-level deficiency prediction or any image model. No model has been trained or evaluated by this project.

## 10. AI/ML requirements (summary — authoritative in `Architecture.md`)

| Component | Role | Input | Status |
|---|---|---|---|
| Rule-based matcher and risk engine | Primary Phase 1 method for matching reviewed symptom tags to reference classes; no diagnosis | Symptom tags; approved inputs only | Proposed; content/specification gated by OD-04, OD-14, PV-07, PV-17 |
| XGBoost and LightGBM | Candidate later structured-data experiments; not Phase 1 scoring engines | Only user-available features supported by verified labels; exclude unavailable labs and leakage columns | Not trained; blocked by PV-01, PV-02, PV-17, OD-17 and owner approval |
| MobileNetV2 (transfer learning, per body region) | Image classification for MedScan | Pre-processed images | Not trained; blocked by PV-04–PV-06; timing Pending (OD-16) |
| Evidence combination | Transparent rules showing agreement or disagreement between image and questionnaire evidence | Outputs above | Proposed; a trained fusion model is not possible without paired data |
| LLM | Language only (MedBot Detailed mode, NurseBot) | User message + retrieved knowledge | Pending provider choice (PV-11, OD-06) |
| OpenCV | Quality checks and preprocessing | Images | Proposed |

No accuracy, sensitivity, or performance figure may be shown to users unless it comes from an independent evaluation on verified data appropriate to the intended task. Metrics from synthetic table-derived examples describe table reproduction only and must not be presented as model performance for people.

## 11. Success criteria for the Version 1 demo

- All MVP modules work end to end with fictional test data.
- MedBot and Symptom Analyzer work end to end using the versioned, reviewed matching rules and clearly described limitations. ML remains deferred unless the relevant data gates are met and owner approval is recorded.
- A written safety test set (red flags, medicine/dose questions, out-of-scope questions, prompt-injection attempts) passes before any LLM feature is shown.
- Each user's data is isolated; security-rule tests pass.
- Accessibility checks pass for the key flows.
- No screen, document or demo script claims diagnostic accuracy or model validity.
- Every unresolved item is visible in `Memory.md`.

## 12. Assumptions

- A1. Users have a modern smartphone or desktop browser and internet access.
- A2. Development and demo use **fictional test data only**; no real users' health data during development.
- A3. The project owner works with AI coding tools (Antigravity, Codex, Cursor) and is a beginner in AI/ML, so documents and decisions are explained simply.
- A4. The deployment country is not decided; anything country-specific is configuration (C-05).
- A5. The deadline is unknown (OD-07); phases are sequenced by dependency, not by date.
- A6. Lifestyle questions should be optional, explained, minimally collected, and used only for general wellness suggestions unless stronger evidence and review are added.
- A7. The 13 mapping CSVs are reference content, not patient records. The provenance and semantics of the separate main CSV remain unknown until verified.

## 13. Open decisions and pending verification

The registers are in `Memory.md`. Items that most affect this PRD:

- **Decisions:** OD-01 scope wording · OD-02 supplement/medicine/timeframe handling · OD-03 clinical reviewer · OD-06 LLM approach · OD-08 retention durations · OD-14 Risk Score specification · OD-16 MedScan scope · OD-17 model task and input/label fit · OD-18 MedBot question set.
- **Verification:** PV-01 to PV-06 (structured/image data verification) · PV-07 (reference CSV provenance and review) · PV-09 (licences) · PV-10 (target country) · PV-11 (LLM) · PV-12 (legal/regulatory) · PV-17 (clinical review).

## 14. Risk register

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| RSK-01 | Datasets are mislabelled, synthetic, duplicated or leak information | Misleading models | Verify provenance, labels, feature/target fit and independent evaluation before ML; image work waits for PV-04–PV-06 |
| RSK-02 | Users treat results as diagnoses | Harm | Consistent wording, disclaimers, urgency guidance, clinician-referral prompts |
| RSK-03 | False reassurance from low-information inputs | Missed care | "Insufficient information" band; no "you are fine" wording |
| RSK-04 | Image model performs unevenly across skin tones, lighting, age or gender | Unfair or wrong results | Subgroup evaluation; withhold regions that fail; MedScan stays Phase 2 |
| RSK-05 | Unreviewed medical content (supplement/drug wording, timeframes) | Unsafe advice | Hide those columns; clinical review (PV-17) |
| RSK-06 | LLM hallucination or boundary breach | Unsafe advice | Curated knowledge, output filtering, safety test set, scripted fallbacks |
| RSK-07 | Privacy breach of health data and photos | Serious harm | Deny-by-default rules, auto-delete, minimal logging, consent |
| RSK-08 | Regulatory classification and privacy-law obligations unknown | Cannot release publicly | Flag before any public release (PV-12); keep as academic demo |
| RSK-09 | Scope too large for a beginner | Unfinished project | Strict phases; MVP first; MedScan and integrations deferred |
| RSK-10 | Integration cost or approval hurdles (Maps billing, Calendar scope verification) | Delays | Defer to Phase 3; verify early (PV-16) |
| RSK-11 | Free-tier or quota limits, unexpected bills | Outages or cost | Spending caps, rate limits, scripted fallbacks (PV-11, PV-13) |
| RSK-12 | Three AI tools drift or contradict each other | Inconsistent code | `Rules.md` workflow rules; `Memory.md` handoff log; one tool per branch |
| RSK-13 | Doctor chat creates liability and verification duties | Legal exposure | Phase 4 only, with legal review and real clinicians |
| RSK-14 | Dataset or content licences prohibit use | Cannot ship | Record licences before use (PV-09) |
| RSK-15 | Low-literacy users misunderstand results | Harm or distrust | Simple mode, icons, read-aloud, usability testing |
| RSK-16 | Reference mappings or unverified structured data are mistaken for patient-level evidence | Misleading claims | Keep table matching transparent; gate ML on verified labels, input compatibility, independent evaluation, and clinical review; do not use synthetic table variants as evidence |
| RSK-17 | Lifestyle questions feel intrusive, or answers are mishandled or over-interpreted | Distrust or harm | Keep questions optional and minimal, obtain consent, use neutral wording, and limit suggestions to general wellness |
