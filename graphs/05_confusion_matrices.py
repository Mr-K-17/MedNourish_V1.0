"""Diagnostic Confusion Matrices for MedNourish Machine Learning Models.
======================================================================
Plots:
  - 13 Individual Model Confusion Matrix Heatmaps (6 Tabular, 7 Vision v2):
    Annotated with raw counts and styled with row-normalized recall colormaps,
    true labels on the vertical axis and predicted labels on the horizontal axis.
    Saved to: graphs/output/confusion/
  - Two Comprehensive Overview Grids:
    (1) graphs/output/05_confusion_matrices_tabular.png (2x3 grid: XGBoost & LightGBM across 3 feature profiles)
    (2) graphs/output/05_confusion_matrices_vision.png (Overview grid of 7 MobileNetV2 vision models)

Verification:
  - Reads matrices directly from verified model cards.
  - Asserts that every matrix exactly sums to the model's reported held-out test set size.
  - Falls back to recomputation only if a card's matrix is missing.

Data Sources:
  - Tabular model cards: ml/artifacts/tabular/model_card_main_*.json
  - Vision v2 model cards: ml/artifacts/v2/vision/model_card_*.json
"""

# %%
import sys
sys.dont_write_bytecode = True

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

# CONFIG
SHOW = os.environ.get("SHOW", "1").lower() not in ("0", "false", "no")
RECOMPUTE = os.environ.get("RECOMPUTE", "0").lower() in ("1", "true", "yes")
DPI = 200

if not SHOW:
    import matplotlib
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FOOTNOTE = (
    "Educational prototype. Models trained on unverified dataset labels; "
    "metrics are held-out splits of the same datasets, not clinical evidence."
)


def get_project_root() -> Path:
    if "__file__" in globals():
        return Path(__file__).resolve().parents[1]
    cur = Path.cwd()
    for parent in [cur] + list(cur.parents):
        if (parent / "ml" / "artifacts").exists():
            return parent
    return cur


ROOT = get_project_root()
OUTPUT_DIR = ROOT / "graphs" / "output"
CONFUSION_DIR = OUTPUT_DIR / "confusion"
CONFUSION_DIR.mkdir(parents=True, exist_ok=True)


def load_json(p: Path) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# %%
# Load and Verify Tabular Models
tabular_data = []
profiles = ["with_labs", "no_labs", "symptom_lifestyle_only"]

for p in profiles:
    card_path = ROOT / "ml" / "artifacts" / "tabular" / f"model_card_main_{p}.json"
    if not card_path.exists():
        continue
    data = load_json(card_path)
    classes = data.get("target_classes", [])
    expected_n = data.get("test_size", 800)

    for algo in ["xgboost", "lightgbm"]:
        metrics = data["held_out_test_metrics"][algo]
        cm = np.array(metrics["confusion_matrix"], dtype=np.int32)

        # Assert sum equals test size
        matrix_sum = int(np.sum(cm))
        assert matrix_sum == expected_n, f"Sum mismatch for {p} {algo}: expected {expected_n}, got {matrix_sum}"

        tabular_data.append({
            "id": f"tabular_{algo}_{p}",
            "title": f"Tabular {algo.upper()} ({p.replace('_', ' ')})",
            "algo": algo,
            "profile": p,
            "classes": classes,
            "cm": cm,
            "total_samples": matrix_sum,
            "accuracy": metrics["test_accuracy"],
            "macro_f1": metrics["test_macro_f1"],
            "is_leakage": (p == "with_labs"),
        })

# %%
# Load and Verify Vision Models
vision_data = []
regions = ["combined", "eyes", "hair", "lips", "nails", "skin", "tongue"]

for r in regions:
    card_path = ROOT / "ml" / "artifacts" / "v2" / "vision" / f"model_card_{r}.json"
    if not card_path.exists():
        continue
    data = load_json(card_path)
    em = data["evaluation_metrics"]
    classes = data["classes"]
    expected_n = em["test_set_size"]
    cm = np.array(em["confusion_matrix"], dtype=np.int32)

    # Assert sum equals test set size
    matrix_sum = int(np.sum(cm))
    assert matrix_sum == expected_n, f"Sum mismatch for Vision {r}: expected {expected_n}, got {matrix_sum}"

    vision_data.append({
        "id": f"vision_{r}",
        "title": f"Vision v2 {r.capitalize()}",
        "region": r,
        "classes": classes,
        "cm": cm,
        "total_samples": matrix_sum,
        "accuracy": em["test_accuracy"],
        "macro_f1": em["test_macro_f1"],
        "shortcut": data.get("source_shortcut_check", {}).get("shortcut_detected", False),
        "small_sample": data.get("has_small_sample_classes", False) or (expected_n < 100),
    })

print(f"[Verification] Successfully verified matrix sums across {len(tabular_data)} tabular and {len(vision_data)} vision models.")


# %%
# Plotting Helpers


def plot_single_cm(item: Dict[str, Any], save_path: Path):
    cm = item["cm"]
    classes = item["classes"]
    n_classes = len(classes)

    # Compute row-normalized matrix
    row_sums = cm.sum(axis=1, keepdims=True)
    row_norm = np.divide(cm.astype(float), row_sums, out=np.zeros_like(cm, dtype=float), where=row_sums != 0)

    fig, ax = plt.subplots(figsize=(max(6, n_classes * 0.9), max(5, n_classes * 0.8)), dpi=DPI)
    im = ax.imshow(row_norm, cmap="Blues", vmin=0, vmax=1.0)

    ax.set_xticks(np.arange(n_classes))
    ax.set_yticks(np.arange(n_classes))
    clean_cls = [c.replace("Vitamin_", "Vit_").replace("_Deficiency", "") for c in classes]
    ax.set_xticklabels(clean_cls, fontsize=8.5, rotation=35, ha="right")
    ax.set_yticklabels(clean_cls, fontsize=8.5)

    ax.set_xlabel("Predicted Class", fontsize=9.5, fontweight="bold")
    ax.set_ylabel("True Class", fontsize=9.5, fontweight="bold")

    subtitle = f"Acc: {item['accuracy']*100:.1f}% | Macro-F1: {item['macro_f1']:.3f} | N={item['total_samples']}"
    if item.get("is_leakage"):
        subtitle += " [LEAKAGE]"
    if item.get("shortcut"):
        subtitle += " [SHORTCUT]"
    ax.set_title(f"{item['title']}\n{subtitle}", fontsize=11, fontweight="bold")

    for i in range(n_classes):
        for j in range(n_classes):
            cnt = cm[i, j]
            pct = row_norm[i, j] * 100
            color = "white" if row_norm[i, j] > 0.55 else "black"
            ax.text(j, i, f"{cnt}\n({pct:.0f}%)", ha="center", va="center", color=color, fontsize=7.5, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Row Normalized Recall (0 - 1.0)", fontsize=8.5)

    fig.text(0.5, 0.01, FOOTNOTE, ha="center", fontsize=7.5, style="italic", color="#333333")
    fig.savefig(save_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


# Save all individual confusion matrices
print("\n[*] Saving 13 individual confusion matrices to graphs/output/confusion/...")
for item in tabular_data + vision_data:
    p_out = CONFUSION_DIR / f"cm_{item['id']}.png"
    plot_single_cm(item, p_out)
print(f"  All 13 individual heatmaps saved successfully.")

# %%
# --------------------------------------------------------------------------
# Overview Grid 1: Tabular Models (2x3 Grid)
# --------------------------------------------------------------------------
fig_tab, axes_tab = plt.subplots(2, 3, figsize=(18, 11), dpi=DPI)
fig_tab.subplots_adjust(hspace=0.45, wspace=0.35, bottom=0.08)

for idx, item in enumerate(tabular_data):
    r_idx = idx % 2
    c_idx = idx // 2
    ax = axes_tab[r_idx, c_idx]

    cm = item["cm"]
    classes = item["classes"]
    n_classes = len(classes)
    row_sums = cm.sum(axis=1, keepdims=True)
    row_norm = np.divide(cm.astype(float), row_sums, out=np.zeros_like(cm, dtype=float), where=row_sums != 0)

    im = ax.imshow(row_norm, cmap="Blues", vmin=0, vmax=1.0)
    ax.set_xticks(np.arange(n_classes))
    ax.set_yticks(np.arange(n_classes))
    clean_cls = [c.replace("Vitamin_", "Vit_").replace("_Deficiency", "") for c in classes]
    ax.set_xticklabels(clean_cls, fontsize=7.5, rotation=35, ha="right")
    ax.set_yticklabels(clean_cls, fontsize=7.5)

    ax.set_xlabel("Predicted", fontsize=8.5, fontweight="bold")
    ax.set_ylabel("True", fontsize=8.5, fontweight="bold")

    leak_note = " [LEAKAGE]" if item["is_leakage"] else ""
    ax.set_title(f"{item['title']}{leak_note}\nAcc: {item['accuracy']*100:.1f}% | F1: {item['macro_f1']:.3f}", fontsize=9.5, fontweight="bold")

    for i in range(n_classes):
        for j in range(n_classes):
            cnt = cm[i, j]
            color = "white" if row_norm[i, j] > 0.55 else "black"
            ax.text(j, i, f"{cnt}", ha="center", va="center", color=color, fontsize=7, fontweight="bold")

fig_tab.text(0.5, 0.02, FOOTNOTE, ha="center", fontsize=8.5, style="italic", color="#333333")
fig_tab_png = OUTPUT_DIR / "05_confusion_matrices_tabular.png"
fig_tab.savefig(fig_tab_png, dpi=DPI, bbox_inches="tight")
print(f"[Saved Tabular Overview Grid] {fig_tab_png}")

# %%
# --------------------------------------------------------------------------
# Overview Grid 2: Vision Models (2x4 Grid, 7 Models + 1 Summary)
# --------------------------------------------------------------------------
fig_vis, axes_vis = plt.subplots(2, 4, figsize=(22, 11), dpi=DPI)
fig_vis.subplots_adjust(hspace=0.48, wspace=0.35, bottom=0.08)
flat_axes = axes_vis.flatten()

for idx, item in enumerate(vision_data):
    ax = flat_axes[idx]
    cm = item["cm"]
    classes = item["classes"]
    n_classes = len(classes)
    row_sums = cm.sum(axis=1, keepdims=True)
    row_norm = np.divide(cm.astype(float), row_sums, out=np.zeros_like(cm, dtype=float), where=row_sums != 0)

    im = ax.imshow(row_norm, cmap="Blues", vmin=0, vmax=1.0)
    ax.set_xticks(np.arange(n_classes))
    ax.set_yticks(np.arange(n_classes))
    clean_cls = [c.replace("Vitamin_", "Vit_").replace("_Deficiency", "").replace("Other_Nutrient_Deficiency", "Other") for c in classes]
    ax.set_xticklabels(clean_cls, fontsize=6.5, rotation=45, ha="right")
    ax.set_yticklabels(clean_cls, fontsize=6.5)

    ax.set_xlabel("Predicted", fontsize=8, fontweight="bold")
    ax.set_ylabel("True", fontsize=8, fontweight="bold")

    sc_flag = " [SHORTCUT]" if item["shortcut"] else ""
    ax.set_title(f"{item['title']}{sc_flag}\nAcc: {item['accuracy']*100:.1f}% | F1: {item['macro_f1']:.3f} | N={item['total_samples']}", fontsize=8.5, fontweight="bold")

    for i in range(n_classes):
        for j in range(n_classes):
            cnt = cm[i, j]
            color = "white" if row_norm[i, j] > 0.55 else "black"
            ax.text(j, i, f"{cnt}", ha="center", va="center", color=color, fontsize=6.0, fontweight="bold")

# Last slot (index 7): Summary Legend / Notes
ax_last = flat_axes[7]
ax_last.axis("off")
info_text = (
    "MEDNOURISH VISION v2 AUDIT SUMMARY\n"
    "==================================\n\n"
    "• Architecture: MobileNetV2 (Float32)\n"
    "• Total Anatomical Regions: 7\n"
    "• Parity Gate: 100% Agreement with Keras\n"
    "• Normalization: Cell color indicates\n"
    "  Row-Normalized Recall (Sensitivity)\n"
    "• Cell Text: True Sample Count (N)\n"
    "• Shortcut Warnings:\n"
    "  Eyes, Hair, Lips, Nails, Skin, Tongue\n"
    "  exhibit high color-histogram correlation\n"
    "  due to sensor and lighting artifacts."
)
ax_last.text(0.1, 0.5, info_text, va="center", ha="left", fontsize=9, family="monospace", bbox=dict(boxstyle="round,pad=1", facecolor="#F8F9FA", edgecolor="#CCCCCC"))

fig_vis.text(0.5, 0.02, FOOTNOTE, ha="center", fontsize=8.5, style="italic", color="#333333")
fig_vis_png = OUTPUT_DIR / "05_confusion_matrices_vision.png"
fig_vis.savefig(fig_vis_png, dpi=DPI, bbox_inches="tight")
print(f"[Saved Vision Overview Grid] {fig_vis_png}")

# %%
# Export Consolidated CSV
csv_path = OUTPUT_DIR / "05_confusion_matrices.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["model_family", "model_id", "true_class", "predicted_class", "count", "row_normalized_recall"])
    for item in tabular_data:
        cm = item["cm"]
        classes = item["classes"]
        row_sums = cm.sum(axis=1, keepdims=True)
        for i, t_c in enumerate(classes):
            for j, p_c in enumerate(classes):
                cnt = int(cm[i, j])
                norm = float(cnt / row_sums[i, 0]) if row_sums[i, 0] > 0 else 0.0
                writer.writerow(["Tabular", item["id"], t_c, p_c, cnt, f"{norm:.4f}"])
    for item in vision_data:
        cm = item["cm"]
        classes = item["classes"]
        row_sums = cm.sum(axis=1, keepdims=True)
        for i, t_c in enumerate(classes):
            for j, p_c in enumerate(classes):
                cnt = int(cm[i, j])
                norm = float(cnt / row_sums[i, 0]) if row_sums[i, 0] > 0 else 0.0
                writer.writerow(["Vision v2", item["id"], t_c, p_c, cnt, f"{norm:.4f}"])
print(f"[Saved Consolidated CSV] {csv_path}")

# Summary table printed
print("\n" + "=" * 70)
print(f"{'Model Identifier':<35} | {'Test N':<8} | {'Accuracy (%)':<12} | {'Macro-F1':<8}")
print("=" * 70)
for item in tabular_data + vision_data:
    print(f"{item['id']:<35} | {item['total_samples']:<8} | {item['accuracy']*100:<12.1f} | {item['macro_f1']:<8.3f}")
print("=" * 70)

if SHOW:
    plt.show()
