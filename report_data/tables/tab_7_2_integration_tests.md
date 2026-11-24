# Table Tab 7 2 Integration Tests

| test_id | integrated_modules | test_file | scenario_description | expected_response_code | status |
| --- | --- | --- | --- | --- | --- |
| IT-API-01 | FastAPI + SQLite / MySQL DB | test_auth_profile.py | Create profile with Bearer token header | 200 OK | PASSED |
| IT-API-02 | FastAPI + Consent Engine | test_consent_flow.py | Access health endpoint without consent log | 403 Forbidden | PASSED |
| IT-API-03 | MedScan -> ImageGate -> TFLite | test_medscan_flow.py | Submit dark image payload | 422 Unprocessable / Rejected | PASSED |
| IT-API-04 | MedScan -> TFLite -> Scoring | test_medscan_flow.py | Valid nail scan inference with shortcut penalty | 200 OK | PASSED |
| IT-API-05 | MedBot -> Matcher -> Summary DB | test_medbot_flow.py | Multi-turn interview session state saved to DB | 200 OK | PASSED |
| IT-API-06 | CarePlan -> Aggregation -> DB | test_careplan_sync.py | Sync daily nutrition tasks and recalculate progress | 200 OK | PASSED |
| IT-API-07 | NurseBot -> MedlinePlus -> Triage | test_nursebot_flow.py | Trigger emergency keyword 'severe chest pain' | 200 OK (Emergency Triage Flag) | PASSED |

*Educational Prototype - Not a Medical Device.*
