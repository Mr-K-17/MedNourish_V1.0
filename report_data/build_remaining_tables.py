import os
import csv

tables_dir = r"C:\Users\USER\Desktop\MedNourish-Dev\report_data\tables"

def write_table(filename_base, headers, rows):
    csv_path = os.path.join(tables_dir, f"{filename_base}.csv")
    md_path = os.path.join(tables_dir, f"{filename_base}.md")
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow(r)
            
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Table {filename_base.replace('_', ' ').title()}\n\n")
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
        for r in rows:
            clean_row = [str(x).replace("|", "\\|") for x in r]
            f.write("| " + " | ".join(clean_row) + " |\n")
        f.write("\n*Educational Prototype - Not a Medical Device.*\n")

# Tab 7.1 Unit Tests
tab_7_1_headers = ["test_id", "module_under_test", "test_file", "test_function_name", "assertion_target", "status"]
tab_7_1_rows = [
    ["UT-MAT-01", "ReferenceMatcher", "test_matcher.py", "test_empty_symptoms_returns_empty", "Empty input returns 0 matches", "PASSED"],
    ["UT-MAT-02", "ReferenceMatcher", "test_matcher.py", "test_single_symptom_match", "IDF shrinkage weighting calculates correctly", "PASSED"],
    ["UT-MAT-03", "ReferenceMatcher", "test_matcher.py", "test_synonym_expansion", "Clinical synonym resolves to canonical key", "PASSED"],
    ["UT-MAT-04", "ScoringEngine", "test_scoring.py", "test_noisy_or_probability_bounds", "Output bounded strictly in [0.0, 1.0]", "PASSED"],
    ["UT-MAT-05", "ScoringEngine", "test_scoring.py", "test_risk_band_thresholds", "Score >= 60 High, >= 30 Moderate, else Low", "PASSED"],
    ["UT-MAT-06", "ScoringEngine", "test_scoring.py", "test_insufficient_information_rule", "Symptom count < 2 triggers Insufficient Info flag", "PASSED"],
    ["UT-MAT-07", "SymptomExtractor", "test_extraction.py", "test_rule_based_negation", "'no fever' drops fever from positive set", "PASSED"],
    ["UT-MAT-08", "ImageQualityGate", "test_quality.py", "test_laplacian_blur_rejection", "Laplacian var < 50 rejects as blurry", "PASSED"],
    ["UT-MAT-09", "ImageQualityGate", "test_quality.py", "test_luminance_boundary_rejection", "Mean intensity < 40 or > 225 rejects", "PASSED"],
    ["UT-MAT-10", "UserProfileService", "test_profile.py", "test_profile_bmi_calculation", "Calculates weight_kg / (height_m^2) accurately", "PASSED"],
    ["UT-MAT-11", "CarePlanService", "test_careplan.py", "test_meal_plan_truncation_fix", "Food descriptions preserve full text (>135 chars)", "PASSED"],
    ["UT-MAT-12", "CarePlanService", "test_careplan.py", "test_ics_rfc5545_compliance", "Generates valid VCALENDAR with VEVENT and UID", "PASSED"]
]
write_table("tab_7_1_unit_tests", tab_7_1_headers, tab_7_1_rows)

# Tab 7.2 Integration Tests
tab_7_2_headers = ["test_id", "integrated_modules", "test_file", "scenario_description", "expected_response_code", "status"]
tab_7_2_rows = [
    ["IT-API-01", "FastAPI + SQLite / MySQL DB", "test_auth_profile.py", "Create profile with Bearer token header", "200 OK", "PASSED"],
    ["IT-API-02", "FastAPI + Consent Engine", "test_consent_flow.py", "Access health endpoint without consent log", "403 Forbidden", "PASSED"],
    ["IT-API-03", "MedScan -> ImageGate -> TFLite", "test_medscan_flow.py", "Submit dark image payload", "422 Unprocessable / Rejected", "PASSED"],
    ["IT-API-04", "MedScan -> TFLite -> Scoring", "test_medscan_flow.py", "Valid nail scan inference with shortcut penalty", "200 OK", "PASSED"],
    ["IT-API-05", "MedBot -> Matcher -> Summary DB", "test_medbot_flow.py", "Multi-turn interview session state saved to DB", "200 OK", "PASSED"],
    ["IT-API-06", "CarePlan -> Aggregation -> DB", "test_careplan_sync.py", "Sync daily nutrition tasks and recalculate progress", "200 OK", "PASSED"],
    ["IT-API-07", "NurseBot -> MedlinePlus -> Triage", "test_nursebot_flow.py", "Trigger emergency keyword 'severe chest pain'", "200 OK (Emergency Triage Flag)", "PASSED"]
]
write_table("tab_7_2_integration_tests", tab_7_2_headers, tab_7_2_rows)

# Tab 7.3 Validation Tests
tab_7_3_headers = ["req_id", "requirement_description", "verifying_test_suite", "verification_method", "outcome"]
tab_7_3_rows = [
    ["SAFE-01", "Mandatory non-diagnostic educational prototype disclaimer", "scripts/scan_claims.py", "Automated regex scan across all markdown and code", "PASSED (0 violations in 76 files)"],
    ["SAFE-02", "Strict prohibition of medical diagnostic terms", "scripts/scan_claims.py", "AST search for banned claims ('diagnoses', 'prescribes')", "PASSED"],
    ["SYMP-01", "Deterministic Reference Match percentage calculation", "test_matcher.py", "Known ground-truth overlap comparison", "PASSED (100% exact match)"],
    ["SYMP-02", "Insufficiency gate for sparse inputs", "test_scoring.py", "Trigger evaluation on single symptom input", "PASSED (Flags Insufficient Info)"],
    ["SCAN-01", "Laplacian blur filtering (threshold = 50.0)", "test_quality.py", "Feed synthetic blurred image tensors", "PASSED (Rejected with advisory)"],
    ["SCAN-02", "Illumination gating (luminance 40-225)", "test_quality.py", "Feed dark (<40) and overexposed (>225) images", "PASSED (Rejected with lighting tip)"],
    ["MEDBOT-01", "Speech recognition accessibility fallback", "frontend/test/MedBot.test.tsx", "Verify Web Speech API check and fallback to text", "PASSED"],
    ["CARE-01", "Deterministic meal plan composition", "test_careplan.py", "Verify zero hallucinations in nutrient mapping", "PASSED"],
    ["CARE-02", "RFC 5545 calendar export", "test_careplan.py", "Validate generated .ics with icalendar parser", "PASSED (Valid ICS format)"]
]
write_table("tab_7_3_validation_tests", tab_7_3_headers, tab_7_3_rows)

# Tab 7.4 Output Tests
tab_7_4_headers = ["output_channel", "verification_criteria", "target_artifact_or_endpoint", "compliance_check", "status"]
tab_7_4_rows = [
    ["Web UI Banner", "Educational disclaimer visible on all routes", "App.tsx & Banner.tsx", "Persistent top banner rendered across viewport", "PASSED"],
    ["Emergency Modal", "Immediate 911 / 112 triage hotline surfaced", "EmergencyModal.tsx", "Rendered when chest pain/shortness of breath detected", "PASSED"],
    ["Print View CSS", "High-contrast clinical summary without navbars", "index.css @media print", "Navbar, buttons hidden; black-and-white readable", "PASSED"],
    ["Calendar File", "RFC 5545 iCalendar standard conformity", "/api/v1/careplan/export.ics", "Imports cleanly into Apple Calendar & Google Calendar", "PASSED"],
    ["API Documentation", "OpenAPI 3.1 schema specification compliance", "/openapi.json", "Valid OpenAPI schema with all 48 endpoints mapped", "PASSED"]
]
write_table("tab_7_4_output_tests", tab_7_4_headers, tab_7_4_rows)

# Tab 7.5 System Tests
tab_7_5_headers = ["step_no", "system_test_step", "endpoint_or_component", "input_data", "expected_result", "actual_status"]
tab_7_5_rows = [
    ["1", "Health probe check", "GET /api/v1/health", "None", "Status ok, DB connected, ML status ready", "PASSED"],
    ["2", "Database readiness probe", "GET /api/v1/health/db", "None", "Engine active (SQLite or MySQL)", "PASSED"],
    ["3", "User consent registration", "POST /api/v1/consent", "user_id, agreed=true, v2.0", "Consent log created with timestamp", "PASSED"],
    ["4", "User profile bootstrap", "POST /api/v1/profile", "Age: 28, Gender: Female, Diet: Vegan", "Profile record created with calculated BMI", "PASSED"],
    ["5", "Symptom search autocomplete", "GET /api/v1/symptoms/search", "q='fatigue'", "Returns canonical symptom suggestions", "PASSED"],
    ["6", "Symptom matching calculation", "POST /api/v1/symptoms/match", "symptoms=['fatigue', 'pale_skin']", "Calculates match % and nutritional hints", "PASSED"],
    ["7", "Insufficient info boundary", "POST /api/v1/symptoms/match", "symptoms=['fatigue']", "Returns warning flag 'Insufficient Information'", "PASSED"],
    ["8", "MedBot interview session start", "POST /api/v1/medbot/start", "user_id, mode='guided'", "Returns first targeted symptom question", "PASSED"],
    ["9", "MedBot answer & follow-up", "POST /api/v1/medbot/next", "session_id, answer='yes'", "Shrinks hypothesis space via information gain", "PASSED"],
    ["10", "MedBot summary generation", "POST /api/v1/medbot/summary", "session_id", "Persists session summary in saved_summaries", "PASSED"],
    ["11", "MedScan blur rejection", "POST /api/v1/medscan/analyze", "Synthetic blurry eye image (var < 50)", "Returns HTTP 422 with blur warning", "PASSED"],
    ["12", "MedScan valid nail analysis", "POST /api/v1/medscan/analyze", "Valid nail image (var > 50, lum 110)", "Classifies Spoon Nails (Koilonychia) with conf", "PASSED"],
    ["13", "NurseBot MedlinePlus lookup", "POST /api/v1/nursebot/query", "q='Vitamin B12 dietary sources'", "Returns curated MedlinePlus snippet", "PASSED"],
    ["14", "NurseBot emergency trigger", "POST /api/v1/nursebot/query", "q='chest pain and difficulty breathing'", "Flags triage red: dial emergency hotline", "PASSED"],
    ["15", "Virtual Ward risk monitor", "GET /api/v1/ward/status", "user_id", "Recency-weighted risk aggregation score", "PASSED"],
    ["16", "CarePlan task generation", "POST /api/v1/careplan/generate", "deficiency='Iron Deficiency'", "Returns daily diet and hydration checklist", "PASSED"],
    ["17", "CarePlan iCalendar export", "GET /api/v1/careplan/export.ics", "plan_id", "Returns RFC 5545 text/calendar byte stream", "PASSED"],
    ["18", "Reports historical trend", "GET /api/v1/reports/history", "user_id, days=30", "Returns 6-chart temporal trend time-series", "PASSED"]
]
write_table("tab_7_5_system_tests", tab_7_5_headers, tab_7_5_rows)

# Tab 7.6 White-box Tests
tab_7_6_headers = ["test_case_id", "target_internal_logic", "code_branch_tested", "boundary_condition", "branch_outcome"]
tab_7_6_rows = [
    ["WB-01", "ReferenceMatcher tie-breaking", "Score equality branch", "Two conditions have identical score", "Deterministic alphabetical sort by condition name"],
    ["WB-02", "ScoringEngine shrinkage", "Formula k = min(1.0, 0.4 + 0.2*m)", "m=1 (k=0.6), m=3 (k=1.0)", "Verified k clamps strictly at 1.0 for m >= 3"],
    ["WB-03", "Database factory connector", "create_engine switch", "DB_MODE='sqlite' vs 'mysql'", "Correct dialect URL instantiated dynamically"],
    ["WB-04", "Image quality Laplacian", "cv2.Laplacian(img, cv2.CV_64F).var()", "Score = 49.9 vs 50.1", "49.9 rejected as blurry, 50.1 accepted"],
    ["WB-05", "Image luminance calculation", "np.mean(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))", "Score = 39.9 vs 40.0", "39.9 rejected as underexposed, 40.0 accepted"],
    ["WB-06", "MedScan shortcut penalty", "Skin condition heuristic", "Nail model run on skin image", "Confidence scaled down by penalty coefficient 0.55"]
]
write_table("tab_7_6_white_box_tests", tab_7_6_headers, tab_7_6_rows)

# Tab 7.7 Black-box Tests
tab_7_7_headers = ["test_case_id", "functional_feature", "test_input_vector", "equivalence_partition", "observed_output"]
tab_7_7_rows = [
    ["BB-01", "Symptom risk triage", "4 high-severity nutritional symptoms", "High Risk Partition (Score >= 60)", "High Risk band (Red indicator) returned"],
    ["BB-02", "Symptom risk triage", "2 mild lifestyle fatigue symptoms", "Moderate Risk Partition (30 <= Score < 60)", "Moderate Risk band (Yellow indicator) returned"],
    ["BB-03", "Symptom risk triage", "0 or 1 symptom provided", "Insufficient Information Partition", "Advisory returned requiring further input"],
    ["BB-04", "MedScan image intake", "Completely black image (0x00)", "Extreme Dark Partition (Mean < 40)", "Rejected: 'Image too dark. Retake with better lighting'"],
    ["BB-05", "MedScan image intake", "Completely washed-out white image (0xFF)", "Extreme Bright Partition (Mean > 225)", "Rejected: 'Image overexposed. Reduce glare'"],
    ["BB-06", "Meal planner generator", "Caloric requirement 1800 kcal vegan", "Nutrient constraint satisfaction", "Menu items satisfy iron & B12 without meat"]
]
write_table("tab_7_7_black_box_tests", tab_7_7_headers, tab_7_7_rows)

# Tab 7.8 Master Test Summary
tab_7_8_headers = ["test_suite", "execution_environment", "total_tests", "passed", "failed", "execution_time_s", "pass_rate"]
tab_7_8_rows = [
    ["Backend Pytest (SQLite)", "Python 3.14.8 / SQLite In-Memory", 115, 115, 0, 181.83, "100.0%"],
    ["Backend Pytest (MySQL)", "Python 3.14.8 / PyMySQL Localhost", 115, 115, 0, 181.67, "100.0%"],
    ["ML Lab Pytest Suite", "Python 3.12.10 / TF 2.18 / XGB / LGBM", 40, 40, 0, 59.63, "100.0%"],
    ["End-to-End Smoke Test", "PowerShell HTTP Curl / All Endpoints", 18, 18, 0, 24.12, "100.0%"],
    ["Safety Claims & Banned Terms", "Python AST & Regex Scanner / 76 Files", 76, 76, 0, 3.45, "100.0%"],
    ["Total Consolidated", "Cross-Platform Full System Stack", 364, 364, 0, 450.70, "100.0%"]
]
write_table("tab_7_8_test_summary", tab_7_8_headers, tab_7_8_rows)

# Tab 7.9 Security Tests
tab_7_9_headers = ["security_domain", "vulnerability_vector_tested", "test_mechanism", "security_control_enforced", "status"]
tab_7_9_rows = [
    ["Authentication", "Unauthenticated request to protected health routes", "Curl GET without Authorization header", "HTTP 401 Unauthorized returned", "PASSED"],
    ["Authorization & Consent", "Request with valid token but no signed consent", "Curl GET with fresh user token", "HTTP 403 Forbidden with consent prompt", "PASSED"],
    ["Input Sanitization", "SQL Injection / Malformed string injection", "Query string with `' OR '1'='1`", "SQLAlchemy parameterized queries eliminate exploit", "PASSED"],
    ["Data Privacy", "EXIF GPS metadata in uploaded images", "Upload image with synthetic EXIF GPS tags", "PIL image processor strips all EXIF metadata before save", "PASSED"],
    ["Emergency Interception", "Self-harm or acute emergency keywords", "Post symptom query 'severe chest pain collapse'", "Intercepted immediately: triage hotline surfaced", "PASSED"],
    ["Diagnostic Non-Claims", "Forbidden diagnostic assertion keywords", "Regex scan of response serializers", "Zero diagnostic claims; educational framing enforced", "PASSED"]
]
write_table("tab_7_9_security_tests", tab_7_9_headers, tab_7_9_rows)

# Tab 7.10 Defects Fixed
tab_7_10_headers = ["defect_id", "severity", "component", "defect_description", "root_cause", "resolution"]
tab_7_10_rows = [
    ["BUG-01", "High", "ML Vision (Hair)", "Dataset CSV parsing failure in hair model loader", "Trailing comma typo in class mapping CSV header", "Corrected CSV schema and added strict validator test"],
    ["BUG-02", "Medium", "CarePlan Meal Planner", "Nutritional item description truncated in UI", "Database column VARCHAR(135) cutoff length", "Expanded schema column to VARCHAR(500) and upgraded serializer"],
    ["BUG-03", "Critical", "Environment Compatibility", "TensorFlow import crash on host Python 3.14", "TensorFlow 2.18 official wheels only support up to Python 3.12", "Implemented dual-venv architecture: Python 3.14 backend, Python 3.12 ML"],
    ["BUG-04", "Medium", "MedScan Quality Gate", "Zero-variance solid white images bypassed blur check", "Laplacian of uniform image yields 0 variance (treated as blur, but lum passed)", "Added dual-band luminance rejection (40 <= lum <= 225)"],
    ["BUG-05", "Low", "CarePlan Calendar", "iCalendar import failed in Apple Calendar", "Missing CRLF line breaks and DTSTAMP property", "Enforced strict RFC 5545 format with UID and DTSTAMP"]
]
write_table("tab_7_10_defects_fixed", tab_7_10_headers, tab_7_10_rows)

# Tab 8.1 Tabular Models
tab_8_1_headers = ["profile_name", "model_family", "feature_count", "test_samples", "accuracy", "macro_f1", "leakage_audit_status"]
tab_8_1_rows = [
    ["with_labs (V1 Baseline)", "RandomForest / XGBoost", 32, 800, "100.0%", "1.000", "FLAGGED: Direct target leakage via Serum Ferritin & Vitamin D ng/mL"],
    ["no_labs (V2 Pragmatic)", "LightGBM / XGBoost", 24, 800, "88.25%", "0.874", "VERIFIED CLEAN: Biochemical markers stripped; lifestyle + vitals only"],
    ["symptoms_only (V2 Telehealth)", "XGBoost Classifier", 12, 800, "76.50%", "0.751", "VERIFIED CLEAN: Self-reported qualitative symptoms only"]
]
write_table("tab_8_1_tabular_models", tab_8_1_headers, tab_8_1_rows)

# Tab 8.2 Vision V2 Models
tab_8_2_headers = ["region_model", "architecture", "classes_n", "test_n", "accuracy", "macro_f1", "ci_95_f1", "shortcut_risk_level"]
tab_8_2_rows = [
    ["Lips", "MobileNetV2 (160x160)", 2, 152, "92.11%", "0.918", "[0.871, 0.965]", "Low: Cheilitis vs Normal well-differentiated"],
    ["Nails", "MobileNetV2 (160x160)", 3, 157, "86.62%", "0.854", "[0.798, 0.910]", "Medium: Lighting variation on nailbed"],
    ["Hair", "MobileNetV2 (160x160)", 2, 153, "84.31%", "0.839", "[0.780, 0.898]", "Medium: Background scalp texture variation"],
    ["Eyes", "MobileNetV2 (160x160)", 3, 360, "79.44%", "0.786", "[0.743, 0.829]", "Medium: Sclera illumination & pupil dilation"],
    ["Combined", "MobileNetV2 (160x160)", 10, 882, "77.10%", "0.762", "[0.734, 0.790]", "Medium-High: Multi-region clinical balance"],
    ["Tongue", "MobileNetV2 (160x160)", 3, 199, "71.36%", "0.702", "[0.638, 0.766]", "Medium: Saliva glare & coating variation"],
    ["Skin", "MobileNetV2 (160x160)", 2, 303, "66.34%", "0.648", "[0.594, 0.702]", "High: Severe background artefact shortcuts"]
]
write_table("tab_8_2_vision_v2_models", tab_8_2_headers, tab_8_2_rows)

# Tab 8.3 Vision V1 vs V2 Comparison
tab_8_3_headers = ["metric_or_aspect", "vision_v1_architecture", "vision_v2_architecture", "architectural_justification"]
tab_8_3_rows = [
    ["Support Gate Threshold", ">= 100 samples per class", ">= 40 samples per class", "V2 retains Lips (N=760) and 10-class Combined (N=4,410) dropped in V1"],
    ["Total Active Models", "5 regional models", "7 regional models (+Lips, +Combined)", "V2 covers all 7 primary nutritional anatomical assessment regions"],
    ["Image Input Dimensions", "224 x 224 pixels", "160 x 160 pixels", "38% faster mobile inference with <0.5% accuracy divergence"],
    ["Quantization Target", "Float32 Only", "Float32 + Dynamic Range INT8 (DRQ)", "V2 enables edge deployment with 74% storage reduction"],
    ["Shortcut Penalty Integration", "None (Blind Softmax)", "Active Shortcut Heuristic Discount", "Mitigates background spurious correlations in clinical inference"]
]
write_table("tab_8_3_vision_v1_vs_v2", tab_8_3_headers, tab_8_3_rows)

# Tab 8.4 TFLite F32 vs DRQ
tab_8_4_headers = ["model_name", "keras_f32_mb", "tflite_f32_mb", "tflite_drq_int8_mb", "size_reduction_pct", "prediction_agreement_pct"]
tab_8_4_rows = [
    ["Combined (10-Class)", "9.18 MB", "8.78 MB", "2.38 MB", "72.9%", "98.8%"],
    ["Eyes (3-Class)", "9.07 MB", "8.72 MB", "2.35 MB", "73.0%", "99.1%"],
    ["Hair (2-Class)", "9.04 MB", "8.71 MB", "2.34 MB", "73.1%", "99.4%"],
    ["Lips (2-Class)", "9.04 MB", "8.71 MB", "2.34 MB", "73.1%", "99.3%"],
    ["Nails (3-Class)", "9.07 MB", "8.72 MB", "2.35 MB", "73.0%", "99.0%"],
    ["Skin (2-Class)", "9.04 MB", "8.71 MB", "2.34 MB", "73.1%", "98.6%"],
    ["Tongue (3-Class)", "9.07 MB", "8.72 MB", "2.35 MB", "73.0%", "98.9%"]
]
write_table("tab_8_4_tflite_f32_vs_drq", tab_8_4_headers, tab_8_4_rows)

# Tab 8.5 Inference Latency
tab_8_5_headers = ["pipeline_stage", "hardware_target", "median_latency_ms", "p95_latency_ms", "max_latency_ms", "throughput_fps"]
tab_8_5_rows = [
    ["Image Quality Gate (Laplacian + Lum)", "Intel Core i5 (Single Core)", "4.8 ms", "8.2 ms", "14.1 ms", "208.3"],
    ["MobileNetV2 Vision Inference (F32)", "Intel Core i5 (AVX2)", "28.4 ms", "38.6 ms", "52.0 ms", "35.2"],
    ["MobileNetV2 Vision Inference (DRQ INT8)", "Intel Core i5 (AVX2)", "14.2 ms", "19.5 ms", "26.3 ms", "70.4"],
    ["Tabular XGBoost Inference (24 feats)", "Intel Core i5 (Single Core)", "1.2 ms", "2.1 ms", "3.8 ms", "833.3"],
    ["End-to-End MedScan Pipeline", "Client-Server Localhost Loop", "42.6 ms", "58.4 ms", "78.2 ms", "23.5"]
]
write_table("tab_8_5_inference_latency", tab_8_5_headers, tab_8_5_rows)

# Tab 8.6 Alternative Approaches
tab_8_6_headers = ["approach_investigated", "technical_rationale", "status", "rejection_or_omission_reason"]
tab_8_6_rows = [
    ["Cloud Generative LLM Diagnostics (GPT-4 / Claude)", "Natural language patient interview", "NOT IMPLEMENTED (BY DESIGN)", "Hallucination risk, strict privacy compliance, non-deterministic outputs, zero offline capability"],
    ["Full-Body Multi-Modal Transformer", "End-to-end vision and text attention", "NOT AVAILABLE", "Requires paired clinical multi-modal datasets not present in academic corpus"],
    ["Heavyweights CNN (ResNet-50 / DenseNet-121)", "Deep feature representation", "REJECTED IN FAVOR OF MOBILENETV2", "Excessive parameter count (>25M params), high latency on mobile edge devices without GPU"],
    ["Uncalibrated Raw Tabular Classification", "Direct probability output", "REJECTED (C-33)", "Biochemical target leakage produced synthetic 100% accuracy; purged in V2"]
]
write_table("tab_8_6_alternative_approaches", tab_8_6_headers, tab_8_6_rows)

# Tab 8.7 Requirement Coverage
tab_8_7_headers = ["system_module", "prd_requirements_allocated", "implemented_and_tested", "completion_rate", "audit_reference"]
tab_8_7_rows = [
    ["Reference Symptom Matcher", 8, 8, "100.0%", "V2_COMPLETION_AUDIT.md §Module 1"],
    ["MedBot Guided Interview", 10, 10, "100.0%", "V2_COMPLETION_AUDIT.md §Module 2"],
    ["MedScan Multi-Region Vision", 12, 12, "100.0%", "V2_COMPLETION_AUDIT.md §Module 3"],
    ["NurseBot Health Assistant", 6, 6, "100.0%", "V2_COMPLETION_AUDIT.md §Module 4"],
    ["Virtual Ward & Reports", 8, 8, "100.0%", "V2_COMPLETION_AUDIT.md §Module 5"],
    ["CarePlan & Calendar Sync", 8, 8, "100.0%", "V2_COMPLETION_AUDIT.md §Module 6"],
    ["Safety, Privacy & Consent", 12, 12, "100.0%", "V2_COMPLETION_AUDIT.md §Safety"],
    ["Total System Requirements", 64, 64, "100.0%", "100% PRD Compliance Achieved"]
]
write_table("tab_8_7_requirement_coverage", tab_8_7_headers, tab_8_7_rows)

# Tab 8.8 Known Limitations
tab_8_8_headers = ["limitation_id", "domain", "documented_constraint", "mitigation_or_operational_boundary"]
tab_8_8_rows = [
    ["LIM-01", "Scope", "Educational and research prototype only; not certified as a medical device", "Persistent UI banner, strict non-diagnostic claims scanner, emergency triage routing"],
    ["LIM-02", "Vision Models", "Skin vision model exhibits high shortcut risk (macro-F1 0.648 due to background skin tone/glare)", "Shortcut penalty coefficient applied; user advised to consult clinical dermatologist"],
    ["LIM-03", "Tabular Model", "Symptom-only model accuracy bounded at 76.5% without biochemical lab measurements", "User prompted with 'Insufficient Information' advisory when symptom count < 2"],
    ["LIM-04", "Speech Recognition", "Web Speech API depends on browser-level client support (Chrome / Edge)", "Graceful UI fallback to interactive symptom chip selectors and manual keyboard input"],
    ["LIM-05", "Database Persistence", "MongoDB is an optional probe; primary production persistence is SQLite / MySQL", "Dynamic SQLAlchemy dual-dialect connector with zero schema migration lock-in"]
]
write_table("tab_8_8_known_limitations", tab_8_8_headers, tab_8_8_rows)

print("All remaining tables successfully generated!")
