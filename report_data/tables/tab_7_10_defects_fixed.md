# Table Tab 7 10 Defects Fixed

| defect_id | severity | component | defect_description | root_cause | resolution |
| --- | --- | --- | --- | --- | --- |
| BUG-01 | High | ML Vision (Hair) | Dataset CSV parsing failure in hair model loader | Trailing comma typo in class mapping CSV header | Corrected CSV schema and added strict validator test |
| BUG-02 | Medium | CarePlan Meal Planner | Nutritional item description truncated in UI | Database column VARCHAR(135) cutoff length | Expanded schema column to VARCHAR(500) and upgraded serializer |
| BUG-03 | Critical | Environment Compatibility | TensorFlow import crash on host Python 3.14 | TensorFlow 2.18 official wheels only support up to Python 3.12 | Implemented dual-venv architecture: Python 3.14 backend, Python 3.12 ML |
| BUG-04 | Medium | MedScan Quality Gate | Zero-variance solid white images bypassed blur check | Laplacian of uniform image yields 0 variance (treated as blur, but lum passed) | Added dual-band luminance rejection (40 <= lum <= 225) |
| BUG-05 | Low | CarePlan Calendar | iCalendar import failed in Apple Calendar | Missing CRLF line breaks and DTSTAMP property | Enforced strict RFC 5545 format with UID and DTSTAMP |

*Educational Prototype - Not a Medical Device.*
