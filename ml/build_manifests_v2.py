"""
MedNourish — Phase 3 v2 Manifest Generator (min 40 support gate)
================================================================
Spec: Phase 3 (a)
Generates clean, leakage-resistant manifests for 7 CV models:
- eyes, hair, lips, nails, skin, tongue, combined (11 vitamin classes)
Gating:
- Drops classes with < 40 usable images (reports them)
- Near-duplicate clustering via pHash Hamming distance <= 2
- 70/15/15 train/val/test group-aware split
- Writes manifests to ml/artifacts/v2/manifests/<model>_manifest.csv
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.image_pipeline import (
    calculate_blur_variance,
    calculate_mean_luminance,
    load_image_rgb,
)

ARCHIVE_DIR = Path(r"C:\Users\USER\Desktop\MedNourish\datasets")
DEV_DATASETS = Path(r"C:\Users\USER\Desktop\MedNourish-Dev\datasets")
DATASET_ROOT = ARCHIVE_DIR if ARCHIVE_DIR.exists() else DEV_DATASETS

MANIFESTS_DIR = Path("ml/artifacts/v2/manifests")
MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

CLASS_MAPS_DIR = Path("ml/class_maps")
MIN_SUPPORT_GATE = 40
CAP_PER_CLASS = 600
RANDOM_SEED = 42

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def process_model_v2(model_yaml_path: Path) -> Dict[str, Any]:
    with open(model_yaml_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    model_name = spec["model"]
    dataset_root = DATASET_ROOT / spec["dataset_root"]
    cap_per_class = spec.get("cap_per_class", CAP_PER_CLASS)
    classes_spec = spec.get("classes", [])

    print(f"\n==========================================")
    print(f"Building v2 Manifest: {model_name.upper()} (Root: {dataset_root})")
    print(f"==========================================")

    model_stats = {
        "model": model_name,
        "dataset_root": spec["dataset_root"],
        "min_support_gate": MIN_SUPPORT_GATE,
        "initial_counts": {},
        "after_cleaning_counts": {},
        "dropped_classes": [],
        "retained_classes": [],
        "total_manifest_images": 0,
        "split_counts": {"train": 0, "val": 0, "test": 0},
    }

    class_records: Dict[str, List[Dict[str, Any]]] = {}

    for c_entry in classes_spec:
        cls_name = c_entry["name"]
        folders = c_entry["source_folders"]

        raw_files = []
        for fld in folders:
            folder_path = dataset_root / fld
            if folder_path.exists():
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        p = Path(root) / file
                        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".jfif"}:
                            raw_files.append(p)

        model_stats["initial_counts"][cls_name] = len(raw_files)
        print(f"Class '{cls_name}': Discovered {len(raw_files)} raw candidate images.")

        usable_records = []
        seen_sha256: Set[str] = set()
        seen_phash_ints: List[int] = []

        random.seed(RANDOM_SEED)
        random.shuffle(raw_files)

        for p in raw_files:
            if len(usable_records) >= cap_per_class:
                break

            try:
                sha = compute_sha256(p)
            except Exception:
                continue

            if sha in seen_sha256:
                continue

            img_rgb = load_image_rgb(p)
            if img_rgb is None:
                continue

            h, w = img_rgb.shape[:2]
            if h < 64 or w < 64:
                continue

            try:
                pil_img = Image.fromarray(img_rgb)
                ph = imagehash.phash(pil_img)
                ph_str = str(ph)
                ph_int = int(ph_str, 16)
            except Exception:
                continue

            if any((ph_int ^ ex).bit_count() <= 2 for ex in seen_phash_ints):
                continue

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
                "phash_cluster": ph_str[:8],
                "width": w,
                "height": h,
                "blur_variance": round(blur, 2),
                "mean_luminance": round(lum, 2),
                "quality_pass": quality_pass,
            })

        class_records[cls_name] = usable_records
        model_stats["after_cleaning_counts"][cls_name] = len(usable_records)
        print(f"Class '{cls_name}': Usable clean samples = {len(usable_records)}")

    # Gate: Drop classes with < 40 usable images
    retained_classes = []
    final_records: List[Dict[str, Any]] = []

    for cls_name, recs in class_records.items():
        if len(recs) < MIN_SUPPORT_GATE:
            print(f"DROPPING Class '{cls_name}': Insufficient samples ({len(recs)} < {MIN_SUPPORT_GATE}).")
            model_stats["dropped_classes"].append({
                "class": cls_name,
                "usable_count": len(recs),
                "reason": f"Under minimum support threshold (usable={len(recs)} < {MIN_SUPPORT_GATE})"
            })
        else:
            retained_classes.append(cls_name)
            final_records.extend(recs)

    model_stats["retained_classes"] = retained_classes

    # Group-aware 70/15/15 train/val/test split by phash_cluster
    cluster_groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for r in final_records:
        cluster_groups[(r["class_name"], r["phash_cluster"])].append(r)

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

    print(f"Wrote v2 manifest: {manifest_csv} ({len(all_split_records)} rows)")
    return model_stats

def main():
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
            stats = process_model_v2(y_path)
            all_stats.append(stats)

    summary_file = MANIFESTS_DIR / "manifests_v2_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_stats, f, indent=2)
    print(f"\nManifests v2 generation complete! Summary saved to {summary_file}")

if __name__ == "__main__":
    main()
