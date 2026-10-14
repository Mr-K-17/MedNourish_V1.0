"""
MedNourish — Reference Contract, Crosswalk and Join Coverage
============================================================
Module: ml.ref_contract
Spec: Phase 3.3 Stage 2(b)

Loads curated CSVs with keep_default_na=False.
Keys rows by (Body_Region, Class_Label).
Builds crosswalk.csv mapping master Class_Label -> regional Class_Label
and master Vitamin_Deficiency -> routine Vitamin_Deficiency.
Evaluates join coverage.
"""

import csv
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any

CURATED_DIR = Path("knowledge/curated")

def clean_key(s: str) -> str:
    return s.strip().lower().replace("_", "").replace(" ", "").replace("-", "")

def load_csv_rows(filepath: Path) -> List[Dict[str, str]]:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        return [{k: (v if v is not None else "") for k, v in row.items()} for row in reader]

def build_reference_crosswalk() -> Dict[str, Any]:
    master_file = CURATED_DIR / "MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv"
    master_rows = load_csv_rows(master_file)

    regions = ["Eyes", "Hair", "Lips", "Nails", "Skin", "Tongue"]
    regional_maps = {}
    routine_maps = {}

    for r in regions:
        reg_file = CURATED_DIR / f"{r}_Symptoms_vs_Vitamin_Deficiency_Mapping.csv"
        rout_file = CURATED_DIR / f"{r}_Vitamin_Deficiency_to_Suggested_Routine.csv"
        
        reg_rows = load_csv_rows(reg_file) if reg_file.exists() else []
        rout_rows = load_csv_rows(rout_file) if rout_file.exists() else []

        r_key = r.upper()
        # Key regional by clean Class_Label
        regional_maps[r_key] = {clean_key(row.get("Class_Label", "")): row.get("Class_Label", "") for row in reg_rows}
        # Key routine by clean Vitamin_Deficiency
        routine_maps[r_key] = {clean_key(row.get("Vitamin_Deficiency", "")): row.get("Vitamin_Deficiency", "") for row in rout_rows}

    # Manual alias overrides for edge differences
    manual_class_aliases = {
        ("Skin", clean_key("Skin_B3_Pellagra")): "VITAMIN_B3_PELLAGRA",
        ("Skin", clean_key("Skin_Vitamin_B3_Pellagra")): "VITAMIN_B3_PELLAGRA",
        ("Hair", clean_key("Hair_Shaft_Corkscrew_Hair")): "CORKSCREW_HAIR",
    }

    manual_routine_aliases = {
        ("Eyes", clean_key("Vitamin B Complex Deficiency")): "Multiple (B1, B2, B6, B9, Folate) Deficiency",
        ("Hair", clean_key("Vitamin B Complex Deficiency")): "Multiple (B1, B2, B6, B9, Folate) Deficiency",
        ("Lips", clean_key("Vitamin B Complex Deficiency")): "Multiple (B1, B2, B6, B9, Folate) Deficiency",
        ("Nails", clean_key("Vitamin B Complex Deficiency")): "Multiple (B1, B2, B6, B9, Folate) Deficiency",
        ("Skin", clean_key("Vitamin B Complex Deficiency")): "Multiple (B1, B2, B6, B9, Folate) Deficiency",
        ("Tongue", clean_key("Vitamin B Complex Deficiency")): "Multiple (B1, B2, B6, B9, Folate) Deficiency",
    }

    crosswalk_rows = []
    matched_regional = 0
    matched_routine = 0
    unmatched_rows = []

    for row in master_rows:
        region = row.get("Body_Region", "").strip()
        m_class = row.get("Class_Label", "").strip()
        m_vit = row.get("Vitamin_Deficiency", "").strip()

        reg_dict = regional_maps.get(region, {})
        rout_dict = routine_maps.get(region, {})

        # Find regional match
        c_key = clean_key(m_class)
        matched_reg_class = reg_dict.get(c_key)
        if not matched_reg_class and (region, c_key) in manual_class_aliases:
            matched_reg_class = manual_class_aliases[(region, c_key)]
        if not matched_reg_class:
            # Try fuzzy substring match within region
            for k, original in reg_dict.items():
                if k in c_key or c_key in k:
                    matched_reg_class = original
                    break

        # Find routine match
        v_key = clean_key(m_vit)
        matched_rout_vit = rout_dict.get(v_key)
        if not matched_rout_vit and (region, v_key) in manual_routine_aliases:
            matched_rout_vit = manual_routine_aliases[(region, v_key)]
        if not matched_rout_vit:
            for k, original in rout_dict.items():
                if k in v_key or v_key in k:
                    matched_rout_vit = original
                    break

        has_reg = bool(matched_reg_class)
        has_rout = bool(matched_rout_vit)

        if has_reg:
            matched_regional += 1
        if has_rout:
            matched_routine += 1
        if not has_reg or not has_rout:
            unmatched_rows.append({
                "body_region": region,
                "master_class": m_class,
                "missing_regional": not has_reg,
                "missing_routine": not has_rout
            })

        crosswalk_rows.append({
            "master_body_region": region,
            "master_class_label": m_class,
            "master_vitamin_deficiency": m_vit,
            "regional_class_label": matched_reg_class or "",
            "routine_vitamin_deficiency": matched_rout_vit or "",
            "regional_join_status": "MATCHED" if has_reg else "UNMATCHED",
            "routine_join_status": "MATCHED" if has_rout else "UNMATCHED"
        })

    # Save crosswalk.csv
    crosswalk_path = CURATED_DIR / "crosswalk.csv"
    with open(crosswalk_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "master_body_region", "master_class_label", "master_vitamin_deficiency",
            "regional_class_label", "routine_vitamin_deficiency",
            "regional_join_status", "routine_join_status"
        ])
        writer.writeheader()
        writer.writerows(crosswalk_rows)

    total_master = len(master_rows)
    coverage = {
        "total_master_rows": total_master,
        "matched_regional": matched_regional,
        "matched_routine": matched_routine,
        "regional_coverage_pct": round((matched_regional / total_master) * 100, 2),
        "routine_coverage_pct": round((matched_routine / total_master) * 100, 2),
        "unmatched_count": len(unmatched_rows),
        "unmatched_rows": unmatched_rows
    }
    return coverage

if __name__ == "__main__":
    cov = build_reference_crosswalk()
    print("Crosswalk generated:", cov)
