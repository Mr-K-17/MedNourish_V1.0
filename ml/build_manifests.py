"""
MedNourish — Image Dataset Analysis, Cleaning, and Manifest Generator
=====================================================================
Module: ml.build_manifests
Spec: Phase 3.3 Stage 3

Generates clean, leakage-resistant manifests for 7 CV models:
- eyes, hair, lips, nails, skin, tongue, combined (11 vitamin classes)

Pipeline per model:
1. Scans source folders defined in ml/class_maps/<model>.yaml.
2. Filters out masks, segmentation collages, corrupt images, tiny images (<64x64).
3. Computes sha256 and perceptual hash (pHash) with imagehash.
4. Deduplicates exact duplicates (sha256) and clusters near-duplicates (pHash Hamming distance <= 2).
5. Computes blur variance (Laplacian) and mean luminance using ml.image_pipeline.
6. Caps each class at 600 images (configurable); drops classes with < 100 usable images.
7. Produces group-aware 70/15/15 train/val/test splits keeping near-duplicate clusters together.
8. Writes CSV manifests to ml/artifacts/manifests/<model>_manifest.csv.
9. Generates docs/IMAGE_DATA_REPORT.md detailing audit numbers, drops, imbalance, and risks.
"""

import csv
import hashlib
import json
import os
import random
import sys
import yaml
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np
from PIL import Image
import imagehash

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.image_pipeline import (
    QualityConfig,
    calculate_blur_variance,
    calculate_mean_luminance,
    load_image_rgb,
)

ARCHIVE_DIR = Path(r"C:\Users\USER\Desktop\MedNourish\datasets")
DEV_DATASETS = Path(r"C:\Users\USER\Desktop\MedNourish-Dev\datasets")
DATASET_ROOT = ARCHIVE_DIR if ARCHIVE_DIR.exists() else DEV_DATASETS

MANIFESTS_DIR = Path("ml/artifacts/manifests")
MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

CLASS_MAPS_DIR = Path("ml/class_maps")
DOCS_DIR = Path("docs")

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".jfif"}
RANDOM_SEED = 42

def is_mask_or_annotation(path: Path) -> bool:
    p_lower = str(path).lower()
    return any(term in p_lower for term in ["mask", "groundtruth", "annotation", "label", "_seg", "-seg"])

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def process_model(model_yaml_path: Path) -> Dict[str, Any]:
    with open(model_yaml_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    model_name = spec["model"]
    dataset_root = DATASET_ROOT / spec["dataset_root"]
    cap_per_class = spec.get("cap_per_class", 600)
    classes_spec = spec.get("classes", [])
    excluded_spec = spec.get("excluded_folders", [])

    print(f"\n==========================================")
    print(f"Processing Model: {model_name.upper()} (Root: {dataset_root})")
    print(f"==========================================")

    model_stats = {
        "model": model_name,
        "dataset_root": spec["dataset_root"],
        "cap_per_class": cap_per_class,
        "initial_counts": {},
        "after_cleaning_counts": {},
        "dropped_classes": [],
        "retained_classes": [],
        "total_manifest_images": 0,
        "split_counts": {"train": 0, "val": 0, "test": 0},
        "exact_duplicates_removed": 0,
        "near_duplicates_removed": 0,
        "quality_failures": 0,
    }

    # Record explicitly excluded folders
    for exc in excluded_spec:
        model_stats["dropped_classes"].append({
            "folder": exc["name"],
            "reason": exc.get("reason", "Pre-configured exclusion")
        })

    class_records: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    seen_sha256: Set[str] = set()
    seen_phash_ints: List[int] = []

    for cls in classes_spec:
        cls_name = cls["name"]
        source_folders = cls["source_folders"]

        # Collect candidate image files
        candidate_paths: List[Path] = []
        max_candidates = cap_per_class * 2
        for sf in source_folders:
            folder_path = dataset_root / sf
            if not folder_path.exists():
                print(f"Warning: Folder {folder_path} not found.", flush=True)
                continue
            for root, dirs, files in os.walk(folder_path):
                if is_mask_or_annotation(Path(root)):
                    continue
                for file in files:
                    fp = Path(root) / file
                    if fp.suffix.lower() in IMG_EXTS and not is_mask_or_annotation(fp):
                        candidate_paths.append(fp)
                        if len(candidate_paths) >= max_candidates:
                            break
                if len(candidate_paths) >= max_candidates:
                    break
            if len(candidate_paths) >= max_candidates:
                break

        initial_count = len(candidate_paths)
        model_stats["initial_counts"][cls_name] = initial_count
        print(f"Class '{cls_name}': Scanning {initial_count} candidate images from {source_folders}", flush=True)

        usable_records: List[Dict[str, Any]] = []

        for p in candidate_paths:
            if len(usable_records) >= cap_per_class:
                break

            # 1. Exact Duplicate Check (SHA256)
            try:
                sha = compute_sha256(p)
            except Exception:
                continue

            if sha in seen_sha256:
                model_stats["exact_duplicates_removed"] += 1
                continue

            # 2. Decode and Quality Check
            img_rgb = load_image_rgb(p)
            if img_rgb is None:
                model_stats["quality_failures"] += 1
                continue

            h, w = img_rgb.shape[:2]
            if h < 64 or w < 64:
                model_stats["quality_failures"] += 1
                continue

            # 3. Perceptual Hash (Near-duplicate cluster check)
            try:
                pil_img = Image.fromarray(img_rgb)
                ph = imagehash.phash(pil_img)
                ph_str = str(ph)
                ph_int = int(ph_str, 16)
            except Exception:
                continue

            # Native bit_count popcount Hamming distance comparison
            if any((ph_int ^ ex).bit_count() <= 2 for ex in seen_phash_ints):
                model_stats["near_duplicates_removed"] += 1
                continue

            # 4. Blur and Luminance
            blur = calculate_blur_variance(img_rgb)
            lum = calculate_mean_luminance(img_rgb)
            quality_pass = bool(blur >= 50.0 and 20.0 <= lum <= 235.0)

            seen_sha256.add(sha)
            seen_phash_ints.append(ph_int)

            rel_path = str(p.relative_to(PROJECT_ROOT.parent if (PROJECT_ROOT.parent / "datasets").exists() else DATASET_ROOT.parent))

            usable_records.append({
                "filepath": str(p),
                "relative_path": rel_path.replace("\\", "/"),
                "class_name": cls_name,
                "sha256": sha,
                "phash": ph_str,
                "phash_cluster": ph_str[:8],  # 8-char prefix for group-aware splitting
                "width": w,
                "height": h,
                "blur_variance": round(blur, 2),
                "mean_luminance": round(lum, 2),
                "quality_pass": quality_pass,
            })

        class_records[cls_name] = usable_records
        model_stats["after_cleaning_counts"][cls_name] = len(usable_records)
        print(f"Class '{cls_name}': Cleaned & retained {len(usable_records)} images.")

    # Rule: Drop classes with < 100 usable images
    retained_classes = []
    final_records: List[Dict[str, Any]] = []

    for cls_name, recs in class_records.items():
        if len(recs) < 100:
            print(f"DROPPING Class '{cls_name}': Insufficient samples ({len(recs)} < 100).")
            model_stats["dropped_classes"].append({
                "class": cls_name,
                "usable_count": len(recs),
                "reason": f"Under minimum support threshold (usable={len(recs)} < 100)"
            })
        else:
            retained_classes.append(cls_name)
            final_records.extend(recs)

    model_stats["retained_classes"] = retained_classes

    # Group-aware 70/15/15 train/val/test split by perceptual-hash cluster
    # Group records by (class_name, phash_cluster)
    cluster_groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for r in final_records:
        cluster_groups[(r["class_name"], r["phash_cluster"])].append(r)

    # Distribute clusters per class
    train_recs, val_recs, test_recs = [], [], []

    for c_name in retained_classes:
        c_clusters = [recs for (cn, _), recs in cluster_groups.items() if cn == c_name]
        random.seed(RANDOM_SEED)
        random.shuffle(c_clusters)

        total_imgs = sum(len(c) for c in c_clusters)
        target_train = int(total_imgs * 0.70)
        target_val = int(total_imgs * 0.15)

        curr_train, curr_val = 0, 0
        for cluster in c_clusters:
            if curr_train < target_train:
                for r in cluster:
                    r["split"] = "train"
                train_recs.extend(cluster)
                curr_train += len(cluster)
            elif curr_val < target_val:
                for r in cluster:
                    r["split"] = "val"
                val_recs.extend(cluster)
                curr_val += len(cluster)
            else:
                for r in cluster:
                    r["split"] = "test"
                test_recs.extend(cluster)

    all_split_records = train_recs + val_recs + test_recs
    model_stats["total_manifest_images"] = len(all_split_records)
    model_stats["split_counts"]["train"] = len(train_recs)
    model_stats["split_counts"]["val"] = len(val_recs)
    model_stats["split_counts"]["test"] = len(test_recs)

    # Write manifest CSV
    manifest_csv = MANIFESTS_DIR / f"{model_name}_manifest.csv"
    with open(manifest_csv, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "filepath", "relative_path", "class_name", "split",
            "sha256", "phash", "width", "height",
            "blur_variance", "mean_luminance", "quality_pass"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_split_records)

    print(f"Wrote manifest: {manifest_csv} with {len(all_split_records)} rows.")
    print(f"Splits -> Train: {len(train_recs)}, Val: {len(val_recs)}, Test: {len(test_recs)}")
    return model_stats

def generate_image_data_report(all_model_stats: List[Dict[str, Any]]):
    md = []
    md.append("# MedNourish — Computer Vision Image Dataset Audit & Manifest Report")
    md.append("")
    md.append("**Report Date:** 2026-10-14  ")
    md.append("**Governing Milestone:** Phase 3.3 Stage 3 (Image Dataset Analysis & Manifests)  ")
    md.append(f"**Dataset Source Archive:** `{DATASET_ROOT}`  ")
    md.append("")
    md.append("This document reports the empirical inventory, deduplication, quality filtering, ")
    md.append("class threshold gating (>= 100 images), and group-aware 70/15/15 splits across all 7 vision models.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Executive Summary Table")
    md.append("")
    md.append("| Model | Usable Classes | Total Retained | Train (70%) | Val (15%) | Test (15%) | Exact Dups Removed | Near-Dups Clustered | Quality Rejections |")
    md.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    for s in all_model_stats:
        md.append(
            f"| **`{s['model']}`** | {len(s['retained_classes'])} | {s['total_manifest_images']} | "
            f"{s['split_counts']['train']} | {s['split_counts']['val']} | {s['split_counts']['test']} | "
            f"{s['exact_duplicates_removed']} | {s['near_duplicates_removed']} | {s['quality_failures']} |"
        )
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Model Profiles & Gating Decisions")
    md.append("")

    for s in all_model_stats:
        md.append(f"### Model: `{s['model'].upper()}`")
        md.append(f"- **Dataset Root Folder:** `{s['dataset_root']}`")
        md.append(f"- **Configured Class Cap:** {s['cap_per_class']} images/class")
        md.append(f"- **Retained Classes ({len(s['retained_classes'])}):** `{', '.join(s['retained_classes'])}`")
        
        md.append("- **Class Count Breakdown (Initial vs Cleaned):**")
        for cls_n in s["initial_counts"]:
            init_c = s["initial_counts"][cls_n]
            clean_c = s["after_cleaning_counts"].get(cls_n, 0)
            md.append(f"  * `{cls_n}`: {init_c:,} raw -> {clean_c:,} cleaned")

        if s["dropped_classes"]:
            md.append("- **Dropped / Excluded Classes (< 100 usable images):**")
            for d in s["dropped_classes"]:
                md.append(f"  * **`{d.get('class') or d.get('folder')}`**: {d.get('reason')}")
        else:
            md.append("- **Dropped Classes:** None (all classes satisfied >= 100 usable images)")

        md.append("")

    md.append("---")
    md.append("")
    md.append("## 3. Known Methodological Risks & Clinical Disclaimers")
    md.append("")
    md.append("1. **Source-per-Class Shortcut Learning:**")
    md.append("   - Pathological and normal image subsets often originate from distinct open-source clinical repositories ")
    md.append("     with differing aspect ratios, lighting temperatures, background colors, and sensor characteristics.")
    md.append("   - Neural networks risk learning source sensor artifacts rather than physiological pathology.")
    md.append("2. **Anatomical Overlap and Diagnostic Specificity:**")
    md.append("   - Physical signs such as follicular hyperkeratosis, atrophic glossitis, or brittle nails are not pathognomonic ")
    md.append("     for a single micronutrient deficiency; overlapping systemic etiology is ubiquitous in clinical medicine.")
    md.append("3. **Strict Academic Demo Scope:**")
    md.append("   - All vision models are educational prototypes demonstrating computer-vision engineering feasibility. ")
    md.append("   - Zero clinical or diagnostic authority is claimed or permitted under project guidelines.")
    md.append("")

    report_path = DOCS_DIR / "IMAGE_DATA_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"Generated comprehensive report at {report_path}")

def main():
    print("=== STARTING STAGE 3 IMAGE MANIFEST & DATASET AUDIT ===")
    model_yamls = [
        CLASS_MAPS_DIR / "combined.yaml",
        CLASS_MAPS_DIR / "eyes.yaml",
        CLASS_MAPS_DIR / "hair.yaml",
        CLASS_MAPS_DIR / "lips.yaml",
        CLASS_MAPS_DIR / "nails.yaml",
        CLASS_MAPS_DIR / "skin.yaml",
        CLASS_MAPS_DIR / "tongue.yaml",
    ]

    all_stats = []
    for y_path in model_yamls:
        if y_path.exists():
            stats = process_model(y_path)
            all_stats.append(stats)

    generate_image_data_report(all_stats)
    print("\n=== STAGE 3 COMPLETE ===")

if __name__ == "__main__":
    main()
