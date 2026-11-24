# Database Schema Specification (Table 6.2)

Total Relational Tables: **5**  
Supported Storage Engines: **SQLite 3** (Default local fallback) & **MySQL 8.0+** (Target relational engine)

| Table Name | Column Name | Data Type | Nullable | Primary Key | Foreign Key | Functional Description |
|:---|:---|:---|:---:|:---:|:---:|:---|
| **`user_profiles`** | `id` | VARCHAR(128) | NO | YES | - | Firebase Auth UID unique user identifier |
| | `age` | INTEGER | YES | NO | - | User age integer (1–120) for demo purposes |
| | `gender` | VARCHAR(32) | YES | NO | - | Self-reported gender string |
| | `height_cm` | FLOAT | YES | NO | - | User height in centimeters |
| | `weight_kg` | FLOAT | YES | NO | - | User weight in kilograms |
| | `blood_type` | VARCHAR(16) | YES | NO | - | Blood group (A+, A-, B+, B-, AB+, AB-, O+, O-, Unknown) |
| | `conditions_json` | TEXT | YES | NO | - | JSON serialized array of existing medical conditions |
| | `other_condition` | VARCHAR(128) | YES | NO | - | Free-text entry for other pre-existing condition |
| | `consent_timestamp` | DATETIME | YES | NO | - | Timestamp when user affirmed educational consent |
| | `created_at` | DATETIME | NO | NO | - | Record creation timestamp (UTC) |
| | `updated_at` | DATETIME | NO | NO | - | Record last updated timestamp (UTC) |
| **`user_consent_logs`** | `id` | INTEGER | NO | YES | - | Autoincrementing consent event identifier |
| | `user_id` | VARCHAR(128) | NO | NO | `user_profiles.id` | Target user foreign key |
| | `consent_type` | VARCHAR(64) | NO | NO | - | Consent category (e.g. `adult_prototype_consent`) |
| | `version` | VARCHAR(32) | NO | NO | - | Terms version consented to (e.g. `v1.0`) |
| | `timestamp` | DATETIME | NO | NO | - | Timestamp when consent was recorded |
| **`care_plan_items`** | `id` | VARCHAR(64) | NO | YES | - | Unique UUID task identifier |
| | `user_id` | VARCHAR(128) | NO | NO | `user_profiles.id` | Target user foreign key |
| | `title` | VARCHAR(255) | NO | NO | - | Task description (hydration, sleep, food, walk) |
| | `category` | VARCHAR(64) | NO | NO | - | Task category (`lifestyle`, `diet`, `hydration`, `exercise`) |
| | `time_of_day` | VARCHAR(32) | YES | NO | - | Target execution time (`morning`, `afternoon`, `evening`) |
| | `frequency` | VARCHAR(32) | NO | NO | - | Recurrence schedule (`daily`, `weekly`) |
| | `is_completed` | BOOLEAN | NO | NO | - | Task completion toggle flag |
| | `completed_at` | DATETIME | YES | NO | - | Timestamp of task completion |
| | `source_nutrient` | VARCHAR(128) | YES | NO | - | Nutrient deficiency that triggered auto-sync |
| | `created_at` | DATETIME | NO | NO | - | Task creation timestamp |
| **`saved_summaries`** | `id` | VARCHAR(64) | NO | YES | - | Unique UUID assessment summary identifier |
| | `user_id` | VARCHAR(128) | NO | NO | `user_profiles.id` | Target user foreign key |
| | `engine` | VARCHAR(32) | NO | NO | - | Assessment source engine (`medbot`, `medscan`, `explorer`) |
| | `top_deficiency` | VARCHAR(128) | NO | NO | - | Highest ranking canonical deficiency |
| | `score_percentage` | FLOAT | NO | NO | - | Reference match percentage (0.0 to 95.0) |
| | `risk_band` | VARCHAR(32) | NO | NO | - | Heuristic demo risk band (`High`, `Moderate`, `Low`) |
| | `symptoms_summary` | TEXT | YES | NO | - | Summary string of contributing symptom tags |
| | `details_json` | TEXT | YES | NO | - | JSON serialized contributing rows and explanations |
| | `created_at` | DATETIME | NO | NO | - | Assessment record creation timestamp |
| **`medscan_sessions`** | `id` | VARCHAR(64) | NO | YES | - | Unique UUID photographic scan session identifier |
| | `user_id` | VARCHAR(128) | NO | NO | `user_profiles.id` | Target user foreign key |
| | `region` | VARCHAR(32) | NO | NO | - | Anatomical area (`eyes`, `hair`, `lips`, `nails`, `skin`, `tongue`) |
| | `quality_metrics_json` | TEXT | NO | NO | - | JSON metrics of blur variance and mean luminance |
| | `candidates_json` | TEXT | NO | NO | - | JSON model predictions with shortcut risk penalty |
| | `checklist_json` | TEXT | NO | NO | - | JSON user responses to clinical follow-up checklist |
| | `blended_results_json` | TEXT | NO | NO | - | JSON blended ranking passed to reference matcher |
| | `created_at` | DATETIME | NO | NO | - | Session creation timestamp |
