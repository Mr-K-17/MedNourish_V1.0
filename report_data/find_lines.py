import os

root = r"C:\Users\USER\Desktop\MedNourish-Dev"
out_dir = os.path.join(root, "report_data", "code_excerpts")
os.makedirs(out_dir, exist_ok=True)

def extract_snippet(file_rel, start_line, end_line, title, explanation):
    abs_path = os.path.join(root, file_rel.replace("/", "\\"))
    with open(abs_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    snippet = "".join(lines[start_line - 1 : end_line])
    
    content = f"""# Code Excerpt: {title}

- **Source File**: [`{file_rel}`](file:///{root.replace('\\\\', '/')}/{file_rel}#L{start_line}-L{end_line})
- **Lines**: {start_line}–{end_line}
- **Language**: Python

### Purpose & Architectural Rationale
{explanation}

```python
{snippet.strip()}
```

*Educational Prototype - Not a Medical Device.*
"""
    return content

# 1. Matcher Core: backend/app/services/scoring_service.py
# Let's inspect scoring_service.py around match or scoring
abs_scoring = os.path.join(root, "backend", "app", "services", "scoring_service.py")
with open(abs_scoring, "r", encoding="utf-8") as f:
    scoring_lines = f.readlines()

print(f"scoring_service.py total lines: {len(scoring_lines)}")
