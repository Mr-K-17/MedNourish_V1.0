# API Endpoints Specification (Table 6.1)

Total OpenAPI Endpoints Implemented: **48**

| ID | Method | Route Path | Router Tag | Functional Description |
|:---|:---:|:---|:---|:---|
| **EP-01** | `GET` | `/` | Root | Root informational endpoint with project disclaimer |
| **EP-02** | `GET` | `/v1/health` | Health | Multi-service health check reporting MySQL and MongoDB status |
| **EP-03** | `GET` | `/v1/profile` | Profile | Fetch current user profile and demographic information |
| **EP-04** | `POST` | `/v1/profile` | Profile | Create new user profile and log adult demographic details |
| **EP-05** | `PUT` | `/v1/profile` | Profile | Update existing user demographic and medical condition profile |
| **EP-06** | `DELETE` | `/v1/profile` | Profile | Cascade account deletion purging all user health summaries and tasks |
| **EP-07** | `GET` | `/v1/explorer/categories` | Explorer | Fetch all 6 anatomical body regions and distinct symptom tags |
| **EP-08** | `POST` | `/v1/explorer/match` | Explorer | Deterministic inverted-index reference lookup across 116 rows |
| **EP-09** | `GET` | `/v1/medbot/questions` | MedBot | Fetch guided questionnaire items for Simple and Standard assessment |
| **EP-10** | `POST` | `/v1/medbot/extract` | MedBot | NLP symptom keyword extractor matching free text against synonyms.yaml |
| **EP-11** | `POST` | `/v1/medbot/evaluate` | MedBot | Compute IDF shrinkage scores and demo risk bands for questionnaire tags |
| **EP-12** | `POST` | `/v1/medbot/save` | MedBot | Persist MedBot assessment results as a permanent user SavedSummary |
| **EP-13** | `POST` | `/v1/medscan/analyze` | MedScan | Quality audit (blur and luminance) and MobileNetV2 inference proposal |
| **EP-14** | `GET` | `/v1/medscan/checklist` | MedScan | Fetch regional clinical follow-up checklist questions |
| **EP-15** | `GET` | `/v1/medscan/sessions` | MedScan | List all saved photographic scan sessions for authenticated user |
| **EP-16** | `POST` | `/v1/medscan/sessions` | MedScan | Save completed MedScan checklist and vision analysis session |
| **EP-17** | `GET` | `/v1/medscan/sessions/{session_id}` | MedScan | Retrieve detailed single MedScan session with blended candidates |
| **EP-18** | `DELETE` | `/v1/medscan/sessions/{session_id}` | MedScan | Delete single MedScan session |
| **EP-19** | `GET` | `/v1/reports/summaries` | Reports | List all saved chronological nutritional summaries for user |
| **EP-20** | `POST` | `/v1/reports/summaries` | Reports | Save manual nutritional assessment summary record |
| **EP-21** | `GET` | `/v1/reports/summaries/{summary_id}` | Reports | Fetch single saved summary with contributing condition rows |
| **EP-22** | `DELETE` | `/v1/reports/summaries/{summary_id}` | Reports | Delete single saved assessment summary |
| **EP-23** | `POST` | `/v1/reports/summaries/{summary_id}/suggested-routine` | Reports | Fetch non-pharmacological lifestyle routine for top deficiency |
| **EP-24** | `GET` | `/v1/reports/timeline` | Reports | Retrieve chronological risk band evolution across past assessments |
| **EP-25** | `GET` | `/v1/reports/aggregate` | Reports | Recency-weighted aggregation across all modules powering 6 Recharts |
| **EP-26** | `GET` | `/v1/careplan/tasks` | CarePlan | List all active, completed, and auto-synced wellness tasks |
| **EP-27** | `POST` | `/v1/careplan/tasks` | CarePlan | Create custom user lifestyle task (hydration, sleep, exercise) |
| **EP-28** | `PUT` | `/v1/careplan/tasks/{task_id}` | CarePlan | Toggle task completion or edit title and recurrence schedule |
| **EP-29** | `DELETE` | `/v1/careplan/tasks/{task_id}` | CarePlan | Delete custom wellness task |
| **EP-30** | `GET` | `/v1/careplan/export/ics` | CarePlan | Export active wellness schedule as RFC 5545 iCalendar (.ics) stream |
| **EP-31** | `GET` | `/v1/careplan/meal-plan` | CarePlan | Retrieve current 7-day deterministic meal plan |
| **EP-32** | `POST` | `/v1/careplan/meal-plan/generate` | CarePlan | Generate 7-day food plan from curated food guide matching user diet |
| **EP-33** | `GET` | `/v1/careplan/meal-plan/ics` | CarePlan | Export meal preparation schedule as iCalendar (.ics) file |
| **EP-34** | `POST` | `/v1/careplan/meal-plan/log` | CarePlan | Toggle completion of specific scheduled daily food item |
| **EP-35** | `GET` | `/v1/careplan/meal-plan/nutrients` | CarePlan | Compute cumulative nutritional intake coverage from logged meals |
| **EP-36** | `GET` | `/v1/careplan/meal-plan/preferences` | CarePlan | Fetch dietary preferences (vegan, vegetarian, omnivore, allergies) |
| **EP-37** | `PUT` | `/v1/careplan/meal-plan/preferences` | CarePlan | Update dietary preferences and allergen exclusion flags |
| **EP-38** | `GET` | `/v1/careplan/nutrition-guidance` | CarePlan | Fetch curated dietary sources and preparation notes from food guide |
| **EP-39** | `POST` | `/v1/nursebot/ask` | NurseBot | Process user chat message via intent router, emergency filter, and NIH API |
| **EP-40** | `GET` | `/v1/nursebot/menu` | NurseBot | Fetch top-level suggested application guidance FAQ buttons |
| **EP-41** | `GET` | `/v1/nursebot/topics/{topic_id}` | NurseBot | Fetch specific pre-vetted educational FAQ topic text |
| **EP-42** | `GET` | `/v1/mllab/status` | MLLab | Inspect ML microservice connectivity, loaded models, and memory status |
| **EP-43** | `GET` | `/v1/mllab/model-cards` | MLLab | List all 11 scientific model cards (3 tabular, 7 vision, 1 keyword) |
| **EP-44** | `GET` | `/v1/mllab/model-cards/{card_id}` | MLLab | Retrieve single model card with confusion matrix and provenance note |
| **EP-45** | `POST` | `/v1/mllab/predict/tabular` | MLLab | Benchmark XGBoost and LightGBM prediction on raw CSV feature vector |
| **EP-46** | `POST` | `/v1/mllab/predict/tabular_profile` | MLLab | Predict disease dataset label from user demographic profile |
| **EP-47** | `POST` | `/v1/mllab/predict/image` | MLLab | Run Float32 TFLite MobileNetV2 model on uploaded anatomical photo |
| **EP-48** | `POST` | `/v1/mllab/predict/keywords` | MLLab | Rank top-3 nutrient categories from free-text symptoms via TF-IDF model |
