"""Precision, Recall and F1-Score Comparison for MedNourish Models.
================================================================
Plots:
  Figure 1: Macro and Weighted Precision, Recall, and F1 across:
    (a) Tabular Models (XGBoost and LightGBM for with_labs, no_labs, symptom_lifestyle_only)
    (b) Vision v2 Models (7 MobileNetV2 classifiers)
  Figure 2: Detailed Per-Class Diagnostic Heatmaps:
    (a) Per-class Precision, Recall, F1 for symptom_lifestyle_only (XGB & LGB),
        highlighting the rare deficiency classes Night_Blindness and Scurvy.
    (b) Per-class F1 heatmap across all 7 Vision v2 anatomical models.

Verification:
  - Exact re-derivation of P/R/F1 from raw confusion matrices.
  - Strict assertion: computed macro-F1 == card macro-F1 within 0.001.

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
CACHE_DIR = OUTPUT_DIR / "cache"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_json(p: Path) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# %%
# Metric computation from Confusion Matrix


def metrics_from_cm(cm: List[List[int]]) -> Dict[str, Any]:
    arr = np.array(cm, dtype=np.float64)
    n_classes = arr.shape[0]
    precisions = []
    recalls = []
    f1s = []
    supports = []

    for i in range(n_classes):
        tp = arr[i, i]
        fp = np.sum(arr[:, i]) - tp
        fn = np.sum(arr[i, :]) - tp
        support = np.sum(arr[i, :])

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)
        supports.append(support)

    total_sup = sum(supports)
    macro_p = float(np.mean(precisions))
    macro_r = float(np.mean(recalls))
    macro_f1 = float(np.mean(f1s))

    weighted_p = float(sum(p * s for p, s in zip(precisions, supports)) / total_sup) if total_sup > 0 else 0.0
    weighted_r = float(sum(r * s for r, s in zip(recalls, supports)) / total_sup) if total_sup > 0 else 0.0
    weighted_f1 = float(sum(f * s for f, s in zip(f1s, supports)) / total_sup) if total_sup > 0 else 0.0

    return {
        "per_class_precision": precisions,
        "per_class_recall": recalls,
        "per_class_f1": f1s,
        "supports": supports,
        "macro_p": macro_p,
        "macro_r": macro_r,
        "macro_f1": macro_f1,
        "weighted_p": weighted_p,
        "weighted_r": weighted_r,
        "weighted_f1": weighted_f1,
    }


# %%
# Load and verify tabular models
tabular_models = {}
profiles = ["with_labs", "no_labs", "symptom_lifestyle_only"]

for p in profiles:
    p_path = ROOT / "ml" / "artifacts" / "tabular" / f"model_card_main_{p}.json"
    if not p_path.exists():
        continue
    data = load_json(p_path)
    classes = data.get("target_classes", [])

    for algo in ["xgboost", "lightgbm"]:
        metrics = data["held_out_test_metrics"][algo]
        cm = metrics["confusion_matrix"]
        card_f1 = metrics["test_macro_f1"]
        computed = metrics_from_cm(cm)

        # Assert macro-F1 matches card within 0.001
        diff = abs(computed["macro_f1"] - card_f1)
        assert diff <= 0.001, f"Mismatch in Tabular {p} {algo}: card={card_f1}, computed={computed['macro_f1']}"

        algo_short = "XGB" if algo == "xgboost" else "LGB"
        key = f"Tabular_{algo_short}_{p}"
        tabular_models[key] = {
            "profile": p,
            "algo": algo,
            "classes": classes,
            "card_f1": card_f1,
            "computed": computed,
            "cm": cm,
            "is_leakage": (p == "with_labs"),
        }

# %%
# Load and verify vision models
vision_models = {}
regions = ["combined", "eyes", "hair", "lips", "nails", "skin", "tongue"]

for r in regions:
    r_path = ROOT / "ml" / "artifacts" / "v2" / "vision" / f"model_card_{r}.json"
    if not r_path.exists():
        continue
    data = load_json(r_path)
    em = data["evaluation_metrics"]
    cm = em["confusion_matrix"]
    classes = data["classes"]
    card_f1 = em["test_macro_f1"]
    computed = metrics_from_cm(cm)

    # Assert macro-F1 matches card within 0.001
    diff = abs(computed["macro_f1"] - card_f1)
    assert diff <= 0.001, f"Mismatch in Vision {r}: card={card_f1}, computed={computed['macro_f1']}"

    vision_models[r] = {
        "classes": classes,
        "card_f1": card_f1,
        "computed": computed,
        "cm": cm,
        "shortcut": data.get("source_shortcut_check", {}).get("shortcut_detected", False),
        "small_sample": data.get("has_small_sample_classes", False) or (em.get("test_set_size", 0) < 100),
    }

print(f"[Verification] Successfully verified exact Macro-F1 matches across {len(tabular_models)} tabular and {len(vision_models)} vision models.")

# %%
# Palette
C_P = "#0072B2"  # Blue for Precision
C_R = "#E69F00"  # Orange for Recall
C_F1 = "#009E73" # Green for F1

# --------------------------------------------------------------------------
# FIGURE 1: Macro & Weighted P/R/F1 Comparison
# --------------------------------------------------------------------------
fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 11), dpi=DPI)
fig1.subplots_adjust(hspace=0.45, bottom=0.10)

# (a) Tabular Models
tab_keys = list(tabular_models.keys())
tab_labels = [
    "XGB with_labs\n(leakage)",
    "LGB with_labs\n(leakage)",
    "XGB no_labs\n(diet RDA)",
    "LGB no_labs\n(diet RDA)",
    "XGB symptom\n(realistic)",
    "LGB symptom\n(realistic)",
]
x1 = np.arange(len(tab_keys))
w = 0.25

macro_p = [tabular_models[k]["computed"]["macro_p"] * 100 for k in tab_keys]
macro_r = [tabular_models[k]["computed"]["macro_r"] * 100 for k in tab_keys]
macro_f1 = [tabular_models[k]["computed"]["macro_f1"] * 100 for k in tab_keys]

b1 = ax1.bar(x1 - w, macro_p, w, label="Macro Precision", color=C_P, edgecolor="black")
b2 = ax1.bar(x1, macro_r, w, label="Macro Recall", color=C_R, edgecolor="black")
b3 = ax1.bar(x1 + w, macro_f1, w, label="Macro F1-Score", color=C_F1, edgecolor="black")

# Mark leakage bars with hatching
b1[0].set_hatch("//")
b2[0].set_hatch("//")
b3[0].set_hatch("//")
b1[1].set_hatch("//")
b2[1].set_hatch("//")
b3[1].set_hatch("//")

for bar in list(b1) + list(b2) + list(b3):
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width() / 2, h + 1, f"{h:.1f}%", ha="center", va="bottom", fontsize=7)

ax1.set_ylabel("Score (%)", fontsize=10, fontweight="bold")
ax1.set_title("(a) Tabular Models: Macro-Averaged Precision, Recall, and F1-Score", fontsize=11, fontweight="bold")
ax1.set_xticks(x1)
ax1.set_xticklabels(tab_labels, fontsize=8.5)
ax1.set_ylim(0, 115)
ax1.legend(loc="lower left", fontsize=8.5)
ax1.grid(axis="y", linestyle=":", alpha=0.6)

# (b) Vision v2 Models
vis_keys = list(vision_models.keys())
vis_labels = [k.capitalize() for k in vis_keys]
x2 = np.arange(len(vis_keys))

vis_p = [vision_models[k]["computed"]["macro_p"] * 100 for k in vis_keys]
vis_r = [vision_models[k]["computed"]["macro_r"] * 100 for k in vis_keys]
vis_f1 = [vision_models[k]["computed"]["macro_f1"] * 100 for k in vis_keys]

vb1 = ax2.bar(x2 - w, vis_p, w, label="Macro Precision", color=C_P, edgecolor="black")
vb2 = ax2.bar(x2, vis_r, w, label="Macro Recall", color=C_R, edgecolor="black")
vb3 = ax2.bar(x2 + w, vis_f1, w, label="Macro F1-Score", color=C_F1, edgecolor="black")

for i, k in enumerate(vis_keys):
    if vision_models[k]["shortcut"]:
        vb1[i].set_hatch("//")
        vb2[i].set_hatch("//")
        vb3[i].set_hatch("//")

for bar in list(vb1) + list(vb2) + list(vb3):
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width() / 2, h + 1, f"{h:.1f}%", ha="center", va="bottom", fontsize=7)

ax2.set_ylabel("Score (%)", fontsize=10, fontweight="bold")
ax2.set_title("(b) Vision v2 Models: Macro-Averaged Precision, Recall, and F1-Score", fontsize=11, fontweight="bold")
ax2.set_xticks(x2)
ax2.set_xticklabels(vis_labels, fontsize=9)
ax2.set_ylim(0, 115)
ax2.legend(loc="upper right", fontsize=8.5)
ax2.grid(axis="y", linestyle=":", alpha=0.6)

fig1.text(0.5, 0.02, FOOTNOTE, ha="center", fontsize=8.5, style="italic", color="#333333")

fig1_png = OUTPUT_DIR / "02_precision_recall_f1_comparison.png"
fig1_csv = OUTPUT_DIR / "02_precision_recall_f1_comparison.csv"
fig1.savefig(fig1_png, dpi=DPI, bbox_inches="tight")
print(f"[Saved Figure 1] {fig1_png}")

# CSV export
with open(fig1_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["model_family", "model_id", "macro_precision_pct", "macro_recall_pct", "macro_f1_pct", "weighted_f1_pct", "is_leakage", "shortcut_detected"])
    for k in tab_keys:
        m = tabular_models[k]
        writer.writerow(["Tabular", k, f"{m['computed']['macro_p']*100:.2f}", f"{m['computed']['macro_r']*100:.2f}", f"{m['computed']['macro_f1']*100:.2f}", f"{m['computed']['weighted_f1']*100:.2f}", m["is_leakage"], False])
    for k in vis_keys:
        m = vision_models[k]
        writer.writerow(["Vision v2", k, f"{m['computed']['macro_p']*100:.2f}", f"{m['computed']['macro_r']*100:.2f}", f"{m['computed']['macro_f1']*100:.2f}", f"{m['computed']['weighted_f1']*100:.2f}", False, m["shortcut"]])
print(f"[Saved CSV 1] {fig1_csv}")


# --------------------------------------------------------------------------
# FIGURE 2: Per-Class Diagnostic Heatmaps
# --------------------------------------------------------------------------
fig2, (ax_h1, ax_h2) = plt.subplots(1, 2, figsize=(16, 7), dpi=DPI)
fig2.subplots_adjust(wspace=0.35, bottom=0.15)

# (a) Per-class P/R/F1 for Tabular symptom_lifestyle_only
xgb_sym = tabular_models["Tabular_XGB_symptom_lifestyle_only"]
lgb_sym = tabular_models["Tabular_LGB_symptom_lifestyle_only"]
classes_sym = xgb_sym["classes"]

# Matrix: rows = [XGB P, XGB R, XGB F1, LGB P, LGB R, LGB F1], cols = 5 classes
heat_data = np.array([
    xgb_sym["computed"]["per_class_precision"],
    xgb_sym["computed"]["per_class_recall"],
    xgb_sym["computed"]["per_class_f1"],
    lgb_sym["computed"]["per_class_precision"],
    lgb_sym["computed"]["per_class_recall"],
    lgb_sym["computed"]["per_class_f1"],
]) * 100

im1 = ax_h1.imshow(heat_data, cmap="YlGnBu", aspect="auto", vmin=0, vmax=100)
row_labels = ["XGB Prec", "XGB Rec", "XGB F1", "LGB Prec", "LGB Rec", "LGB F1"]
ax_h1.set_yticks(np.arange(len(row_labels)))
ax_h1.set_yticklabels(row_labels, fontsize=9)
ax_h1.set_xticks(np.arange(len(classes_sym)))

# Highlight rare classes Night_Blindness and Scurvy with red tick labels
class_display = []
for c in classes_sym:
    if c in ["Night_Blindness", "Scurvy"]:
        class_display.append(f"{c}*\n(RARE)")
    else:
        class_display.append(c)
ax_h1.set_xticklabels(class_display, fontsize=8.5, rotation=25, ha="right")

for i in range(heat_data.shape[0]):
    for j in range(heat_data.shape[1]):
        val = heat_data[i, j]
        color = "white" if val > 60 else "black"
        ax_h1.text(j, i, f"{val:.1f}%", ha="center", va="center", color=color, fontsize=8, fontweight="bold")

# Draw red rectangle around rare classes columns
ax_h1.set_title("(a) Tabular (Symptom-Only): Per-Class Metrics (*Rare Classes)", fontsize=10.5, fontweight="bold")
plt.colorbar(im1, ax=ax_h1, fraction=0.046, pad=0.04, label="Metric Score (%)")

# (b) Per-class F1 across 7 Vision Models
# We'll create a table of [Model x Classes]
vis_regions_ordered = ["combined", "eyes", "hair", "lips", "nails", "skin", "tongue"]
vis_rows = []
vis_row_labels = []

# Collect all unique class names across vision models
all_vis_classes = []
for r in vis_regions_ordered:
    for c in vision_models[r]["classes"]:
        if c not in all_vis_classes:
            all_vis_classes.append(c)

vis_f1_matrix = np.full((len(vis_regions_ordered), len(all_vis_classes)), np.nan)

for i, r in enumerate(vis_regions_ordered):
    m = vision_models[r]
    vis_row_labels.append(r.capitalize())
    for j, c in enumerate(all_vis_classes):
        if c in m["classes"]:
            idx = m["classes"].index(c)
            vis_f1_matrix[i, j] = m["computed"]["per_class_f1"][idx] * 100

im2 = ax_h2.imshow(vis_f1_matrix, cmap="Purples", aspect="auto", vmin=0, vmax=100)
ax_h2.set_yticks(np.arange(len(vis_row_labels)))
ax_h2.set_yticklabels(vis_row_labels, fontsize=9)
ax_h2.set_xticks(np.arange(len(all_vis_classes)))
clean_cls_names = [c.replace("Vitamin_", "Vit_").replace("_Deficiency", "_Def") for c in all_vis_classes]
ax_h2.set_xticklabels(clean_cls_names, fontsize=7.5, rotation=45, ha="right")

for i in range(vis_f1_matrix.shape[0]):
    for j in range(vis_f1_matrix.shape[1]):
        val = vis_f1_matrix[i, j]
        if not np.isnan(val):
            color = "white" if val > 55 else "black"
            ax_h2.text(j, i, f"{val:.0f}", ha="center", va="center", color=color, fontsize=6.5)

ax_h2.set_title("(b) Vision Models: Per-Class F1-Scores (%)", fontsize=10.5, fontweight="bold")
plt.colorbar(im2, ax=ax_h2, fraction=0.046, pad=0.04, label="Per-Class F1 (%)")

fig2.text(0.5, 0.02, FOOTNOTE, ha="center", fontsize=8.5, style="italic", color="#333333")

fig2_png = OUTPUT_DIR / "02_per_class_heatmaps.png"
fig2_csv = OUTPUT_DIR / "02_per_class_heatmaps.csv"
fig2.savefig(fig2_png, dpi=DPI, bbox_inches="tight")
print(f"[Saved Figure 2] {fig2_png}")

# Heatmap CSV
with open(fig2_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["model_family", "model", "class_name", "metric", "value_pct"])
    for j, c in enumerate(classes_sym):
        for i, row_name in enumerate(row_labels):
            writer.writerow(["Tabular symptom_only", "symptom_lifestyle_only", c, row_name, f"{heat_data[i, j]:.2f}"])
    for i, r in enumerate(vis_regions_ordered):
        for j, c in enumerate(all_vis_classes):
            val = vis_f1_matrix[i, j]
            if not np.isnan(val):
                writer.writerow(["Vision v2", r, c, "F1-Score", f"{val:.2f}"])
print(f"[Saved CSV 2] {fig2_csv}")

if SHOW:
    plt.show()
