# Table Tab 8 8 Known Limitations

| limitation_id | domain | documented_constraint | mitigation_or_operational_boundary |
| --- | --- | --- | --- |
| LIM-01 | Scope | Educational and research prototype only; not certified as a medical device | Persistent UI banner, strict non-diagnostic claims scanner, emergency triage routing |
| LIM-02 | Vision Models | Skin vision model exhibits high shortcut risk (macro-F1 0.648 due to background skin tone/glare) | Shortcut penalty coefficient applied; user advised to consult clinical dermatologist |
| LIM-03 | Tabular Model | Symptom-only model accuracy bounded at 76.5% without biochemical lab measurements | User prompted with 'Insufficient Information' advisory when symptom count < 2 |
| LIM-04 | Speech Recognition | Web Speech API depends on browser-level client support (Chrome / Edge) | Graceful UI fallback to interactive symptom chip selectors and manual keyboard input |
| LIM-05 | Database Persistence | MongoDB is an optional probe; primary production persistence is SQLite / MySQL | Dynamic SQLAlchemy dual-dialect connector with zero schema migration lock-in |

*Educational Prototype - Not a Medical Device.*
