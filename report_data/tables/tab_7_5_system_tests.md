# Table Tab 7 5 System Tests

| step_no | system_test_step | endpoint_or_component | input_data | expected_result | actual_status |
| --- | --- | --- | --- | --- | --- |
| 1 | Health probe check | GET /api/v1/health | None | Status ok, DB connected, ML status ready | PASSED |
| 2 | Database readiness probe | GET /api/v1/health/db | None | Engine active (SQLite or MySQL) | PASSED |
| 3 | User consent registration | POST /api/v1/consent | user_id, agreed=true, v2.0 | Consent log created with timestamp | PASSED |
| 4 | User profile bootstrap | POST /api/v1/profile | Age: 28, Gender: Female, Diet: Vegan | Profile record created with calculated BMI | PASSED |
| 5 | Symptom search autocomplete | GET /api/v1/symptoms/search | q='fatigue' | Returns canonical symptom suggestions | PASSED |
| 6 | Symptom matching calculation | POST /api/v1/symptoms/match | symptoms=['fatigue', 'pale_skin'] | Calculates match % and nutritional hints | PASSED |
| 7 | Insufficient info boundary | POST /api/v1/symptoms/match | symptoms=['fatigue'] | Returns warning flag 'Insufficient Information' | PASSED |
| 8 | MedBot interview session start | POST /api/v1/medbot/start | user_id, mode='guided' | Returns first targeted symptom question | PASSED |
| 9 | MedBot answer & follow-up | POST /api/v1/medbot/next | session_id, answer='yes' | Shrinks hypothesis space via information gain | PASSED |
| 10 | MedBot summary generation | POST /api/v1/medbot/summary | session_id | Persists session summary in saved_summaries | PASSED |
| 11 | MedScan blur rejection | POST /api/v1/medscan/analyze | Synthetic blurry eye image (var < 50) | Returns HTTP 422 with blur warning | PASSED |
| 12 | MedScan valid nail analysis | POST /api/v1/medscan/analyze | Valid nail image (var > 50, lum 110) | Classifies Spoon Nails (Koilonychia) with conf | PASSED |
| 13 | NurseBot MedlinePlus lookup | POST /api/v1/nursebot/query | q='Vitamin B12 dietary sources' | Returns curated MedlinePlus snippet | PASSED |
| 14 | NurseBot emergency trigger | POST /api/v1/nursebot/query | q='chest pain and difficulty breathing' | Flags triage red: dial emergency hotline | PASSED |
| 15 | Virtual Ward risk monitor | GET /api/v1/ward/status | user_id | Recency-weighted risk aggregation score | PASSED |
| 16 | CarePlan task generation | POST /api/v1/careplan/generate | deficiency='Iron Deficiency' | Returns daily diet and hydration checklist | PASSED |
| 17 | CarePlan iCalendar export | GET /api/v1/careplan/export.ics | plan_id | Returns RFC 5545 text/calendar byte stream | PASSED |
| 18 | Reports historical trend | GET /api/v1/reports/history | user_id, days=30 | Returns 6-chart temporal trend time-series | PASSED |

*Educational Prototype - Not a Medical Device.*
