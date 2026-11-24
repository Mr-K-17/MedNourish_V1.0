import os
from PIL import Image, ImageDraw, ImageFont

diag_dir = r"C:\Users\USER\Desktop\MedNourish-Dev\report_data\diagrams"
src_dir = os.path.join(diag_dir, "src")
os.makedirs(diag_dir, exist_ok=True)
os.makedirs(src_dir, exist_ok=True)

# Helper to create diagram canvas
def create_diag_canvas(width=2400, height=1400, fig_no="", title="", subtitle=""):
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    # Header
    draw.rectangle([30, 30, width - 30, 110], fill="#f8fafc", outline="#cbd5e1", width=2)
    draw.text((60, 45), f"{fig_no}: {title}", fill="#0f172a")
    if subtitle:
        draw.text((60, 75), subtitle, fill="#475569")
    # Footer
    draw.line([(30, height - 60), (width - 30, height - 60)], fill="#e2e8f0", width=2)
    draw.text((60, height - 45), "MEDNOURISH Architectural Specification | Educational Prototype - Not a Medical Device", fill="#64748b")
    # Outer Border
    draw.rectangle([15, 15, width - 15, height - 15], outline="#94a3b8", width=2)
    return img, draw

def draw_box(draw, x, y, w, h, title, items=None, fill="#ffffff", border="#0f172a", text_color="#0f172a", corner=8):
    draw.rectangle([x, y, x + w, y + h], fill=fill, outline=border, width=2)
    draw.rectangle([x, y, x + w, y + 36], fill="#f1f5f9", outline=border, width=1)
    draw.text((x + 15, y + 10), title, fill=text_color)
    if items:
        cy = y + 48
        for it in items:
            draw.text((x + 15, cy), f"- {it}", fill="#334155")
            cy += 24

def draw_arrow_h(draw, x1, y, x2, label="", color="#334155"):
    draw.line([(x1, y), (x2, y)], fill=color, width=3)
    if x2 > x1:
        draw.polygon([(x2, y), (x2 - 12, y - 6), (x2 - 12, y + 6)], fill=color)
    else:
        draw.polygon([(x2, y), (x2 + 12, y - 6), (x2 + 12, y + 6)], fill=color)
    if label:
        draw.text(((x1 + x2) // 2 - len(label)*3, y - 22), label, fill=color)

def draw_arrow_v(draw, x, y1, y2, label="", color="#334155"):
    draw.line([(x, y1), (x, y2)], fill=color, width=3)
    if y2 > y1:
        draw.polygon([(x, y2), (x - 6, y2 - 12), (x + 6, y2 - 12)], fill=color)
    else:
        draw.polygon([(x, y2), (x - 6, y2 + 12), (x + 6, y2 + 12)], fill=color)
    if label:
        draw.text((x + 12, (y1 + y2) // 2 - 10), label, fill=color)

# List of all 20 diagrams with their specifications and Mermaid definitions
diagrams = [
    {
        "id": "fig_5_1_system_architecture",
        "fig_no": "Figure 5.1",
        "title": "System Architecture of MEDNOURISH",
        "subtitle": "Three-Tier Client-Server Architecture: Frontend (React/TS), Backend API Gateway (FastAPI), ML Engine & Relational DB",
        "boxes": [
            (80, 200, 480, 1000, "Presentation Layer (React 18 / Vite)", [
                "Tailwind CSS & Lucide Icons",
                "Educational Disclaimer Persistent Banner",
                "Module 1: Reference Explorer UI",
                "Module 2: MedBot Conversational UI",
                "Module 3: MedScan Drag-and-Drop Vision UI",
                "Module 4: NurseBot Health FAQ UI",
                "Module 5: Virtual Ward Risk Dashboard",
                "Module 6: CarePlan & CalDAV Sync",
                "Web Speech API (Speech-to-Text Fallback)",
                "HTML5 Canvas Image Processor (EXIF Strip)"
            ], "#f8fafc"),
            (680, 200, 520, 1000, "Application Gateway (FastAPI 0.115)", [
                "Dynamic Database Session Engine (SQLite / MySQL)",
                "Firebase Auth Token Verifier",
                "Mandatory Consent Gate Middleware",
                "Emergency Triage Keyword Interceptor",
                "Inverted Index Clinical Symptom Matcher",
                "Noisy-OR Probabilistic Inference Engine",
                "Laplacian Blur & Dual-Luminance Gate",
                "Recency-Weighted Score Aggregator",
                "RFC 5545 iCalendar Byte Stream Generator",
                "MedlinePlus Knowledge Retrieval Client"
            ], "#f8fafc"),
            (1320, 200, 480, 460, "Edge ML Engine (TFLite / MobileNetV2)", [
                "TF 2.18 / Python 3.12 ML Microservice",
                "7 MobileNetV2 Regional Vision Models (160x160)",
                "Dynamic Range Quantization (INT8 DRQ)",
                "Shortcut Penalty Confidence Calibrator",
                "Tabular XGBoost / LightGBM Classifiers",
                "Dual Feature Profiles (No-Labs / Symptoms-Only)"
            ], "#f8fafc"),
            (1320, 720, 480, 480, "Data Persistence Layer (SQLAlchemy ORM)", [
                "Table: user_profiles (Demographics & Vitals)",
                "Table: user_consent_logs (Audit Trail)",
                "Table: care_plan_items (Checklists)",
                "Table: saved_summaries (MedBot / Matcher)",
                "Table: medscan_sessions (Inference Logs)",
                "Optional Telemetry: MongoDB Probe",
                "Curated CSV / YAML Clinical Knowledge Base"
            ], "#f8fafc"),
            (1920, 200, 400, 1000, "Safety & External Services", [
                "Firebase Auth Emulator (Port 9099)",
                "NIH MedlinePlus Clinical API",
                "Local Emergency 911 / 112 Triage Dispatch",
                "Static Report Card PDF / Print CSS",
                "Strict Non-Diagnostic Claim Enforcer",
                "Prohibited Medical Term Regex Auditor"
            ], "#f8fafc")
        ],
        "arrows": [
            ("h", 560, 400, 680, "HTTPS / JSON"),
            ("h", 680, 600, 560, "REST Responses"),
            ("h", 1200, 400, 1320, "Tensor Arrays"),
            ("h", 1320, 500, 1200, "Class Probabilities"),
            ("v", 1560, 660, 720, "Model Metadata"),
            ("h", 1200, 900, 1320, "SQL Queries"),
            ("h", 1320, 960, 1200, "ORM Entities"),
            ("h", 1200, 320, 1920, "External Probes")
        ],
        "mmd": """graph TD
    subgraph Frontend["Presentation Layer (React 18 / Vite / TS)"]
        UI_Banner["Educational Disclaimer Banner"]
        UI_M1["Symptom Matcher Explorer"]
        UI_M2["MedBot Guided Dialogue"]
        UI_M3["MedScan Camera & Upload"]
        UI_M4["NurseBot Health Assistant"]
        UI_M5["Virtual Ward Risk Monitor"]
        UI_M6["CarePlan & Meal Planner"]
    end
    subgraph Gateway["Application API Gateway (FastAPI / PyMySQL)"]
        AUTH["Firebase Token & Consent Gate"]
        TRIAGE["Emergency Keyword Interceptor"]
        MATCHER["Reference Matcher & Scoring Engine"]
        GATE["Image Quality Gate (Laplacian & Lum)"]
        AGG["Recency Aggregation Engine"]
        ICS["RFC 5545 iCalendar Generator"]
    end
    subgraph MLEngine["Edge Machine Learning Engine"]
        TFLITE["7 MobileNetV2 TFLite DRQ Models"]
        TABULAR["XGBoost Tabular Classifiers"]
        SHORTCUT["Shortcut Penalty Calibrator"]
    end
    subgraph Database["Persistence Layer (SQLAlchemy ORM)"]
        DB_SQL["MySQL / SQLite Relational DB"]
        DB_KNOW["Curated Clinical CSVs & YAML"]
    end
    Frontend -->|HTTPS/REST| Gateway
    Gateway -->|Tensors| MLEngine
    MLEngine -->|Inference Scores| Gateway
    Gateway -->|SQL Queries| Database
"""
    },
    {
        "id": "fig_5_2_proposed_system_modules",
        "fig_no": "Figure 5.2",
        "title": "Proposed System Functional Module Breakdown",
        "subtitle": "Modular Architecture encompassing the 6 core functional subsystems and cross-cutting safety infrastructure",
        "boxes": [
            (80, 200, 350, 450, "Module 1: Reference Explorer", ["Deterministic Inverted Index", "IDF Shrinkage Weighting", "Noisy-OR Aggregation", "Risk Band Classification", "Clinical Synonym Resolver"], "#ffffff"),
            (470, 200, 350, 450, "Module 2: MedBot Interview", ["Targeted Clinical Questioning", "Entropy / Info Gain Selection", "Voice Input (Speech-to-Text)", "Interactive Symptom Chips", "Session Summary Export"], "#ffffff"),
            (860, 200, 350, 450, "Module 3: MedScan Vision", ["7 Anatomical Target Models", "MobileNetV2 160x160", "Laplacian Blur Filtering (>=50)", "Dual Luminance Filter (40-225)", "Shortcut Penalty Heuristic"], "#ffffff"),
            (1250, 200, 350, 450, "Module 4: NurseBot FAQ", ["Curated Health Knowledge", "MedlinePlus Integration", "Emergency Keyword Interceptor", "Red Flag Triage Modal", "Zero-Hallucination Scope"], "#ffffff"),
            (1640, 200, 350, 450, "Module 5: Virtual Ward", ["Recency-Weighted Scoring", "Historical Time-Series View", "6 Interactive Trend Charts", "Printable Health Summary", "Deficiency Risk Monitoring"], "#ffffff"),
            (2030, 200, 320, 450, "Module 6: CarePlan & Cal", ["Daily Nutrition Tasks", "Meal Planner (Macro Guidance)", "RFC 5545 iCalendar Feed", "Task Completion Tracking", "Hydration Monitoring"], "#ffffff"),
            (200, 750, 2000, 500, "Underlying Cross-Cutting Security, Safety & Governance Services", [
                "Mandatory Educational Prototype Non-Diagnostic Disclaimer Banner (Rendered across all UI routes)",
                "Explicit User Consent Logging System (Versioned consent records saved to relational database prior to intake)",
                "Emergency 911 / 112 Triage Interceptor (Immediate modal escalation on chest pain, severe dyspnea, acute distress)",
                "Deterministic Curated Knowledge Base (Knowledge grounded strictly in peer-reviewed clinical tables, eliminating LLM hallucinations)",
                "Client-Side Image Privacy Guard (EXIF metadata stripping and local edge inference support without external cloud transmission)",
                "Automated CI/CD Safety Validator (Scans 76 project files ensuring zero banned diagnostic or prescriptive terminology)"
            ], "#f8fafc")
        ],
        "arrows": [
            ("v", 255, 650, 750, "Enforces"),
            ("v", 645, 650, 750, "Enforces"),
            ("v", 1035, 650, 750, "Enforces"),
            ("v", 1425, 650, 750, "Enforces"),
            ("v", 1815, 650, 750, "Enforces"),
            ("v", 2190, 650, 750, "Enforces")
        ],
        "mmd": """graph LR
    subgraph Core["MEDNOURISH Subsystems"]
        M1["M1: Reference Explorer"]
        M2["M2: MedBot Interview"]
        M3["M3: MedScan Vision"]
        M4["M4: NurseBot FAQ"]
        M5["M5: Virtual Ward"]
        M6["M6: CarePlan & Calendar"]
    end
    subgraph Safety["Safety & Governance Engine"]
        DISC["Non-Diagnostic Disclaimer"]
        CONS["User Consent Gate"]
        EMERG["Emergency Triage Interceptor"]
        EXIF["EXIF Privacy Stripper"]
    end
    Safety --> Core
"""
    },
    {
        "id": "fig_5_3_dfd_level_0",
        "fig_no": "Figure 5.3",
        "title": "Data Flow Diagram (DFD) Level 0 — Context Diagram",
        "subtitle": "System context delineating inputs, outputs, external entities, and high-level boundaries",
        "boxes": [
            (100, 500, 400, 400, "External Entity: User / Patient", [
                "Self-reported symptoms",
                "Anatomical photographs",
                "Health queries",
                "Care plan checkoffs",
                "Consent acknowledgement"
            ], "#f1f5f9"),
            (900, 400, 600, 600, "Process 0.0: MEDNOURISH System", [
                "Validates user consent & auth",
                "Processes clinical symptoms",
                "Audits image quality (blur/lighting)",
                "Executes MobileNetV2 inference",
                "Computes recency risk score",
                "Generates nutrition care plan",
                "Supplies RFC 5545 calendar stream"
            ], "#f8fafc"),
            (1900, 500, 400, 400, "External Services & Clinicians", [
                "NIH MedlinePlus XML/REST",
                "Local Emergency Dispatch",
                "Primary Care Physician (Printout)",
                "Personal Calendar Application"
            ], "#f1f5f9")
        ],
        "arrows": [
            ("h", 500, 550, 900, "Symptoms, Photos, Queries"),
            ("h", 900, 750, 500, "Educational Summaries, Risk Scores, Meals"),
            ("h", 1500, 550, 1900, "Medical Query / Emergency Flag"),
            ("h", 1900, 750, 1500, "MedlinePlus Snippets / Cal Sync")
        ],
        "mmd": """graph LR
    User["User / Patient"]
    System["0.0 MEDNOURISH System"]
    Ext["External Services / Clinician"]
    User -->|Symptoms, Photos, Consent| System
    System -->|Risk Bands, Meal Plans, Summaries| User
    System -->|Health Queries, Emergency Triage| Ext
    Ext -->|MedlinePlus Data, Calendar Sync| System
"""
    },
    {
        "id": "fig_5_4_dfd_level_1",
        "fig_no": "Figure 5.4",
        "title": "Data Flow Diagram (DFD) Level 1 — Decomposed System Flow",
        "subtitle": "Detailed flow across intake, quality validation, inference calculation, persistence, and reporting",
        "boxes": [
            (80, 200, 380, 250, "1.0 User Authentication & Consent", ["Verify Bearer JWT token", "Check consent version log", "Prompt if consent expired"], "#ffffff"),
            (560, 200, 380, 250, "2.0 Symptom Processing", ["Resolve clinical synonyms", "Run Inverted Index lookup", "Calculate shrinkage IDF score"], "#ffffff"),
            (1040, 200, 380, 250, "3.0 Image Audit & Inference", ["Laplacian blur filter (var>=50)", "Luminance check (40-225)", "MobileNetV2 TFLite model"], "#ffffff"),
            (1520, 200, 380, 250, "4.0 Health Q&A & Triage", ["Inspect emergency red-flags", "Query curated knowledge base", "Fetch MedlinePlus guidelines"], "#ffffff"),
            (2000, 200, 350, 250, "5.0 CarePlan & Calendar", ["Synthesize dietary suggestions", "Generate daily checklist", "Encode RFC 5545 iCal stream"], "#ffffff"),
            (400, 700, 700, 450, "Data Store D1: Relational Persistence", [
                "user_profiles (Demographics & Vitals)",
                "user_consent_logs (Audit Records)",
                "medscan_sessions (Inference Outcomes)",
                "saved_summaries (Session Archives)",
                "care_plan_items (Daily Nutrition)"
            ], "#f8fafc"),
            (1300, 700, 700, 450, "Data Store D2: Curated Clinical Repositories", [
                "food_items.csv (Nutrient Compositions)",
                "nutrient_guidance.csv (Daily RDAs)",
                "synonyms.yaml (Standardized Medical Terminology)",
                "Regional Vision Class Maps (7 Target Regions)"
            ], "#f8fafc")
        ],
        "arrows": [
            ("v", 270, 450, 700, "Store Consent"),
            ("v", 750, 450, 700, "Save Session"),
            ("v", 1230, 450, 700, "Store MedScan"),
            ("v", 1710, 450, 700, "Fetch Curated"),
            ("v", 2175, 450, 700, "Sync Tasks")
        ],
        "mmd": """graph TD
    P1["1.0 Auth & Consent"] --> DB1[(D1: Relational DB)]
    P2["2.0 Symptom Matcher"] --> DB2[(D2: Curated Knowledge)]
    P2 --> DB1
    P3["3.0 Image Quality & MedScan"] --> DB1
    P4["4.0 NurseBot Triage"] --> DB2
    P5["5.0 CarePlan & Sync"] --> DB1
    P5 --> DB2
"""
    },
    {
        "id": "fig_5_5_use_case_diagram",
        "fig_no": "Figure 5.5",
        "title": "Use Case Diagram for MEDNOURISH System",
        "subtitle": "Actor interactions across Patient/User, Educational Auditor, and Clinician/Provider",
        "boxes": [
            (100, 300, 350, 800, "Primary Actor: Patient / User", [
                "UC-01: Acknowledge Disclaimer & Consent",
                "UC-02: Manage Health Profile & Vitals",
                "UC-03: Explore Symptoms via Explorer",
                "UC-04: Conduct MedBot Interview",
                "UC-05: Capture & Submit Anatomical Photo",
                "UC-06: Query NurseBot for Nutrition FAQ",
                "UC-07: Track Ward Deficiency Trends",
                "UC-08: Complete Daily CarePlan Tasks",
                "UC-09: Export Calendar Feed (.ics)",
                "UC-10: Print Clinical Summary Report"
            ], "#f1f5f9"),
            (700, 200, 1000, 1050, "MEDNOURISH System Boundary", [
                "(UC-01) Enforce Mandatory Non-Diagnostic Gate",
                "(UC-02) Calculate Body Mass Index (BMI)",
                "(UC-03) Inverted Index Symptom Matching",
                "(UC-04) Entropy-Guided Dynamic Questioning",
                "(UC-05) Laplacian & Luminance Image Audit",
                "(UC-06) MobileNetV2 Multi-Region Vision Inference",
                "(UC-07) MedlinePlus Curated Retrieval",
                "(UC-08) Emergency Red-Flag Keyword Interception",
                "(UC-09) Recency-Weighted Risk Aggregation",
                "(UC-10) Rule-Based Nutrition & Calorie Planner",
                "(UC-11) RFC 5545 iCalendar Byte Serialization",
                "(UC-12) Dual SQLite / MySQL Dialect Persistence"
            ], "#ffffff"),
            (1950, 300, 350, 800, "Secondary Actor: Clinician / Auditor", [
                "UC-11: Review Printed Clinical Summary",
                "UC-12: Inspect Model Cards & Artifacts",
                "UC-13: Validate Non-Diagnostic Claims",
                "UC-14: Audit Benchmark Performance"
            ], "#f1f5f9")
        ],
        "arrows": [
            ("h", 450, 450, 700, "Initiates"),
            ("h", 450, 700, 700, "Submits"),
            ("h", 450, 950, 700, "Exports"),
            ("h", 1700, 450, 1950, "Provides Evidence"),
            ("h", 1700, 850, 1950, "Presents Summary")
        ],
        "mmd": """graph LR
    User((Patient / User))
    Auditor((Auditor / Clinician))
    subgraph MedNourish["MEDNOURISH System Boundary"]
        UC1["Acknowledge Consent & Disclaimers"]
        UC2["Match Clinical Symptoms"]
        UC3["Guided MedBot Interview"]
        UC4["Upload Anatomical Photo"]
        UC5["View Ward Trends"]
        UC6["Export CarePlan iCal"]
        UC7["Review Clinical Summary"]
    end
    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6
    Auditor --> UC7
"""
    },
    {
        "id": "fig_5_6_er_database_schema",
        "fig_no": "Figure 5.6",
        "title": "Entity-Relationship (ER) Database Schema",
        "subtitle": "Relational Entity Model showing 5 core tables, primary keys, foreign keys, and cardinalities",
        "boxes": [
            (100, 200, 420, 500, "user_profiles (1)", [
                "PK id: INTEGER",
                "user_id: VARCHAR(128) [UNIQUE]",
                "age: INTEGER",
                "gender: VARCHAR(32)",
                "diet_type: VARCHAR(64)",
                "activity_level: VARCHAR(64)",
                "height_cm: FLOAT",
                "weight_kg: FLOAT",
                "created_at: DATETIME",
                "updated_at: DATETIME"
            ], "#ffffff"),
            (680, 200, 420, 500, "user_consent_logs (N)", [
                "PK id: INTEGER",
                "FK user_id: VARCHAR(128)",
                "consent_type: VARCHAR(64)",
                "agreed: BOOLEAN",
                "version: VARCHAR(32)",
                "ip_address_hash: VARCHAR(128)",
                "timestamp: DATETIME"
            ], "#ffffff"),
            (1260, 200, 440, 500, "saved_summaries (N)", [
                "PK id: INTEGER",
                "FK user_id: VARCHAR(128)",
                "session_type: VARCHAR(32)",
                "summary_data: JSON / TEXT",
                "risk_band: VARCHAR(32)",
                "score: FLOAT",
                "created_at: DATETIME"
            ], "#ffffff"),
            (400, 800, 450, 480, "care_plan_items (N)", [
                "PK id: INTEGER",
                "FK user_id: VARCHAR(128)",
                "plan_date: DATE",
                "task_category: VARCHAR(64)",
                "title: VARCHAR(255)",
                "description: VARCHAR(500)",
                "completed: BOOLEAN",
                "created_at: DATETIME"
            ], "#ffffff"),
            (1100, 800, 450, 480, "medscan_sessions (N)", [
                "PK id: INTEGER",
                "FK user_id: VARCHAR(128)",
                "anatomical_region: VARCHAR(32)",
                "blur_score: FLOAT",
                "luminance_score: FLOAT",
                "predicted_class: VARCHAR(64)",
                "confidence: FLOAT",
                "created_at: DATETIME"
            ], "#ffffff")
        ],
        "arrows": [
            ("h", 520, 400, 680, "1 to N"),
            ("h", 1100, 400, 1260, "1 to N"),
            ("v", 310, 700, 800, "1 to N"),
            ("h", 520, 650, 1100, "1 to N")
        ],
        "mmd": """erDiagram
    user_profiles ||--o{ user_consent_logs : "records"
    user_profiles ||--o{ saved_summaries : "generates"
    user_profiles ||--o{ care_plan_items : "schedules"
    user_profiles ||--o{ medscan_sessions : "captures"

    user_profiles {
        int id PK
        string user_id UK
        int age
        string gender
        string diet_type
        float height_cm
        float weight_kg
    }
    user_consent_logs {
        int id PK
        string user_id FK
        boolean agreed
        string version
        datetime timestamp
    }
    care_plan_items {
        int id PK
        string user_id FK
        date plan_date
        string title
        boolean completed
    }
    saved_summaries {
        int id PK
        string user_id FK
        string session_type
        string risk_band
        float score
    }
    medscan_sessions {
        int id PK
        string user_id FK
        string anatomical_region
        float blur_score
        string predicted_class
    }
"""
    },
    {
        "id": "fig_5_7_user_workflow_flowchart",
        "fig_no": "Figure 5.7",
        "title": "End-to-End User Clinical Intake Workflow",
        "subtitle": "Step-by-step logic flow from portal access to report printing and calendar synchronization",
        "boxes": [
            (100, 200, 320, 180, "1. Portal Entry", ["Display Disclaimer Banner", "Check Stored Consent"], "#ffffff"),
            (520, 200, 320, 180, "2. Consent Verification", ["Agreed to V2.0 terms?", "If No -> Route to Gate"], "#ffffff"),
            (940, 200, 320, 180, "3. Intake Modality Choice", ["Option A: Symptom Explorer", "Option B: MedBot Voice/Chat", "Option C: MedScan Camera"], "#ffffff"),
            (1360, 200, 320, 180, "4. Assessment Execution", ["Compute Shrinkage Score", "Or Execute TFLite Model", "Check Emergency Red Flags"], "#ffffff"),
            (1780, 200, 320, 180, "5. Emergency Triage Check", ["Severe distress detected?", "If Yes -> Emergency Hotline", "If No -> Proceed to Plan"], "#ffffff"),
            (300, 600, 450, 300, "6. Insufficient Info Gate", ["Symptom count < 2?", "Or Image Quality Rejected?", "Display Advisory Guidance", "Prompt for Clarification"], "#ffffff"),
            (950, 600, 450, 300, "7. Ward & CarePlan Synthesis", ["Calculate Risk Band (60/30)", "Assemble Daily Meals & Water", "Schedule Nutrition Tasks", "Persist to SQL Database"], "#ffffff"),
            (1600, 600, 450, 300, "8. Export & Follow-up", ["Download RFC 5545 (.ics)", "Print Clinical Summary PDF", "Consult Healthcare Provider", "Educational Follow-up"], "#ffffff")
        ],
        "arrows": [
            ("h", 420, 290, 520, "Enter"),
            ("h", 840, 290, 940, "Consent Logged"),
            ("h", 1260, 290, 1360, "Selected"),
            ("h", 1680, 290, 1780, "Calculated"),
            ("v", 1940, 380, 600, "Emergency Safe"),
            ("h", 1600, 750, 1400, "Approved"),
            ("h", 950, 750, 750, "Sparse Input")
        ],
        "mmd": """flowchart TD
    Start([Portal Access]) --> Banner[View Educational Disclaimer]
    Banner --> Consent{Signed Consent?}
    Consent -- No --> SignConsent[Display Consent Gate Modal]
    SignConsent --> Consent
    Consent -- Yes --> ChooseMode{Select Assessment Modality}
    ChooseMode -->|Explorer| Sym[Enter Symptoms]
    ChooseMode -->|MedBot| Bot[Guided Dialogue]
    ChooseMode -->|MedScan| Scan[Upload Anatomical Image]
    Sym --> CheckInf{Symptom Count >= 2?}
    Bot --> CheckInf
    Scan --> Quality{Laplacian >= 50 & Lum in [40,225]?}
    Quality -- Fail --> Rej[Reject: Suggest Lighting/Focus]
    Quality -- Pass --> Inf[Run MobileNetV2 Inference]
    CheckInf -- Fail --> Insuff[Display Insufficient Info Warning]
    CheckInf -- Yes --> Score[Calculate Noisy-OR Risk Score]
    Inf --> Merge[Aggregate in Virtual Ward]
    Score --> Merge
    Merge --> Care[Generate CarePlan & iCalendar Feed]
    Care --> Print[Export Summary / Consult Doctor]
"""
    },
    {
        "id": "fig_5_8_ml_pipeline",
        "fig_no": "Figure 5.8",
        "title": "Machine Learning Training, Quantization, and Inference Pipeline",
        "subtitle": "Data preparation, cross-validation, hyperparameter tuning, model quantization, and edge parity check",
        "boxes": [
            (80, 200, 380, 400, "Stage 1: Ingestion & Curation", [
                "4,000 Tabular Clinical Records",
                "364,292 Raw Images in Corpus",
                "Support Gate >= 40 Filter",
                "Retain 10,980 Curated Images",
                "Purge Direct Target Leakage"
            ], "#f8fafc"),
            (540, 200, 380, 400, "Stage 2: Model Training", [
                "Tabular: XGBoost / LightGBM",
                "Vision: MobileNetV2 (160x160)",
                "Pretrained ImageNet Weights",
                "Categorical Cross-Entropy Loss",
                "Adam Optimizer (lr=1e-4)",
                "Early Stopping (patience=5)"
            ], "#f8fafc"),
            (1000, 200, 380, 400, "Stage 3: Quantization & Compression", [
                "Keras (.keras) -> TFLite",
                "Dynamic Range Quantization (DRQ)",
                "Weight INT8 Quantization",
                "Size Reduction: ~9.1MB -> ~2.4MB",
                "Storage Savings: ~73.1%"
            ], "#f8fafc"),
            (1460, 200, 380, 400, "Stage 4: Parity & Shortcut Audit", [
                "Prediction Agreement Check (>98.5%)",
                "Max Absolute Difference (<0.05)",
                "Grad-CAM Attribution Audit",
                "Shortcut Penalty Factor (0.55)",
                "Model Cards Generation"
            ], "#f8fafc"),
            (1920, 200, 400, 400, "Stage 5: Edge Deployment", [
                "TFLite Runtime Interpreter",
                "Zero GPU Edge Execution",
                "FastAPI Microservice Integration",
                "Sub-50ms Inference Latency",
                "Clean Error Handling Fallbacks"
            ], "#f8fafc"),
            (200, 750, 2000, 450, "Pipeline Governance & Verification Controls", [
                "Dual Feature Profiles: Tabular models evaluated under 'with_labs' (baseline), 'no_labs' (pragmatic), and 'symptoms_only' (telehealth)",
                "Parity Benchmark: Verified that DRQ INT8 models preserve >98.6% top-1 classification agreement against full-precision Float32 baselines",
                "Explainability Assurance: Top convolutional feature maps audited via Grad-CAM to confirm biological feature localization over background",
                "Zero Cloud Transmission: Inference performed locally on host CPU via TFLite runtime, preserving absolute user data confidentiality"
            ], "#ffffff")
        ],
        "arrows": [
            ("h", 460, 400, 540, "Curated"),
            ("h", 920, 400, 1000, "Trained"),
            ("h", 1380, 400, 1460, "Quantized"),
            ("h", 1840, 400, 1920, "Validated")
        ],
        "mmd": """flowchart LR
    Data[Dataset Ingestion] --> Clean[Quality Gate & Leakage Purge]
    Clean --> Train[Train: XGBoost / MobileNetV2]
    Train --> Quant[Dynamic Range Quantization DRQ]
    Quant --> Audit[Parity Check & Grad-CAM Audit]
    Audit --> Deploy[TFLite CPU Edge Deployment]
"""
    },
    {
        "id": "fig_5_9_safety_privacy_layers",
        "fig_no": "Figure 5.9",
        "title": "Multi-Layered Safety, Ethics, and Privacy Architecture",
        "subtitle": "Defensive defense-in-depth framework preventing diagnostic overreach and protecting sensitive user data",
        "boxes": [
            (80, 250, 400, 900, "Layer 1: Legal & Ethical Disclaimers", [
                "Persistent Non-Diagnostic Header Banner",
                "Explicit V2.0 Consent Logging",
                "Educational Prototype Framing",
                "Mandatory Clinician Consultation Prompt",
                "Zero Prescriptive Claims Guarantee"
            ], "#f8fafc"),
            (540, 250, 400, 900, "Layer 2: Emergency Triage Interceptor", [
                "Real-time Keyword Detection",
                "Chest Pain / Severe Dyspnea Triggers",
                "Immediate Red-Flag Modal Interception",
                "Surfaces 911 / 112 Emergency Hotlines",
                "Suppresses Routine Nutrition Guidance"
            ], "#f8fafc"),
            (1000, 250, 400, 900, "Layer 3: Data Privacy & Sanitization", [
                "Client-Side EXIF Metadata Stripping",
                "Zero GPS Coordinates Retained",
                "Hashed IP Address Consent Auditing",
                "Local Edge Model Inference (No Cloud AI)",
                "Zero PII in Machine Learning Tensors"
            ], "#f8fafc"),
            (1460, 250, 400, 900, "Layer 4: Automated CI/CD Safety Scanner", [
                "76 Project Files Scanned on Commit",
                "AST & Regex Audit for Banned Terms",
                "Enforces 'Deficiency Risk' Terminology",
                "Prohibits 'Treats', 'Diagnoses', 'Cures'",
                "Continuous Integration Pipeline Gate"
            ], "#f8fafc"),
            (1920, 250, 400, 900, "Layer 5: Clinical Grounding", [
                "Deterministic Curated Tables (CSVs)",
                "NIH MedlinePlus Verified Guidance",
                "Zero Generative LLM Hallucinations",
                "Bounded Probabilities [0.0, 1.0]",
                "Transparent Explainable Scoring"
            ], "#f8fafc")
        ],
        "arrows": [
            ("h", 480, 600, 540, "Filters"),
            ("h", 940, 600, 1000, "Guards"),
            ("h", 1400, 600, 1460, "Audits"),
            ("h", 1860, 600, 1920, "Grounds")
        ],
        "mmd": """graph TD
    L1["Layer 1: Legal & Disclaimer Banner"] --> L2["Layer 2: Emergency Triage Interceptor"]
    L2 --> L3["Layer 3: Data Privacy & EXIF Stripping"]
    L3 --> L4["Layer 4: Automated CI/CD Safety Scanner"]
    L4 --> L5["Layer 5: Deterministic Clinical Grounding"]
"""
    },
    {
        "id": "fig_6_1_curated_knowledge_pipeline",
        "fig_no": "Figure 6.1",
        "title": "Curated Clinical Knowledge Ingestion & Validation Pipeline",
        "subtitle": "Ingestion of food items, nutrient guidance, clinical synonyms, and anatomical class definitions",
        "boxes": [
            (100, 200, 480, 500, "Curated Knowledge Sources", [
                "knowledge/curated/food_items.csv",
                "knowledge/curated/nutrient_guidance.csv",
                "knowledge/curated/synonyms.yaml",
                "ml/class_maps/*.json (7 Anatomical Regions)"
            ], "#f8fafc"),
            (700, 200, 500, 500, "Knowledge Validator & Inverted Indexer", [
                "Schema & Type Consistency Validator",
                "Synonym Expansion Normalizer",
                "Inverted Index Table Construction",
                "IDF Weight Precomputation",
                "Zero Hallucination Grounding Assurance"
            ], "#ffffff"),
            (1320, 200, 480, 500, "Runtime Memory Caches", [
                "In-Memory Symptom Dictionary",
                "Canonical Synonym Hash Map",
                "Nutrient RDA Recommendation Cache",
                "TFLite Class Label Lookup Arrays"
            ], "#f8fafc"),
            (1920, 200, 380, 500, "Application Consumers", [
                "Module 1: Reference Explorer",
                "Module 2: MedBot Guided Interview",
                "Module 4: NurseBot Health Assistant",
                "Module 6: CarePlan Meal Planner"
            ], "#f1f5f9")
        ],
        "arrows": [
            ("h", 580, 450, 700, "Parse CSV/YAML"),
            ("h", 1200, 450, 1320, "Build Index"),
            ("h", 1800, 450, 1920, "Fast Retrieval")
        ],
        "mmd": """flowchart LR
    CSV[Curated CSVs & YAML] --> Val[Validation & Schema Check]
    Val --> Index[Inverted Index Builder]
    Index --> Cache[In-Memory Hash Maps]
    Cache --> App[FastAPI Application Subsystems]
"""
    },
    {
        "id": "fig_6_2_reference_matcher_flowchart",
        "fig_no": "Figure 6.2",
        "title": "Reference Symptom Matcher Execution Flow",
        "subtitle": "Synonym resolution, inverted index lookup, IDF weighting, shrinkage scaling, and risk classification",
        "boxes": [
            (100, 300, 380, 350, "1. Input Symptoms", ["User selects canonical symptoms", "Or enters free-text terms", "e.g., ['fatigue', 'pale skin']"], "#ffffff"),
            (550, 300, 380, 350, "2. Synonym Resolution", ["Match against synonyms.yaml", "Expand colloquial variants", "Resolve to canonical IDs"], "#ffffff"),
            (1000, 300, 380, 350, "3. Inverted Index Lookup", ["Retrieve matched conditions", "Count matches (m)", "Check if m < 2 (Insufficient Info)"], "#ffffff"),
            (1450, 300, 380, 350, "4. IDF Shrinkage Weighting", ["Weight w_i = IDF(symptom_i)", "Shrinkage k = min(1.0, 0.4 + 0.2*m)", "Score = k * Sum(w_i) / MaxPossible"], "#ffffff"),
            (1900, 300, 400, 350, "5. Risk Band Classification", ["Score >= 60% -> High Risk (Red)", "30% <= Score < 60% -> Moderate (Yellow)", "Score < 30% -> Low Risk (Green)"], "#ffffff")
        ],
        "arrows": [
            ("h", 480, 475, 550, "Tokens"),
            ("h", 930, 475, 1000, "Canonical"),
            ("h", 1380, 475, 1450, "Candidate Set"),
            ("h", 1830, 475, 1900, "Raw Score")
        ],
        "mmd": """flowchart LR
    Input[Input Symptoms] --> Syn[Synonym Resolution]
    Syn --> Index[Inverted Index Lookup]
    Index --> Shrink[IDF Shrinkage Scaling]
    Shrink --> Bands[Risk Band Classification]
"""
    },
    {
        "id": "fig_6_3_scoring_formulas_flowchart",
        "fig_no": "Figure 6.3",
        "title": "Mathematical Scoring & Probabilistic Aggregation Engine",
        "subtitle": "Mathematical formula execution: IDF weighting, shrinkage scaling, and Noisy-OR combination",
        "boxes": [
            (120, 250, 650, 800, "1. IDF Weighting & Shrinkage", [
                "Symptom Inverse Document Frequency:",
                "IDF(s_i) = ln( (N_total + 1) / (DF(s_i) + 1) ) + 1",
                "",
                "Shrinkage Scaling Factor:",
                "k(m) = min(1.0, 0.4 + 0.2 * m)",
                "where m is the count of matching symptoms",
                "",
                "Reference Match Percentage:",
                "Match% = k(m) * [ Sum(w_i) / Sum(W_total) ] * 100"
            ], "#f8fafc"),
            (900, 250, 650, 800, "2. Noisy-OR Probabilistic Model", [
                "Condition Deficiency Probability:",
                "P(D | S) = 1 - Prod_{i in S} (1 - P(D | s_i))",
                "",
                "Leakage Probability Grounding:",
                "P_leak = 0.02 (Baseline spontaneous risk)",
                "",
                "Bounded Output Domain:",
                "P(D | S) in [0.00, 1.00] strictly",
                "Monotonically increasing with symptom evidence"
            ], "#f8fafc"),
            (1680, 250, 600, 800, "3. Decision Boundaries & Risk Bands", [
                "High Risk Band (Red Alert):",
                "Score >= 60.0% OR P(D | S) >= 0.60",
                "",
                "Moderate Risk Band (Yellow Warning):",
                "30.0% <= Score < 60.0%",
                "",
                "Low Risk Band (Green Baseline):",
                "Score < 30.0%",
                "",
                "Insufficient Information Warning:",
                "Triggered when m < 2 (Prompt further assessment)"
            ], "#f8fafc")
        ],
        "arrows": [
            ("h", 770, 650, 900, "Probabilities"),
            ("h", 1550, 650, 1680, "Classify")
        ],
        "mmd": """flowchart LR
    IDF["IDF Weighting & Shrinkage k(m)"] --> NoisyOR["Noisy-OR Probabilistic Synthesis"]
    NoisyOR --> Bands["Tri-Band Risk Thresholds (60% / 30%)"]
"""
    },
    {
        "id": "fig_6_4_medbot_workflow",
        "fig_no": "Figure 6.4",
        "title": "MedBot Dynamic Conversational Interview Workflow",
        "subtitle": "Interactive interview loop utilizing entropy-based symptom prioritization and speech recognition",
        "boxes": [
            (80, 300, 380, 350, "1. Session Initialization", ["User selects 'Start Guided Interview'", "Create medbot_session in memory", "Load candidate deficiency conditions"], "#ffffff"),
            (530, 300, 380, 350, "2. Entropy-Based Questioning", ["Select symptom with highest entropy", "Maximize information gain", "Formulate targeted yes/no query"], "#ffffff"),
            (980, 300, 380, 350, "3. Multi-Modal User Input", ["Voice response (Web Speech API)", "Or interactive symptom chips", "Or standard keyboard reply"], "#ffffff"),
            (1430, 300, 380, 350, "4. State & Hypothesis Update", ["Update confirmed symptoms", "Update eliminated symptoms", "Recalculate condition probabilities"], "#ffffff"),
            (1880, 300, 420, 350, "5. Termination & Summary", ["Terminate when confidence > 0.85", "Or max turns (8) reached", "Save summary to database", "Generate nutritional care recommendations"], "#ffffff")
        ],
        "arrows": [
            ("h", 460, 475, 530, "Init"),
            ("h", 910, 475, 980, "Query"),
            ("h", 1360, 475, 1430, "Answer"),
            ("h", 1810, 475, 1880, "Threshold Met")
        ],
        "mmd": """flowchart TD
    Init[Start Session] --> Prioritize[Calculate Maximum Entropy Symptom]
    Prioritize --> Query[Surface Question / Speech Prompt]
    Query --> Input[User Responds: Voice or Chip]
    Input --> Update[Update Hypotheses & Evidence]
    Update --> Done{Confidence >= 0.85 or Turns >= 8?}
    Done -- No --> Prioritize
    Done -- Yes --> Summary[Save Session & Export Summary]
"""
    },
    {
        "id": "fig_6_5_mobilenetv2_multitask_architecture",
        "fig_no": "Figure 6.5",
        "title": "MobileNetV2 Regional Vision Architecture",
        "subtitle": "Network layer structure: inverted residuals, depthwise separable convolutions, pooling, and classification head",
        "boxes": [
            (80, 250, 380, 400, "Input Layer", ["Input Image Tensor", "Resolution: 160 x 160 x 3", "Normalization: [-1, 1]", "Channel Order: RGB"], "#f8fafc"),
            (520, 250, 420, 400, "MobileNetV2 Backbone", ["Pretrained ImageNet Weights", "Inverted Residual Blocks", "Depthwise Separable Convolutions", "Linear Bottleneck Projections", "Expansion Factor t = 6"], "#ffffff"),
            (1000, 250, 400, 400, "Classification Head", ["GlobalAveragePooling2D", "Dropout Layer (rate = 0.2)", "Dense Linear Layer", "Softmax Activation Function", "Output Class Probabilities"], "#ffffff"),
            (1460, 250, 420, 400, "Dynamic Range Quantizer", ["TFLite DRQ Converter", "Weight Quantization: INT8", "Activation Quantization: Float32", "Model Footprint: ~2.35 MB", "73% Compression Ratio"], "#f8fafc"),
            (1940, 250, 380, 400, "Shortcut Calibrator", ["Inspect Anatomical Metadata", "Detect Out-of-Domain Shortcut", "Apply Heuristic Penalty (0.55)", "Output Calibrated Risk Confidence"], "#ffffff"),
            (200, 750, 2000, 450, "Architecture Performance Specifications across 7 Regional Targets", [
                "Lips (2 Classes): Test Acc 92.11% | Macro-F1 0.918 | Size 2.34 MB | Shortcut Risk: Low",
                "Nails (3 Classes): Test Acc 86.62% | Macro-F1 0.854 | Size 2.35 MB | Shortcut Risk: Medium",
                "Hair (2 Classes): Test Acc 84.31% | Macro-F1 0.839 | Size 2.34 MB | Shortcut Risk: Medium",
                "Eyes (3 Classes): Test Acc 79.44% | Macro-F1 0.786 | Size 2.35 MB | Shortcut Risk: Medium",
                "Combined (10 Classes): Test Acc 77.10% | Macro-F1 0.762 | Size 2.38 MB | Shortcut Risk: Medium-High",
                "Tongue (3 Classes): Test Acc 71.36% | Macro-F1 0.702 | Size 2.35 MB | Shortcut Risk: Medium",
                "Skin (2 Classes): Test Acc 66.34% | Macro-F1 0.648 | Size 2.34 MB | Shortcut Risk: High (Background shortcuts penalised)"
            ], "#f8fafc")
        ],
        "arrows": [
            ("h", 460, 450, 520, "160x160x3"),
            ("h", 940, 450, 1000, "Feature Maps"),
            ("h", 1400, 450, 1460, "Keras Model"),
            ("h", 1880, 450, 1940, "TFLite INT8")
        ],
        "mmd": """flowchart LR
    Input[Input Tensor 160x160x3] --> Backbone[MobileNetV2 Inverted Residuals]
    Backbone --> Head[GlobalAvgPool + Dropout + Dense Softmax]
    Head --> Quant[TFLite Dynamic Range Quantization INT8]
    Quant --> Penalty[Shortcut Penalty Calibrator]
"""
    },
    {
        "id": "fig_6_6_vision_training_export_flow",
        "fig_no": "Figure 6.6",
        "title": "Vision Model Training, Validation, and TFLite Export Flow",
        "subtitle": "Support gate thresholding, stratified splitting, augmentation, fine-tuning, and DRQ edge compilation",
        "boxes": [
            (80, 300, 380, 350, "1. Quality Gate Filter", ["Raw Corpus: 364,292 images", "Apply Support Gate >= 40", "Retain 10,980 usable images", "Exclude under-supported classes"], "#ffffff"),
            (530, 300, 380, 350, "2. Data Augmentation", ["Random Horizontal Flip", "Random Rotation (+- 15 deg)", "Color Jitter & Brightness (10%)", "Stratified Train/Val/Test Split"], "#ffffff"),
            (980, 300, 380, 350, "3. Fine-Tuning Execution", ["ImageNet Transfer Learning", "Freeze Backbone (Epochs 1-10)", "Unfreeze Top 30 Layers (11-25)", "ReduceLROnPlateau Scheduler"], "#ffffff"),
            (1430, 300, 380, 350, "4. TFLite INT8 DRQ Export", ["tf.lite.TFLiteConverter", "Optimize for DEFAULT", "Quantize weights to INT8", "Export model_name.tflite"], "#ffffff"),
            (1880, 300, 420, 350, "5. Parity & Card Packaging", ["Verify top-1 agreement >98.5%", "Evaluate test latency on CPU", "Generate model_card.json", "Commit weights & card to repo"], "#ffffff")
        ],
        "arrows": [
            ("h", 460, 475, 530, "Cleaned"),
            ("h", 910, 475, 980, "Batches"),
            ("h", 1360, 475, 1430, "Weights"),
            ("h", 1810, 475, 1880, "Quantized")
        ],
        "mmd": """flowchart LR
    Gate[Support Gate >= 40 Filter] --> Aug[Stratified Split & Augmentation]
    Aug --> Train[Two-Stage Fine-Tuning]
    Train --> Export[TFLite DRQ Converter]
    Export --> Card[Parity Validation & Model Card Export]
"""
    },
    {
        "id": "fig_6_7_medscan_sequence_diagram",
        "fig_no": "Figure 6.7",
        "title": "MedScan Multi-Region Vision Inference Sequence Diagram",
        "subtitle": "UML sequence interaction between User UI, ImageGate Validator, TFLite Microservice, and Database",
        "boxes": [
            (100, 200, 300, 80, "User Interface", [], "#f8fafc"),
            (600, 200, 350, 80, "ImageQualityGate", [], "#f8fafc"),
            (1150, 200, 350, 80, "TFLiteVisionEngine", [], "#f8fafc"),
            (1700, 200, 350, 80, "SQLAlchemy / MySQL", [], "#f8fafc")
        ],
        "arrows": [
            ("v", 250, 280, 1200, "Lifeline"),
            ("v", 775, 280, 1200, "Lifeline"),
            ("v", 1325, 280, 1200, "Lifeline"),
            ("v", 1875, 280, 1200, "Lifeline"),
            ("h", 250, 400, 775, "POST /api/v1/medscan/analyze (image bytes, region)"),
            ("h", 775, 520, 250, "If Blur < 50 or Lum not in [40,225] -> 422 Rejected"),
            ("h", 775, 640, 1325, "Quality Passed -> Invoke Model(tensor 160x160)"),
            ("h", 1325, 780, 775, "Return Probabilities + Apply Shortcut Penalty"),
            ("h", 775, 900, 1875, "INSERT INTO medscan_sessions (scores, class)"),
            ("h", 1875, 980, 775, "Record Confirmed"),
            ("h", 775, 1100, 250, "Return 200 OK (Risk Class, Confidence, Educational Tip)")
        ],
        "mmd": """sequenceDiagram
    autonumber
    actor User as Patient User
    participant UI as React Frontend
    participant Gate as ImageQualityGate
    participant TFLite as TFLite Vision Engine
    participant DB as MySQL / SQLite

    User->>UI: Uploads anatomical photo
    UI->>Gate: POST /api/v1/medscan/analyze
    Note over Gate: Evaluate Laplacian var & mean luminance
    alt Blurry or Poorly Lit
        Gate-->>UI: 422 Rejected (Actionable Lighting / Blur Tip)
    else Quality Approved
        Gate->>TFLite: Run inference on 160x160 tensor
        TFLite-->>Gate: Class probabilities & shortcut penalty
        Gate->>DB: INSERT INTO medscan_sessions
        DB-->>Gate: 201 Created
        Gate-->>UI: 200 OK (Classification, Confidence, Advisory)
    end
"""
    },
    {
        "id": "fig_6_8_nursebot_intent_router",
        "fig_no": "Figure 6.8",
        "title": "NurseBot Intent Routing & Health FAQ Dispatcher",
        "subtitle": "Natural language query routing: emergency detection, local clinical knowledge, and MedlinePlus fallback",
        "boxes": [
            (80, 300, 380, 350, "1. User Health Query", ["User enters question in chat", "e.g., 'What foods have iron?'", "Or 'Severe chest pain crushing'"], "#ffffff"),
            (530, 300, 380, 350, "2. Emergency Classifier", ["Check acute clinical red flags", "Chest pain, breathing crisis, collapse", "If Flagged -> Trigger Red Modal"], "#ffffff"),
            (980, 300, 380, 350, "3. Curated FAQ Matcher", ["Query curated CSV / YAML tables", "Match nutritional RDA guidance", "Check food composition database"], "#ffffff"),
            (1430, 300, 380, 350, "4. MedlinePlus Resolver", ["If not in local curated cache", "Query NIH MedlinePlus REST API", "Extract peer-reviewed summary"], "#ffffff"),
            (1880, 300, 420, 350, "5. Response Serializer", ["Append Non-Diagnostic Disclaimer", "Format bulleted nutrition guidance", "Present source citation link", "Prompt clinician consultation"], "#ffffff")
        ],
        "arrows": [
            ("h", 460, 475, 530, "Query"),
            ("h", 910, 475, 980, "Safe"),
            ("h", 1360, 475, 1430, "Fallback"),
            ("h", 1810, 475, 1880, "Grounded Content")
        ],
        "mmd": """flowchart TD
    Query[User Health Query] --> Check{Emergency Keywords?}
    Check -- Yes --> Triage[Trigger Emergency Modal: Dial 911 / 112]
    Check -- No --> MatchLocal{Found in Curated Knowledge?}
    MatchLocal -- Yes --> ReturnLocal[Return Curated Nutritional Guidance]
    MatchLocal -- No --> QueryNIH[Query NIH MedlinePlus API]
    QueryNIH --> ReturnNIH[Extract Snippet & Add Citation]
    ReturnLocal --> Disclaimer[Attach Educational Disclaimer]
    ReturnNIH --> Disclaimer
"""
    },
    {
        "id": "fig_6_9_recency_weighted_aggregation",
        "fig_no": "Figure 6.9",
        "title": "Recency-Weighted Temporal Risk Aggregation Engine",
        "subtitle": "Time-decay weighting across historical intake logs: Explorer, MedBot, and MedScan",
        "boxes": [
            (80, 250, 450, 400, "Historical Assessment Logs", [
                "saved_summaries (Symptom Explorer)",
                "medbot_sessions (Conversational)",
                "medscan_sessions (Vision Scans)",
                "Timestamped over 30-day window"
            ], "#f8fafc"),
            (600, 250, 520, 400, "Exponential Time-Decay Model", [
                "Weight formula: w(t) = exp( - lambda * delta_t )",
                "Half-life parameter: t_half = 7.0 days",
                "lambda = ln(2) / 7.0 ~= 0.099 days^-1",
                "Recent observations contribute higher weight",
                "Aged observations gracefully attenuate"
            ], "#ffffff"),
            (1200, 250, 520, 400, "Cross-Modality Blending Engine", [
                "Blended Risk Score:",
                "S_total = [ Sum(w_i * S_i) ] / [ Sum(w_i) ]",
                "Confidence floor scaling applied",
                "Outlier attenuation for conflicting scans"
            ], "#ffffff"),
            (1800, 250, 520, 400, "Virtual Ward Visualization", [
                "Overall Deficiency Status (Low/Mod/High)",
                "6 Temporal Line / Bar Charts",
                "Nutritional Adherence Progress Ring",
                "Printable Health Summary Document"
            ], "#f8fafc"),
            (200, 750, 2000, 450, "Temporal Decay Values across Observation Intervals", [
                "Observation Age: Day 0 (Today) | Time Decay Weight: 1.000 | Clinical Relevance: 100%",
                "Observation Age: Day 3 | Time Decay Weight: 0.743 | Clinical Relevance: 74.3%",
                "Observation Age: Day 7 (1 Half-life) | Time Decay Weight: 0.500 | Clinical Relevance: 50.0%",
                "Observation Age: Day 14 (2 Half-lives) | Time Decay Weight: 0.250 | Clinical Relevance: 25.0%",
                "Observation Age: Day 30 | Time Decay Weight: 0.052 | Clinical Relevance: 5.2% (Historical baseline only)"
            ], "#f8fafc")
        ],
        "arrows": [
            ("h", 530, 450, 600, "Logs"),
            ("h", 1120, 450, 1200, "Decay Weights"),
            ("h", 1720, 450, 1800, "Aggregate Score")
        ],
        "mmd": """flowchart LR
    Logs[Historical Assessment Logs] --> Decay[Exponential Decay: w = exp -lambda*t]
    Decay --> Blend[Cross-Modality Blending Engine]
    Blend --> Ward[Virtual Ward 6-Chart Temporal Visualizer]
"""
    },
    {
        "id": "fig_6_10_careplan_meals_and_sync",
        "fig_no": "Figure 6.10",
        "title": "CarePlan Meal Synthesizer & iCalendar Sync Pipeline",
        "subtitle": "Deterministic meal generation, dietary constraint satisfaction, and RFC 5545 iCalendar stream serialization",
        "boxes": [
            (80, 300, 380, 350, "1. Deficiency Profile", ["Identified Deficiency Risk", "e.g., Iron or Vitamin D", "Dietary Profile (Vegan/Omnivore)", "Caloric Budget Target"], "#ffffff"),
            (530, 300, 380, 350, "2. Meal Matrix Generator", ["Query curated food_items.csv", "Filter by diet_type constraint", "Select nutrient-dense foods", "Prevent string truncation (>135)"], "#ffffff"),
            (980, 300, 380, 350, "3. Daily Nutrition Checklist", ["Hydration goal (e.g. 2.5L)", "Morning / Evening dietary tasks", "Sunlight exposure suggestion", "Persist in care_plan_items"], "#ffffff"),
            (1430, 300, 380, 350, "4. RFC 5545 CalDAV Engine", ["Serialize to text/calendar", "Generate VCALENDAR container", "Generate VEVENT with UID & DTSTAMP", "Set recurrence to DAILY"], "#ffffff"),
            (1880, 300, 420, 350, "5. User Calendar Integration", ["Live HTTP subscription endpoint", "Compatible with Google Calendar", "Compatible with Apple Calendar", "Compatible with Microsoft Outlook"], "#ffffff")
        ],
        "arrows": [
            ("h", 460, 475, 530, "Constraints"),
            ("h", 910, 475, 980, "Meal Items"),
            ("h", 1360, 475, 1430, "Tasks"),
            ("h", 1810, 475, 1880, "ICS Byte Stream")
        ],
        "mmd": """flowchart LR
    Def[Deficiency Risk & Diet] --> Meals[Curated Meal Synthesizer]
    Meals --> Tasks[Daily CarePlan Checklist]
    Tasks --> ICS[RFC 5545 iCalendar Serializer]
    ICS --> Cal[External Calendar Subscription]
"""
    },
    {
        "id": "fig_7_1_testing_strategy",
        "fig_no": "Figure 7.1",
        "title": "Comprehensive Multi-Tiered Verification & Testing Pyramid",
        "subtitle": "Testing hierarchy: Unit Tests, Integration Tests, End-to-End System Tests, and Automated CI Safety Scanners",
        "boxes": [
            (100, 200, 480, 500, "Tier 1: Unit Testing (Pytest)", [
                "Backend: 115 Tests in SQLite Mode",
                "Backend: 115 Tests in MySQL Mode",
                "ML Lab: 40 Tests (Parity & Leakage)",
                "Matcher & Inverted Index Verification",
                "Laplacian Blur & Luminance Boundary Checks",
                "Scoring Bounds & Shrinkage Clamping",
                "100% Pass Rate across 270 test runs"
            ], "#f8fafc"),
            (700, 200, 480, 500, "Tier 2: Integration Testing", [
                "FastAPI + DB Connection Lifecycle",
                "Bearer Token Authentication & Consent Gate",
                "MedScan -> ImageGate -> TFLite Pipeline",
                "NurseBot -> MedlinePlus REST Retrieval",
                "CarePlan DB Persistence & CalDAV Export",
                "Emergency Triage Keyword Interceptor"
            ], "#f8fafc"),
            (1300, 200, 480, 500, "Tier 3: End-to-End System Tests", [
                "18-Step Automated Smoke Test Script",
                "Full HTTP Request/Response Round-Trip",
                "Simulates Patient Intake Workflow",
                "Evaluates Blur & Luminance Edge Cases",
                "Validates Virtual Ward Risk Serialization",
                "18 / 18 Steps Passed Deterministically"
            ], "#f8fafc"),
            (1900, 200, 420, 500, "Tier 4: Automated CI Safety Scanners", [
                "76 Project Files Inspected",
                "AST Scanner for Banned Claims",
                "Enforces Educational Disclaimer",
                "Verifies Zero Diagnostic Overreach",
                "Blocks Commits Violating Safety Rules",
                "Passed 76 / 76 Files Audited"
            ], "#f8fafc"),
            (200, 750, 2000, 450, "Verification Metrics Summary across System Stack", [
                "Total Automated Test Assertions Executed: 364 Test Cases",
                "Total Test Failures: 0 Failures (100.0% Pass Rate across All Test Suites)",
                "Database Dialect Equivalence: Verified exact behavioral parity between SQLite (Local Dev) and MySQL (Production)",
                "ML Parity: Verified dynamic range quantized INT8 models yield >98.6% identical predictions against Float32 references",
                "Code Cleanliness: 0 secrets, 0 unhedged diagnostic claims, 0 external cloud generative dependencies"
            ], "#ffffff")
        ],
        "arrows": [
            ("h", 580, 450, 700, "Integrates"),
            ("h", 1180, 450, 1300, "Exercises"),
            ("h", 1780, 450, 1900, "Governs")
        ],
        "mmd": """flowchart TD
    subgraph Pyramid["Testing Strategy Pyramid"]
        T4["Tier 4: Automated CI/CD Safety Scanners (76 Files)"]
        T3["Tier 3: End-to-End System Smoke Tests (18 Steps)"]
        T2["Tier 2: Module Integration Tests (API + DB + TFLite)"]
        T1["Tier 1: Unit Tests (115 Backend + 40 ML Tests)"]
    end
    T1 --> T2
    T2 --> T3
    T3 --> T4
"""
    }
]

for d in diagrams:
    # 1. Save Mermaid .mmd
    mmd_path = os.path.join(src_dir, f"{d['id']}.mmd")
    with open(mmd_path, "w", encoding="utf-8") as f:
        f.write(d["mmd"].strip() + "\n")
        
    # 2. Render high-res PNG
    img, draw = create_diag_canvas(2400, 1400, d["fig_no"], d["title"], d["subtitle"])
    for b in d["boxes"]:
        draw_box(draw, b[0], b[1], b[2], b[3], b[4], b[5], fill=b[6])
    for a in d["arrows"]:
        if a[0] == "h":
            draw_arrow_h(draw, a[1], a[2], a[3], a[4])
        elif a[0] == "v":
            draw_arrow_v(draw, a[1], a[2], a[3], a[4])
            
    png_path = os.path.join(diag_dir, f"{d['id']}.png")
    img.save(png_path)

print(f"Successfully rendered all {len(diagrams)} architectural diagrams and saved Mermaid sources!")
