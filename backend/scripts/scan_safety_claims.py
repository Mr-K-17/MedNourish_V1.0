"""MedNourish — Automated Safety & Prohibited Claims Scanner
============================================================
Module: backend.scripts.scan_safety_claims
Spec: Final Finish F6 / SAF-01..SAF-17

Scans frontend code, backend endpoints, seed data, model cards, demo scripts,
and documentation to verify that no affirmative diagnostic, prescriptive, or
clinical probability claims exist in the user-facing application.

Uses an allowlist context check to permit necessary disclaimer, refusal, and
anti-diagnostic documentation sentences (e.g. 'not a medical diagnosis').
"""

import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SCAN_TARGETS = [
    os.path.join(REPO_ROOT, "backend", "app"),
    os.path.join(REPO_ROOT, "backend", "scripts"),
    os.path.join(REPO_ROOT, "frontend", "src"),
    os.path.join(REPO_ROOT, "ml", "artifacts", "vision"),
    os.path.join(REPO_ROOT, "ml", "artifacts", "tabular"),
    os.path.join(REPO_ROOT, "README.md"),
    os.path.join(REPO_ROOT, "docs", "DEMO_SCRIPT.md"),
]

BANNED_PATTERNS = [
    (r"\bautonomous diagnosis\b", "autonomous diagnosis"),
    (r"\bclinical decision support system\b", "clinical decision support system"),
    (r"\bwe prescribe\b", "we prescribe"),
    (r"\bcure your\b", "cure your"),
    (r"\breplaces your doctor\b", "replaces your doctor"),
    (r"\bguaranteed deficiency\b", "guaranteed deficiency"),
    (r"\b100% accurate diagnosis\b", "100% accurate diagnosis"),
    (r"\byou have deficiency\b", "you have deficiency"),
    (r"\bconfirmed deficiency\b", "confirmed deficiency"),
    (r"\bclinical prescription\b", "clinical prescription"),
    (r"\bprescribe medication\b", "prescribe medication"),
    (r"\bdisease probability\b", "disease probability"),
    (r"\bdeficiency probability\b", "deficiency probability"),
]

ALLOWLIST_SUBSTRINGS = [
    "not a medical diagnosis",
    "never a medical diagnosis",
    "is not a medical diagnosis",
    "cannot diagnose",
    "does not diagnose",
    "do not diagnose",
    "no medical diagnosis",
    "not a substitute",
    "not intended as",
    "disclaimer",
    "educational prototype",
    "educational reference",
    "never medical diagnoses",
    "never clinical risk",
    "not clinical treatments",
    "not a prescription",
    "not a clinical",
    "is not a clinical",
    "not clinical",
    "never a clinical",
    "zero medication",
    "zero-medication",
    "zero probability",
    "zero probabilities",
    "zero risk",
    "no probability",
    "without probabilities",
    "labels only",
    "banned",
    "forbidden",
    "prohibited",
    "refusal",
    "allowlist",
    "demo risk band",
    "reference match %",
    "model %",
    "image model %",
    "probable pattern",
    "screened",
]


def is_line_exempt(line_lower: str) -> bool:
    clean_line = line_lower.replace("*", "").replace("`", "").replace("_", "")
    return any(allow in clean_line for allow in ALLOWLIST_SUBSTRINGS)


def scan_repository():
    violations = []
    scanned_file_count = 0

    for target in SCAN_TARGETS:
        if not os.path.exists(target):
            continue

        if os.path.isfile(target):
            file_paths = [target]
        else:
            file_paths = []
            for root, _, files in os.walk(target):
                for f in files:
                    if f.endswith((".py", ".ts", ".tsx", ".md", ".json", ".yaml", ".yml")):
                        file_paths.append(os.path.join(root, f))

        for fpath in file_paths:
            if os.path.abspath(fpath) == os.path.abspath(__file__):
                continue
            scanned_file_count += 1
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, start=1):
                        line_lower = line.lower().strip()
                        if not line_lower or is_line_exempt(line_lower):
                            continue

                        for pattern, label in BANNED_PATTERNS:
                            if re.search(pattern, line_lower):
                                violations.append({
                                    "file": os.path.relpath(fpath, REPO_ROOT),
                                    "line_no": line_no,
                                    "pattern": label,
                                    "snippet": line.strip(),
                                })
            except Exception as e:
                print(f"Warning reading {fpath}: {e}")

    print(f"[*] Audited {scanned_file_count} files across frontend, backend, ML artifacts, and documentation.")

    if violations:
        print(f"\n[FAIL] Found {len(violations)} prohibited claim occurrences:")
        for v in violations:
            print(f"  {v['file']}:{v['line_no']} -> [{v['pattern']}] \"{v['snippet']}\"")
        return False

    print("[SUCCESS] 100% PASS: Zero prohibited diagnostic or prescriptive claims detected.")
    return True


if __name__ == "__main__":
    passed = scan_repository()
    sys.exit(0 if passed else 1)
