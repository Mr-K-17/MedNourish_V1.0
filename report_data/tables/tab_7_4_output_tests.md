# Table Tab 7 4 Output Tests

| output_channel | verification_criteria | target_artifact_or_endpoint | compliance_check | status |
| --- | --- | --- | --- | --- |
| Web UI Banner | Educational disclaimer visible on all routes | App.tsx & Banner.tsx | Persistent top banner rendered across viewport | PASSED |
| Emergency Modal | Immediate 911 / 112 triage hotline surfaced | EmergencyModal.tsx | Rendered when chest pain/shortness of breath detected | PASSED |
| Print View CSS | High-contrast clinical summary without navbars | index.css @media print | Navbar, buttons hidden; black-and-white readable | PASSED |
| Calendar File | RFC 5545 iCalendar standard conformity | /api/v1/careplan/export.ics | Imports cleanly into Apple Calendar & Google Calendar | PASSED |
| API Documentation | OpenAPI 3.1 schema specification compliance | /openapi.json | Valid OpenAPI schema with all 48 endpoints mapped | PASSED |

*Educational Prototype - Not a Medical Device.*
