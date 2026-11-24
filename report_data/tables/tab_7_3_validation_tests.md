# Table Tab 7 3 Validation Tests

| req_id | requirement_description | verifying_test_suite | verification_method | outcome |
| --- | --- | --- | --- | --- |
| SAFE-01 | Mandatory non-diagnostic educational prototype disclaimer | scripts/scan_claims.py | Automated regex scan across all markdown and code | PASSED (0 violations in 76 files) |
| SAFE-02 | Strict prohibition of medical diagnostic terms | scripts/scan_claims.py | AST search for banned claims ('diagnoses', 'prescribes') | PASSED |
| SYMP-01 | Deterministic Reference Match percentage calculation | test_matcher.py | Known ground-truth overlap comparison | PASSED (100% exact match) |
| SYMP-02 | Insufficiency gate for sparse inputs | test_scoring.py | Trigger evaluation on single symptom input | PASSED (Flags Insufficient Info) |
| SCAN-01 | Laplacian blur filtering (threshold = 50.0) | test_quality.py | Feed synthetic blurred image tensors | PASSED (Rejected with advisory) |
| SCAN-02 | Illumination gating (luminance 40-225) | test_quality.py | Feed dark (<40) and overexposed (>225) images | PASSED (Rejected with lighting tip) |
| MEDBOT-01 | Speech recognition accessibility fallback | frontend/test/MedBot.test.tsx | Verify Web Speech API check and fallback to text | PASSED |
| CARE-01 | Deterministic meal plan composition | test_careplan.py | Verify zero hallucinations in nutrient mapping | PASSED |
| CARE-02 | RFC 5545 calendar export | test_careplan.py | Validate generated .ics with icalendar parser | PASSED (Valid ICS format) |

*Educational Prototype - Not a Medical Device.*
