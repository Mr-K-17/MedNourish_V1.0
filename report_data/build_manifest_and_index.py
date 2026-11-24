import os
import hashlib
import csv

report_root = r"C:\Users\USER\Desktop\MedNourish-Dev\report_data"

def calc_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

# Item mappings to chapters and descriptive titles
chapter_map = {
    # Diagrams
    "fig_5_1": ("Chapter 5: Methodology", "System Architecture (Three-Tier Client-Server)"),
    "fig_5_2": ("Chapter 5: Methodology", "Proposed Functional Modules & Subsystems"),
    "fig_5_3": ("Chapter 5: Methodology", "DFD Level 0 (Context Diagram)"),
    "fig_5_4": ("Chapter 5: Methodology", "DFD Level 1 (Decomposed System Data Flow)"),
    "fig_5_5": ("Chapter 5: Methodology", "Use Case Diagram (Actors & System Boundary)"),
    "fig_5_6": ("Chapter 5: Methodology", "Entity-Relationship (ER) Database Schema"),
    "fig_5_7": ("Chapter 5: Methodology", "User Workflow Flowchart (End-to-End Intake)"),
    "fig_5_8": ("Chapter 5: Methodology", "Machine Learning Pipeline (Train/Quant/Infer)"),
    "fig_5_9": ("Chapter 5: Methodology", "Safety, Ethics & Multi-Layered Privacy Architecture"),
    "fig_6_1": ("Chapter 6: Implementation", "Curated Clinical Knowledge Ingestion Pipeline"),
    "fig_6_2": ("Chapter 6: Implementation", "Reference Symptom Matcher Flowchart"),
    "fig_6_3": ("Chapter 6: Implementation", "Scoring Engine & Noisy-OR Formulas Flowchart"),
    "fig_6_4": ("Chapter 6: Implementation", "MedBot Guided Conversational Workflow"),
    "fig_6_5": ("Chapter 6: Implementation", "MobileNetV2 Multitask Architecture"),
    "fig_6_6": ("Chapter 6: Implementation", "Vision Training, Validation & TFLite Export Flow"),
    "fig_6_7": ("Chapter 6: Implementation", "MedScan Multi-Region Inference Sequence Diagram"),
    "fig_6_8": ("Chapter 6: Implementation", "NurseBot Intent Router & MedlinePlus Fallback"),
    "fig_6_9": ("Chapter 6: Implementation", "Recency-Weighted Temporal Aggregation Engine"),
    "fig_6_10": ("Chapter 6: Implementation", "CarePlan Meal Synthesizer & iCalendar Sync"),
    "fig_7_1": ("Chapter 7: System Testing", "Multi-Tiered Verification & Testing Strategy"),
    
    # Charts
    "fig_6_11": ("Chapter 6: Implementation", "Image Dataset Composition (Raw vs Retained per Region)"),
    "fig_6_12": ("Chapter 6: Implementation", "Tabular Dataset Class Distribution (N=4,000)"),
    "fig_6_13": ("Chapter 6: Implementation", "XGBoost Feature Importance (Symptoms Profile)"),
    "fig_6_14": ("Chapter 6: Implementation", "Grad-CAM Attention Attribution Maps across 6 Regions"),
    "fig_8_1": ("Chapter 8: Results & Discussion", "Model Accuracy Comparison across Profiles"),
    "fig_8_2": ("Chapter 8: Results & Discussion", "Precision, Recall, and Macro-F1 Comparison"),
    "fig_8_3": ("Chapter 8: Results & Discussion", "Per-Class Performance Heatmaps"),
    "fig_8_4": ("Chapter 8: Results & Discussion", "MedScan Vision Regional Evaluation Performance"),
    "fig_8_5": ("Chapter 8: Results & Discussion", "Edge Inference Latency Percentiles (p50, p95)"),
    "fig_8_6": ("Chapter 8: Results & Discussion", "Tabular Models Confusion Matrices"),
    "fig_8_7": ("Chapter 8: Results & Discussion", "Vision V2 Models Confusion Matrices"),

    # Tables
    "tab_6_1": ("Chapter 6: Implementation", "Complete REST API Endpoints Specification (48 Endpoints)"),
    "tab_6_2": ("Chapter 6: Implementation", "Relational Database Schema (5 Tables)"),
    "tab_6_3": ("Chapter 6: Implementation", "Tabular Feature Inventory across 3 Profiles"),
    "tab_6_4": ("Chapter 6: Implementation", "Vision V2 Class Maps & Anatomical Targets"),
    "tab_6_5": ("Chapter 6: Implementation", "Comprehensive Dataset Inventory & Corpus Composition"),
    "tab_7_1": ("Chapter 7: System Testing", "Unit Test Cases per Core Module"),
    "tab_7_2": ("Chapter 7: System Testing", "Integration Test Cases across Services"),
    "tab_7_3": ("Chapter 7: System Testing", "PRD Requirements Validation Matrix"),
    "tab_7_4": ("Chapter 7: System Testing", "Output Format & Compliance Verification"),
    "tab_7_5": ("Chapter 7: System Testing", "18-Step End-to-End System Smoke Test Matrix"),
    "tab_7_6": ("Chapter 7: System Testing", "White-Box Branch Coverage Test Cases"),
    "tab_7_7": ("Chapter 7: System Testing", "Black-Box Functional Boundary Test Cases"),
    "tab_7_8": ("Chapter 7: System Testing", "Master Test Execution Summary (100% Pass Rate)"),
    "tab_7_9": ("Chapter 7: System Testing", "Security, Privacy & Consent Gating Tests"),
    "tab_7_10": ("Chapter 7: System Testing", "Software Defects Resolved & Root Causes"),
    "tab_8_1": ("Chapter 8: Results & Discussion", "Tabular Models Benchmark & Leakage Audit"),
    "tab_8_2": ("Chapter 8: Results & Discussion", "Vision V2 Models Empirical Performance & 95% CI"),
    "tab_8_3": ("Chapter 8: Results & Discussion", "Vision V1 vs V2 Architectural Comparison"),
    "tab_8_4": ("Chapter 8: Results & Discussion", "TFLite Float32 vs INT8 DRQ Model Parity & Sizes"),
    "tab_8_5": ("Chapter 8: Results & Discussion", "Inference Latency & Edge CPU Throughput"),
    "tab_8_6": ("Chapter 8: Results & Discussion", "Alternative Approaches Investigated & Omission Reasons"),
    "tab_8_7": ("Chapter 8: Results & Discussion", "System Requirement Coverage Matrix (100% PRD)"),
    "tab_8_8": ("Chapter 8: Results & Discussion", "Known System Limitations & Clinical Boundaries")
}

records = []
all_files = []

for root_dir, dirs, files in os.walk(report_root):
    for f in sorted(files):
        if f in ["MANIFEST.csv", "REPORT_DATA.md", "generate_charts_pil.py", "build_remaining_tables.py", "build_all_diagrams.py", "find_lines.py", "build_code_excerpts.py", "test_cdp.js", "test_cdp_clean.js", "capture_all_screenshots.js", "capture_suite.js", "debug_dom.js", "render_terminal_and_system_shots.py", "build_dataset_samples.py", "build_manifest_and_index.py"]:
            continue
        full_path = os.path.join(root_dir, f)
        rel_path = os.path.relpath(full_path, report_root).replace("\\", "/")
        size = os.path.getsize(full_path)
        sha = calc_sha256(full_path)
        
        # Determine category & target chapter
        cat = "general"
        target_ch = "Chapter 5–8 General"
        title = f.replace("_", " ").title()
        
        if rel_path.startswith("diagrams/"):
            cat = "diagram"
            key = f.split(".")[0]
            if key in chapter_map:
                target_ch, title = chapter_map[key]
            else:
                target_ch = "Chapter 5: Methodology"
        elif rel_path.startswith("charts/"):
            cat = "chart"
            key = f.split(".")[0]
            if key in chapter_map:
                target_ch, title = chapter_map[key]
            else:
                target_ch = "Chapter 8: Results & Discussion"
        elif rel_path.startswith("tables/"):
            cat = "table"
            key = f.split(".")[0]
            if key in chapter_map:
                target_ch, title = chapter_map[key]
            else:
                target_ch = "Chapter 6 or 7"
        elif rel_path.startswith("screenshots/"):
            cat = "screenshot"
            target_ch = "Chapter 6: Implementation"
            title = f"Screenshot: {f.replace('.png', '').replace('_', ' ').title()}"
        elif rel_path.startswith("code_excerpts/"):
            cat = "code_excerpt"
            target_ch = "Chapter 6: Implementation"
            title = f"Code Excerpt: {f.replace('.md', '').replace('_', ' ').title()}"
        elif rel_path.startswith("logs/"):
            cat = "log"
            target_ch = "Chapter 7: System Testing"
            title = f"Execution Log: {f.replace('.txt', '').replace('_', ' ').title()}"
        elif rel_path.startswith("facts/"):
            cat = "fact"
            target_ch = "Chapter 5–8 Reference Facts"
            title = f"Fact Reference: {f.replace('_', ' ').title()}"
        elif rel_path.startswith("dataset_samples/"):
            cat = "dataset_sample"
            target_ch = "Chapter 5 & 6 Evidence"
            title = f"Dataset Sample: {f.replace('_', ' ').title()}"

        records.append({
            "relative_path": rel_path,
            "category": cat,
            "title": title,
            "target_chapter": target_ch,
            "file_size_bytes": size,
            "sha256": sha,
            "availability_status": "AVAILABLE"
        })

# Missing items explicitly required to be documented in manifest per prompt rules
missing_items = [
    {
        "relative_path": "charts/fig_6_15_learning_curves.png",
        "category": "chart",
        "title": "Figure 6.15: Model Loss & Accuracy Learning Curves across Epochs",
        "target_chapter": "Chapter 6: Implementation",
        "file_size_bytes": 0,
        "sha256": "N/A",
        "availability_status": "NOT AVAILABLE (training history logs not persisted in repository; retraining prohibited per C-09/C-16)"
    },
    {
        "relative_path": "logs/pytest_cov.txt",
        "category": "log",
        "title": "Pytest Automated Statement Coverage Report",
        "target_chapter": "Chapter 7: System Testing",
        "file_size_bytes": 0,
        "sha256": "N/A",
        "availability_status": "NOT AVAILABLE (pytest-cov plugin not installed in virtual environment; new package installation prohibited)"
    },
    {
        "relative_path": "dataset_samples/tabular_sample.csv",
        "category": "dataset_sample",
        "title": "Tabular Dataset 20-Row Raw CSV Sample",
        "target_chapter": "Chapter 5: Methodology",
        "file_size_bytes": 0,
        "sha256": "N/A",
        "availability_status": "NOT AVAILABLE (raw training datasets physically quarantined outside repository per C-09/C-40 publish policy)"
    },
    {
        "relative_path": "dataset_samples/sample_lips.png",
        "category": "dataset_sample",
        "title": "Lips Anatomical Target Raw Image Sample",
        "target_chapter": "Chapter 6: Implementation",
        "file_size_bytes": 0,
        "sha256": "N/A",
        "availability_status": "NOT AVAILABLE (raw training datasets physically quarantined outside repository per C-09/C-40 publish policy)"
    }
]

records.extend(missing_items)

# Write MANIFEST.csv
manifest_path = os.path.join(report_root, "MANIFEST.csv")
with open(manifest_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["relative_path", "category", "title", "target_chapter", "file_size_bytes", "sha256", "availability_status"])
    w.writeheader()
    for r in records:
        w.writerow(r)

print(f"Wrote MANIFEST.csv with {len(records)} entries!")

# Write comprehensive REPORT_DATA.md
md_path = os.path.join(report_root, "REPORT_DATA.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("""# MEDNOURISH Project Report Evidence Package (REPORT_DATA)

**Context**: Master Evidence Dossier for Final-Year Computer Science Project Report  
**Chapters Covered**: Chapter 5 (Methodology), Chapter 6 (Implementation), Chapter 7 (System Testing), Chapter 8 (Results & Discussion)  
**Author Role**: Implementation Engineer & System Technical Auditor  
**Notice**: Educational Prototype — Not a Medical Device. Empirical Research Benchmark.

---

## Executive Summary for the Report Writer

This package contains **verified empirical evidence, architectural diagrams, statistical charts, system test logs, verbatim code excerpts, and high-resolution screenshots** collected directly from the active `MedNourish-Dev` codebase (branch `dev`, commit `51865759`).

### Core Rules for Report Writing Assistant:
1. **Never Invent Data**: Cite the exact numbers, accuracy percentages, test counts, and latency figures documented in this dossier.
2. **Strict Non-Diagnostic Framing**: Always maintain that MEDNOURISH is an *educational and dietary awareness research prototype*, not certified software for clinical diagnosis or emergency triage.
3. **Acknowledge Data Quarantine**: Raw training datasets (364,292 images, 4,000 tabular rows) are preserved under strict data quarantine and excluded from the public repository snapshot in accordance with Owner Authorization C-40 and research ethics protocols.
4. **Refer to Ground Truth Artifacts**: Every table, figure, and excerpt listed below has a corresponding verified file on disk.

---

## Table of Contents
1. [Chapter 5: Methodology Artifacts](#chapter-5-methodology-artifacts)
2. [Chapter 6: Implementation Artifacts](#chapter-6-implementation-artifacts)
3. [Chapter 7: System Testing Artifacts](#chapter-7-system-testing-artifacts)
4. [Chapter 8: Results & Discussion Artifacts](#chapter-8-results--discussion-artifacts)
5. [Summary Statistics & Verification Manifest](#summary-statistics--verification-manifest)

---

## Chapter 5: Methodology Artifacts

### Architectural & Process Diagrams
- **Figure 5.1: System Architecture**  
  - File: `diagrams/fig_5_1_system_architecture.png` (Source: `diagrams/src/fig_5_1_system_architecture.mmd`)  
  - *Summary*: Three-tier client-server specification. Presentation (React 18 / Vite), API Gateway (FastAPI 0.115), Edge ML Engine (MobileNetV2 TFLite DRQ), Relational Persistence (SQLAlchemy / PyMySQL / SQLite).
- **Figure 5.2: Proposed Functional Modules Breakdown**  
  - File: `diagrams/fig_5_2_proposed_system_modules.png` (Source: `diagrams/src/fig_5_2_proposed_system_modules.mmd`)  
  - *Summary*: 6 Core Subsystems (Explorer, MedBot, MedScan, NurseBot, Virtual Ward, CarePlan) governed by multi-layered safety.
- **Figure 5.3: Data Flow Diagram (DFD) Level 0**  
  - File: `diagrams/fig_5_3_dfd_level_0.png` (Source: `diagrams/src/fig_5_3_dfd_level_0.mmd`)  
  - *Summary*: Context-level data flows between User/Patient, MEDNOURISH System, and External Clinical Services (MedlinePlus, CalDAV).
- **Figure 5.4: Data Flow Diagram (DFD) Level 1**  
  - File: `diagrams/fig_5_4_dfd_level_1.png` (Source: `diagrams/src/fig_5_4_dfd_level_1.mmd`)  
  - *Summary*: Decomposed process flow across intake, quality checks, inference computation, persistence, and calendar export.
- **Figure 5.5: Use Case Diagram**  
  - File: `diagrams/fig_5_5_use_case_diagram.png` (Source: `diagrams/src/fig_5_5_use_case_diagram.mmd`)  
  - *Summary*: Use cases for Patient/User and Clinical Auditor within system boundaries.
- **Figure 5.6: Entity-Relationship Database Schema**  
  - File: `diagrams/fig_5_6_er_database_schema.png` (Source: `diagrams/src/fig_5_6_er_database_schema.mmd`)  
  - *Summary*: Relational schema across 5 core entities: `user_profiles`, `user_consent_logs`, `saved_summaries`, `care_plan_items`, `medscan_sessions`.
- **Figure 5.7: User Workflow Flowchart**  
  - File: `diagrams/fig_5_7_user_workflow_flowchart.png` (Source: `diagrams/src/fig_5_7_user_workflow_flowchart.mmd`)  
  - *Summary*: End-to-end user journey from consent gate, modality selection, evaluation, triage check, to care plan synthesis.
- **Figure 5.8: Machine Learning Pipeline**  
  - File: `diagrams/fig_5_8_ml_pipeline.png` (Source: `diagrams/src/fig_5_8_ml_pipeline.mmd`)  
  - *Summary*: 5-Stage ML lifecycle: Ingestion/Support Gate >= 40, Training (XGBoost/MobileNetV2), INT8 DRQ Quantization, Parity Verification, Edge Deployment.
- **Figure 5.9: Multi-Layered Safety, Ethics & Privacy Architecture**  
  - File: `diagrams/fig_5_9_safety_privacy_layers.png` (Source: `diagrams/src/fig_5_9_safety_privacy_layers.mmd`)  
  - *Summary*: 5-Tier defense-in-depth: Disclaimer Banner, Emergency Triage Interceptor, EXIF Metadata Stripping, AST Safety Scanner, Grounded Curated Knowledge.

---

## Chapter 6: Implementation Artifacts

### Implementation Flowcharts & Architecture
- **Figure 6.1: Curated Clinical Knowledge Ingestion Pipeline** (`diagrams/fig_6_1_curated_knowledge_pipeline.png`)
- **Figure 6.2: Reference Symptom Matcher Flowchart** (`diagrams/fig_6_2_reference_matcher_flowchart.png`)
- **Figure 6.3: Scoring Engine Mathematical Flowchart** (`diagrams/fig_6_3_scoring_formulas_flowchart.png`)
- **Figure 6.4: MedBot Conversational Interview Workflow** (`diagrams/fig_6_4_medbot_workflow.png`)
- **Figure 6.5: MobileNetV2 Regional Vision Architecture** (`diagrams/fig_6_5_mobilenetv2_multitask_architecture.png`)
- **Figure 6.6: Vision Training & TFLite Export Flow** (`diagrams/fig_6_6_vision_training_export_flow.png`)
- **Figure 6.7: MedScan Vision Sequence Diagram** (`diagrams/fig_6_7_medscan_sequence_diagram.png`)
- **Figure 6.8: NurseBot Intent Routing & FAQ Dispatcher** (`diagrams/fig_6_8_nursebot_intent_router.png`)
- **Figure 6.9: Recency-Weighted Temporal Aggregation Engine** (`diagrams/fig_6_9_recency_weighted_aggregation.png`)
- **Figure 6.10: CarePlan Meal Synthesizer & iCalendar Sync** (`diagrams/fig_6_10_careplan_meals_and_sync.png`)

### Chapter 6 Tables & Visuals
- **Table 6.1**: API Endpoints Specification (48 Endpoints) (`tables/tab_6_1_api_endpoints.md`)
- **Table 6.2**: Relational Database Schema (`tables/tab_6_2_db_schema.md`)
- **Table 6.3**: Tabular Feature Classification across 3 Profiles (`tables/tab_6_3_tabular_features.md`)
- **Table 6.4**: Vision V2 Regional Class Maps (`tables/tab_6_4_vision_class_maps.md`)
- **Table 6.5**: Physical Dataset Inventory (`tables/tab_6_5_dataset_inventory.md`)
- **Figure 6.11**: Image Dataset Composition Chart (`charts/fig_6_11_image_dataset_composition.png`)
- **Figure 6.12**: Tabular Dataset Class Distribution (`charts/fig_6_12_tabular_class_distribution.png`)
- **Figure 6.13**: XGBoost Feature Importance (`charts/fig_6_13_feature_importance_symptoms.png`)
- **Figure 6.14**: Grad-CAM Visual Attention Heatmaps (`charts/fig_6_14_gradcam_overlays.png`)

### Verbatim Implementation Code Excerpts
- `code_excerpts/matcher_core.md`: Core Inverted-Index Symptom Matcher
- `code_excerpts/scoring_formulas.md`: Shrinkage Scaling & Noisy-OR Formulas
- `code_excerpts/symptom_extraction.md`: Clinical Synonym Expansion & Rule-Based Negation
- `code_excerpts/tabular_preprocessor.md`: Tabular Preprocessor & Leakage Purge
- `code_excerpts/vision_model_builder.md`: MobileNetV2 Regional Transfer Learning Model
- `code_excerpts/tflite_parity_check.md`: Float32 vs Quantized INT8 Parity Evaluator
- `code_excerpts/medscan_quality_audit.md`: Laplacian Variance Blur & Dual-Luminance Gate
- `code_excerpts/medscan_shortcut_blend.md`: Confidence Discounting & Shortcut Heuristics
- `code_excerpts/nursebot_router_webanswer.md`: Emergency Interception & MedlinePlus Fetcher
- `code_excerpts/reports_aggregation.md`: Exponential Time-Decay Risk Aggregation
- `code_excerpts/careplan_meal_planner.md`: Deterministic Dietary Matrix Generator
- `code_excerpts/careplan_ics_export.md`: RFC 5545 iCalendar Byte Serialization
- `code_excerpts/db_mode_switch.md`: Dynamic SQLite / MySQL Dialect Switch
- `code_excerpts/consent_auth_dependency.md`: Mandatory Consent & JWT Verification
- `code_excerpts/safety_claims_scanner.md`: Automated CI/CD AST Safety Scanner

---

## Chapter 7: System Testing Artifacts

### Test Strategy & Execution Logs
- **Figure 7.1: Testing Strategy Pyramid** (`diagrams/fig_7_1_testing_strategy.png`)
- **Backend Pytest Log (SQLite Mode)**: `logs/pytest_backend_sqlite.txt` (115 passed in 181.83s)
- **Backend Pytest Log (MySQL Mode)**: `logs/pytest_backend_mysql.txt` (115 passed in 181.67s)
- **ML Lab Pytest Log**: `logs/pytest_ml.txt` (40 passed in 59.63s)
- **End-to-End System Smoke Log**: `logs/smoke_e2e.txt` (18 / 18 passed in 24.12s)
- **Safety Claims Scanner Log**: `logs/safety_scan.txt` (76 / 76 files passed in 3.45s)
- **Frontend Production Build Log**: `logs/frontend_build.txt` (`npm run build` success)

### Chapter 7 Tables
- **Table 7.1**: Unit Test Cases per Core Module (`tables/tab_7_1_unit_tests.md`)
- **Table 7.2**: Integration Test Cases across Subsystems (`tables/tab_7_2_integration_tests.md`)
- **Table 7.3**: PRD Requirements Validation Matrix (`tables/tab_7_3_validation_tests.md`)
- **Table 7.4**: Output Format Verification & Compliance (`tables/tab_7_4_output_tests.md`)
- **Table 7.5**: 18-Step End-to-End Smoke Test Matrix (`tables/tab_7_5_system_tests.md`)
- **Table 7.6**: White-Box Branch Coverage Test Cases (`tables/tab_7_6_white_box_tests.md`)
- **Table 7.7**: Black-Box Boundary Partition Test Cases (`tables/tab_7_7_black_box_tests.md`)
- **Table 7.8**: Master Consolidated Testing Summary (364 Tests, 100% Pass Rate) (`tables/tab_7_8_test_summary.md`)
- **Table 7.9**: Security, Privacy & Consent Gating Tests (`tables/tab_7_9_security_tests.md`)
- **Table 7.10**: Software Defects Identified & Resolved (`tables/tab_7_10_defects_fixed.md`)

---

## Chapter 8: Results & Discussion Artifacts

### Empirical Performance Charts
- **Figure 8.1**: Model Accuracy Comparison (`charts/fig_8_1_model_accuracy_comparison.png`)
- **Figure 8.2**: Precision, Recall, and Macro-F1 Comparison (`charts/fig_8_2_precision_recall_f1_comparison.png`)
- **Figure 8.3**: Per-Class Performance Heatmaps (`charts/fig_8_3_per_class_heatmaps.png`)
- **Figure 8.4**: MedScan Vision Regional Performance (`charts/fig_8_4_medscan_cv_performance.png`)
- **Figure 8.5**: Edge Inference Latency Percentiles (`charts/fig_8_5_inference_latency.png`)
- **Figure 8.6**: Tabular Confusion Matrices (`charts/fig_8_6_confusion_matrices_tabular.png`)
- **Figure 8.7**: Vision Confusion Matrices (`charts/fig_8_7_confusion_matrices_vision.png`)

### Chapter 8 Empirical Tables
- **Table 8.1**: Tabular Models Benchmark & Leakage Audit (`tables/tab_8_1_tabular_models.md`)
- **Table 8.2**: Vision V2 Regional Models Empirical Performance & 95% CI (`tables/tab_8_2_vision_v2_models.md`)
- **Table 8.3**: Vision V1 vs V2 Architectural Comparison (`tables/tab_8_3_vision_v1_vs_v2.md`)
- **Table 8.4**: TFLite Float32 vs INT8 DRQ Model Parity & Sizes (`tables/tab_8_4_tflite_f32_vs_drq.md`)
- **Table 8.5**: Inference Latency & Edge CPU Throughput (`tables/tab_8_5_inference_latency.md`)
- **Table 8.6**: Alternative Approaches Investigated & Omission Reasons (`tables/tab_8_6_alternative_approaches.md`)
- **Table 8.7**: System Requirement Coverage Matrix (`tables/tab_8_7_requirement_coverage.md`)
- **Table 8.8**: Known System Limitations & Clinical Boundaries (`tables/tab_8_8_known_limitations.md`)
- **Discussion Narrative**: In-depth analysis of tradeoffs, leakage separation, and future directions (`facts/discussion.md`)

---

## Complete Headless Screenshot Inventory

| Screenshot ID | Artifact File | View Description |
|---|---|---|
| Shot 01 | `screenshots/01_landing_page.png` | Initial landing page with Auth Form and disclaimer banner |
| Shot 02 | `screenshots/02_disclaimer_banner.png` | Crop of persistent top educational disclaimer banner |
| Shot 03 | `screenshots/03_emergency_modal.png` | Urgent Help Modal with local 911 / 112 emergency hotlines |
| Shot 04 | `screenshots/04_consent_gate.png` | Mandatory Terms & Consent Gate Modal prior to assessment |
| Shot 05 | `screenshots/05_dashboard.png` | Clinical suite dashboard with 8 functional module tiles |
| Shot 06 | `screenshots/06_explorer_selection.png` | Symptom Reference Explorer symptom selection interface |
| Shot 07 | `screenshots/07_explorer_results.png` | Explorer match results, percentages, and deficiency risk |
| Shot 08 | `screenshots/08_explorer_why.png` | "Why this condition?" clinical rationale disclosure |
| Shot 09 | `screenshots/09_insufficient_info.png` | Insufficient Information warning triggered by sparse input |
| Shot 10 | `screenshots/10_medbot_mode.png` | MedBot interview mode selector (Guided vs Quick) |
| Shot 11 | `screenshots/11_medbot_question.png` | MedBot targeted questioning with speech listening badge |
| Shot 12 | `screenshots/12_medbot_chips.png` | Interactive clinical symptom chips & free-text input |
| Shot 13 | `screenshots/13_medbot_summary.png` | Final conversational summary & deficiency risk profile |
| Shot 14 | `screenshots/14_medscan_accepted.png` | MedScan valid photograph intake and preview |
| Shot 15 | `screenshots/15_medscan_rejected.png` | MedScan quality rejection dialog (blur/lighting feedback) |
| Shot 16 | `screenshots/16_medscan_checklist.png` | Model classification confidence bars and checklist |
| Shot 17 | `screenshots/17_nursebot_faq.png` | NurseBot clinical health guidance response |
| Shot 18 | `screenshots/18_nursebot_medlineplus.png` | MedlinePlus peer-reviewed web answer with citation link |
| Shot 19 | `screenshots/19_nursebot_emergency.png` | Emergency redirection triage triggered by acute chest pain |
| Shot 20 | `screenshots/20_virtual_ward.png` | Virtual Ward facility directory, map, and patient monitor |
| Shot 21 | `screenshots/21_careplan_tasks.png` | Daily care plan checklist (hydration, nutrition tasks) |
| Shot 22 | `screenshots/22_careplan_meals.png` | Meal planner micronutrient & caloric composition matrix |
| Shot 23 | `screenshots/23_careplan_ics.png` | RFC 5545 iCalendar feed export & CalDAV subscription |
| Shot 24a-f | `screenshots/24a_reports_chart1.png` .. `24f` | 6 Interactive temporal health trend charts |
| Shot 25 | `screenshots/25_report_card.png` | Patient Clinical Report Card comprehensive summary |
| Shot 26 | `screenshots/26_print_preview.png` | High-contrast Print View CSS without navigation chrome |
| Shot 27 | `screenshots/27_mllab_tabular.png` | ML Lab tabular benchmark table (no-labs vs symptoms) |
| Shot 28 | `screenshots/28_mllab_vision.png` | ML Lab vision benchmark (7 MobileNetV2 models) |
| Shot 29 | `screenshots/29_model_card_detail.png` | Detailed Model Card JSON metadata inspection |
| Shot 30 | `screenshots/30_openapi_docs.png` | FastAPI interactive Swagger UI (/docs) |
| Shot 31 | `screenshots/31_health_json.png` | Backend health check JSON payload (/v1/health) |
| Shot 32 | `screenshots/32_mobile_view.png` | Mobile viewport responsive layout (375x667) |
| Shot 33 | `screenshots/33_terminal_services.png` | Terminal console log showing all 4 running microservices |
| Shot 34 | `screenshots/34_github_ci_status.png` | GitHub Actions CI/CD workflows and Pages deployment |
| Shot 35 | `screenshots/35_project_tree.png` | Clean monorepo directory tree specification |

---

*Educational Prototype — Not a Medical Device. Generated by Automated Research Audit.*
""")

print("Successfully generated REPORT_DATA.md and MANIFEST.csv!")
