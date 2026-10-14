"""
MedNourish — Audit all 34 CSV files and generate docs/CSV_USE_MATRIX.md
"""

import os
import glob
import csv
from pathlib import Path

ARCHIVE_DIR = Path(r"C:\Users\USER\Desktop\MedNourish\datasets")
DEV_DATASETS = Path(r"C:\Users\USER\Desktop\MedNourish-Dev\datasets")
DATASET_ROOT = ARCHIVE_DIR if ARCHIVE_DIR.exists() else DEV_DATASETS

def audit_file(p: Path):
    size = p.stat().st_size
    encoding = "utf-8"
    rows = []
    header = []
    
    try:
        with open(p, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            rows = [tuple(r) for r in reader]
    except UnicodeDecodeError:
        try:
            encoding = "latin1"
            with open(p, "r", encoding="latin1") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                rows = [tuple(r) for r in reader]
        except Exception as e:
            return 0, 0, 0, [], f"error: {e}", size
    except Exception as e:
        return 0, 0, 0, [], f"error: {e}", size
        
    row_count = len(rows)
    col_count = len(header)
    unique_rows = len(set(rows))
    duplicates = row_count - unique_rows
    col_names = [h.strip() for h in header]
    return row_count, col_count, duplicates, col_names, encoding, size

def audit_all_csvs():
    csv_paths = sorted(glob.glob(str(DATASET_ROOT / "**" / "*.csv"), recursive=True))
    print(f"Total CSV files found: {len(csv_paths)}")

    records = []
    for p_str in csv_paths:
        p = Path(p_str)
        rel_path = p.relative_to(DATASET_ROOT)
        rel_str = str(rel_path).replace("\\", "/")
        
        row_count, col_count, dups, col_names, encoding, size = audit_file(p)

        # Classification rule
        if rel_str == "vitamin_deficiency_disease_dataset_20260123.csv":
            category = "Used for Training"
            reason = "Main synthetic clinical tabular dataset (4,000 rows x 34 cols). Used for tabular ML benchmarking (XGBoost/LightGBM) with & without serum lab features."
        elif rel_str == "MedBot_datasets/MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv":
            category = "Used for Training & Reference"
            reason = "Master canonical mapping table (116 rows). Used for reference-table keyword-to-nutrient ML model and deterministic symptom lookup."
        elif "MedBot_datasets/" in rel_str:
            category = "Used as Reference Lookup"
            reason = "Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation."
        elif any(rel_str.startswith(f"{r}/") for r in ["EYES", "HAIR", "LIPS", "NAILS", "SKIN", "TONGUE"]) and (
            "_Symptoms_vs_" in rel_str or "_Suggested_Routine" in rel_str
        ):
            category = "Used as Reference Lookup (Duplicate)"
            reason = "Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used."
        elif "balanced_dataset" in rel_str:
            category = "Excluded"
            reason = "Dermatology image classification labels / metadata (HAM10000/ISIC skin lesion subset). Excluded from tabular deficiency models to prevent domain confusion."
        elif "Glaucoma" in rel_str or "Hypertensive_Retinopathy" in rel_str or "Ocular Conditions" in rel_str:
            category = "Excluded"
            reason = "Ophthalmic disease image ground truth / clinical metadata (G1020, HRDC). Excluded from tabular nutritional deficiency training."
        elif "dataset_info.csv" in rel_str:
            category = "Excluded"
            reason = "Hair image metadata catalog. Excluded from tabular deficiency modeling."
        else:
            category = "Excluded"
            reason = "Unused metadata file."

        records.append({
            "rel_path": rel_str,
            "size_bytes": size,
            "encoding": encoding,
            "rows": row_count,
            "cols": col_count,
            "duplicates": dups,
            "col_names": col_names,
            "category": category,
            "reason": reason
        })

    # Generate Markdown
    md = []
    md.append("# MedNourish — Complete 34-CSV Audit & Use Matrix")
    md.append("")
    md.append("**Audit Date:** 2026-10-14  ")
    md.append(f"**Dataset Source:** `{DATASET_ROOT}`  ")
    md.append(f"**Total CSV Files Audited:** {len(records)}  ")
    md.append("")
    md.append("This document audits every CSV file found within `datasets/`, specifying its schema, dimensions, duplicates, encoding, operational classification, and justification.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Summary Matrix")
    md.append("")
    md.append("| # | CSV Path | Rows | Cols | Dups | Encoding | Operational Category |")
    md.append("|---|---|---|---|---|---|---|")
    for idx, r in enumerate(records, 1):
        md.append(f"| {idx} | `{r['rel_path']}` | {r['rows']} | {r['cols']} | {r['duplicates']} | {r['encoding']} | **{r['category']}** |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Detailed File Profiles & Justifications")
    md.append("")
    
    for idx, r in enumerate(records, 1):
        md.append(f"### {idx}. `{r['rel_path']}`")
        md.append(f"- **Size:** {r['size_bytes']:,} bytes")
        md.append(f"- **Dimensions:** {r['rows']} rows × {r['cols']} columns")
        md.append(f"- **Encoding:** {r['encoding']}")
        md.append(f"- **Exact Duplicate Rows:** {r['duplicates']}")
        md.append(f"- **Columns:** `{', '.join(r['col_names'])}`")
        md.append(f"- **Decision:** **{r['category']}**")
        md.append(f"- **Rationale:** {r['reason']}")
        md.append("")

    doc_path = Path("docs/CSV_USE_MATRIX.md")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"Generated {doc_path} with {len(records)} entries.")

if __name__ == "__main__":
    audit_all_csvs()
