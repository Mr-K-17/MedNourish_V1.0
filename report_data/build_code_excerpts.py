import os

root = r"C:\Users\USER\Desktop\MedNourish-Dev"
out_dir = os.path.join(root, "report_data", "code_excerpts")
os.makedirs(out_dir, exist_ok=True)

def find_range(rel_path, search_term, n_lines=30):
    abs_path = os.path.join(root, rel_path.replace("/", "\\"))
    with open(abs_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for idx, line in enumerate(lines):
        if search_term.lower() in line.lower():
            start = max(1, idx - 2)
            end = min(len(lines), start + n_lines - 1)
            return start, end, lines[start-1:end]
    return 1, min(len(lines), n_lines), lines[:n_lines]

excerpts_meta = [
    ("matcher_core", "backend/app/services/scoring_service.py", "def match_conditions", 32,
     "Core inverted-index symptom matcher resolving candidate conditions against user-selected clinical signs. Computes candidate match overlap and extracts condition-specific weight vectors deterministically."),
     
    ("scoring_formulas", "backend/app/services/scoring_service.py", "def calculate_risk_band", 30,
     "Implements the Noisy-OR probabilistic combination and shrinkage scaling factor k = min(1.0, 0.4 + 0.2*m). Clamps probabilities to [0,1] and categorizes risk into High (>=60%), Moderate (>=30%), and Low bands."),
     
    ("symptom_extraction", "backend/app/services/extraction_service.py", "def extract_symptoms", 32,
     "Parses unstructured user text using clinical synonym dictionaries and negation detection rules ('no', 'not', 'denies'). Prevents false-positive symptom confirmation without requiring external LLM dependencies."),
     
    ("tabular_preprocessor", "ml/train_tabular.py", "def preprocess_data", 30,
     "Prepares 4,000 tabular clinical records across three feature profiles (with_labs, no_labs, symptoms_only). Purges biochemical target leakage features (Ferritin, Vitamin D) to ensure honest real-world evaluation."),
     
    ("vision_model_builder", "ml/train_vision_v2.py", "def build_model", 32,
     "Constructs the MobileNetV2 transfer learning architecture (160x160x3 input) with inverted residuals, GlobalAveragePooling2D, dropout (0.2), and dense softmax classification for 7 regional anatomical targets."),
     
    ("tflite_parity_check", "ml/reevaluate_vision.py", "def evaluate_tflite", 30,
     "Evaluates numerical agreement and top-1 prediction parity between Float32 Keras checkpoints and Dynamic Range Quantized (DRQ) INT8 TFLite models on unseen test splits."),
     
    ("medscan_quality_audit", "backend/app/services/medscan_service.py", "def assess_quality", 28,
     "Enforces input image quality gating using cv2.Laplacian variance for blur detection (threshold >= 50.0) and grayscale mean intensity for illumination bounding (40 <= mean <= 225). Rejects invalid images."),
     
    ("medscan_shortcut_blend", "backend/app/services/medscan_service.py", "shortcut", 28,
     "Applies confidence discounting (heuristic penalty coefficient 0.55) to classes exhibiting high background shortcut risk, preventing the vision model from exploiting spurious image artifacts."),
     
    ("nursebot_router_webanswer", "backend/app/services/nursebot_service.py", "def answer_query", 30,
     "Routes user health queries through an emergency triage detector first; if safe, queries the local curated knowledge base and falls back to NIH MedlinePlus REST API with full citation grounding."),
     
    ("reports_aggregation", "backend/app/services/reports_aggregate_service.py", "def aggregate_risk", 30,
     "Executes exponential time-decay weighting (half-life = 7.0 days, lambda = 0.099) across historical Explorer, MedBot, and MedScan assessments to synthesize a unified temporal deficiency trajectory."),
     
    ("careplan_meal_planner", "backend/app/services/meal_plan_service.py", "def generate_meal_plan", 32,
     "Synthesizes daily meal and micronutrient recommendations from curated food_items.csv based on detected deficiency risks and user dietary constraints (e.g. Vegan, Caloric budget) with 0 string truncation."),
     
    ("careplan_ics_export", "backend/app/services/careplan_sync_service.py", "def export_ics", 32,
     "Serializes daily nutrition, hydration, and lifestyle checklists into standard RFC 5545 iCalendar (.ics) format with VEVENT, UID, DTSTAMP, and RRULE for live sync with external calendar clients."),
     
    ("db_mode_switch", "backend/app/db/session.py", "DB_MODE", 30,
     "Dynamically configures SQLAlchemy engine connections between SQLite (in-memory/file for rapid local testing) and MySQL (production localhost) based on environment configuration without code changes."),
     
    ("consent_auth_dependency", "backend/app/core/auth.py", "def verify_consent", 30,
     "FastAPI dependency intercepting incoming requests to verify valid Bearer JWT authentication and check database consent logs, returning HTTP 403 Forbidden if user consent has not been recorded."),
     
    ("safety_claims_scanner", "backend/scripts/scan_safety_claims.py", "def scan_file", 32,
     "Automated AST and regex auditing script that inspects project files for prohibited medical claims ('diagnoses', 'prescribes', 'cures') and verifies mandatory non-diagnostic disclaimer compliance.")
]

for name, rel_path, term, n_lines, explanation in excerpts_meta:
    start, end, lines = find_range(rel_path, term, n_lines)
    snippet = "".join(lines)
    
    file_content = f"""# Code Excerpt: `{name}`

- **Repository Path**: [`{rel_path}`](file:///{root.replace('\\\\', '/')}/{rel_path}#L{start}-L{end})
- **Lines**: {start}–{end} ({end - start + 1} lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
{explanation}

```python
{snippet.strip()}
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
"""
    out_file = os.path.join(out_dir, f"{name}.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(file_content)

print(f"Generated {len(excerpts_meta)} code excerpts!")
