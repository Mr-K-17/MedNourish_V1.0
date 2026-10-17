"""Model Accuracy Comparison for MedNourish Tabular and Vision Classifiers.
========================================================================
Plots:
  (a) Tabular Models: XGBoost vs LightGBM across with_labs, no_labs, and
      symptom_lifestyle_only feature sets, compared against the majority-class baseline.
  (b) Vision v2 Models: MobileNetV2 test accuracy across 7 anatomical regions
      with 95% bootstrap confidence intervals vs color-histogram baseline.
  (c) Overall Model Ranking: Ranked horizontal bar chart across all 13 models.
  (d) Vision v1 vs v2 Comparison: Performance progression from legacy to v2.

Data Sources:
  - Tabular model cards: ml/artifacts/tabular/model_card_main_*.json
  - Vision v2 model cards: ml/artifacts/v2/vision/model_card_*.json
  - Vision v1 model cards: ml/artifacts/vision/model_card_*.json
  - Dataset manifest files: ml/artifacts/manifests/*_manifest.csv
"""

# %%
import sys
sys.dont_write_bytecode = True

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

# %%
# Load Model Cards


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_tabular_data() -> Dict[str, Any]:
    profiles = ["with_labs", "no_labs", "symptom_lifestyle_only"]
    tab_data = {}
    for p in profiles:
        card_path = ROOT / "ml" / "artifacts" / "tabular" / f"model_card_main_{p}.json"
        if not card_path.exists():
            print(f"Warning: Tabular card missing: {card_path}")
            continue
        d = load_json(card_path)
        tab_data[p] = {
            "xgb_acc": d["held_out_test_metrics"]["xgboost"]["test_accuracy"],
            "lgb_acc": d["held_out_test_metrics"]["lightgbm"]["test_accuracy"],
            "test_size": d.get("test_size", 800),
            "leakage": (p == "with_labs"),
        }
    return tab_data


def get_vision_v2_data() -> Dict[str, Any]:
    regions = ["combined", "eyes", "hair", "lips", "nails", "skin", "tongue"]
    vis_data = {}
    for r in regions:
        card_path = ROOT / "ml" / "artifacts" / "v2" / "vision" / f"model_card_{r}.json"
        if not card_path.exists():
            print(f"Warning: Vision v2 card missing: {card_path}")
            continue
        d = load_json(card_path)
        em = d.get("evaluation_metrics", {})
        sc = d.get("source_shortcut_check", {})
        ci = em.get("bootstrap_95_ci_accuracy", [em.get("test_accuracy", 0.0), em.get("test_accuracy", 0.0)])
        vis_data[r] = {
            "accuracy": em.get("test_accuracy", 0.0),
            "ci_low": ci[0],
            "ci_high": ci[1],
            "baseline_acc": sc.get("test_accuracy", 0.0),
            "shortcut_detected": sc.get("shortcut_detected", False),
            "small_sample": d.get("has_small_sample_classes", False) or (em.get("test_set_size", 0) < 100),
            "test_set_size": em.get("test_set_size", 0),
        }
    return vis_data


def get_vision_v1_data() -> Dict[str, float]:
    v1_dir = ROOT / "ml" / "artifacts" / "vision"
    v1_data = {}
    if not v1_dir.exists():
        return v1_data
    for p in v1_dir.glob("model_card_*.json"):
        reg = p.stem.replace("model_card_", "")
        d = load_json(p)
        acc = d.get("evaluation_metrics", {}).get("test_accuracy")
        if acc is not None:
            v1_data[reg] = float(acc)
    return v1_data


# %%
# Optional Recomputation Logic
def recompute_tabular() -> Dict[str, Dict[str, float]]:
    cache_file = CACHE_DIR / "recompute_tabular_acc.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Read dataset and re-evaluate
    import xgboost as xgb
    import lightgbm as lgb
    from sklearn.model_selection import train_test_split

    csv_path = Path(r"C:\Users\USER\Desktop\MedNourish\datasets\vitamin_deficiency_disease_dataset_20260123.csv")
    if not csv_path.exists():
        csv_path = ROOT / "datasets" / "vitamin_deficiency_disease_dataset_20260123.csv"
    if not csv_path.exists():
        print("Warning: CSV not found for recompute. Skipping.")
        return {}

    sys.path.insert(0, str(ROOT))
    from ml.data_pipeline import TabularPreprocessor, load_raw_dataset

    fieldnames, records = load_raw_dataset(csv_path)
    labels = [r["disease_diagnosis"] for r in records]
    train_records, test_records = train_test_split(records, test_size=0.20, stratify=labels, random_state=42)

    profiles = ["with_labs", "no_labs", "symptom_lifestyle_only"]
    recomp_res = {}

    for p in profiles:
        card = load_json(ROOT / "ml" / "artifacts" / "tabular" / f"model_card_main_{p}.json")
        features = card["feature_names"]
        prep = TabularPreprocessor(feature_names=features, target_name="disease_diagnosis")
        prep.fit(train_records)
        _, y_test = prep.transform(test_records)
        X_test, _ = prep.transform(test_records)

        # XGBoost
        xgb_model = xgb.XGBClassifier()
        xgb_model.load_model(str(ROOT / "ml" / "artifacts" / "tabular" / f"xgboost_main_{p}.json"))
        preds_xgb = xgb_model.predict(X_test)
        acc_xgb = float(np.mean(preds_xgb == y_test))

        # LightGBM
        lgb_booster = lgb.Booster(model_file=str(ROOT / "ml" / "artifacts" / "tabular" / f"lightgbm_main_{p}.txt"))
        preds_lgb = np.argmax(lgb_booster.predict(X_test), axis=1)
        acc_lgb = float(np.mean(preds_lgb == y_test))

        recomp_res[p] = {"xgb_acc": round(acc_xgb, 4), "lgb_acc": round(acc_lgb, 4)}

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(recomp_res, f, indent=2)
    return recomp_res


# %%
# Execution and Plotting
tab_data = get_tabular_data()
vis_data = get_vision_v2_data()
v1_data = get_vision_v1_data()

if RECOMPUTE:
    print("\n--- Running RECOMPUTE for Tabular Accuracies ---")
    recomputed = recompute_tabular()
    print(f"{'Profile':<25} | {'Metric':<10} | {'Card':<8} | {'Recomputed':<10} | {'Diff':<8}")
    print("-" * 70)
    for p, vals in tab_data.items():
        if p in recomputed:
            for k in ["xgb_acc", "lgb_acc"]:
                diff = abs(vals[k] - recomputed[p][k])
                flag = " >0.5pt" if diff > 0.005 else " OK"
                print(f"{p:<25} | {k:<10} | {vals[k]:<8.4f} | {recomputed[p][k]:<10.4f} | {diff:<8.4f}{flag}")

# Majority baseline: Healthy in test set = 302 / 800 = 0.3775
MAJORITY_BASELINE = 0.3775

# Colorblind friendly palette (Okabe-Ito inspired)
C_BLUE = "#0072B2"
C_VERMILION = "#D55E00"
C_GREEN = "#009E73"
C_ORANGE = "#E69F00"
C_SKY = "#56B4E9"
C_GREY = "#7F7F7F"

fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=DPI)
fig.subplots_adjust(hspace=0.35, wspace=0.25, bottom=0.10)

# --------------------------------------------------------------------------
# Panel A: Tabular Accuracy (Grouped Bar)
# --------------------------------------------------------------------------
ax = axes[0, 0]
profiles = ["with_labs", "no_labs", "symptom_lifestyle_only"]
display_names = [
    "with_labs\n(leakage)",
    "no_labs\n(diet RDA)",
    "symptom_lifestyle\n(realistic)",
]
x = np.arange(len(profiles))
width = 0.32

xgb_vals = [tab_data[p]["xgb_acc"] * 100 for p in profiles]
lgb_vals = [tab_data[p]["lgb_acc"] * 100 for p in profiles]

rects1 = ax.bar(x - width / 2, xgb_vals, width, label="XGBoost", color=C_BLUE, edgecolor="black")
rects2 = ax.bar(x + width / 2, lgb_vals, width, label="LightGBM", color=C_VERMILION, edgecolor="black")

# Add leakage warning text
rects1[0].set_hatch("//")
rects2[0].set_hatch("//")
ax.text(
    0,
    102,
    "labels derived from lab values (leakage)",
    ha="center",
    va="bottom",
    fontsize=8,
    color="darkred",
    fontweight="bold",
)

# Majority baseline
ax.axhline(MAJORITY_BASELINE * 100, color="dimgray", linestyle="--", linewidth=1.5, label=f"Majority Baseline ({MAJORITY_BASELINE*100:.1f}%)")

for bar in rects1:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, yval + 1, f"{yval:.1f}%", ha="center", va="bottom", fontsize=8)
for bar in rects2:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, yval + 1, f"{yval:.1f}%", ha="center", va="bottom", fontsize=8)

ax.set_ylabel("Held-Out Test Accuracy (%)", fontsize=10, fontweight="bold")
ax.set_title("(a) Tabular Models: XGBoost vs LightGBM", fontsize=11, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(display_names, fontsize=9)
ax.set_ylim(0, 115)
ax.legend(loc="lower left", fontsize=8)
ax.grid(axis="y", linestyle=":", alpha=0.6)

# --------------------------------------------------------------------------
# Panel B: Vision v2 Models with 95% Bootstrap CI
# --------------------------------------------------------------------------
ax = axes[0, 1]
vis_regions = list(vis_data.keys())
vis_labels = [r.capitalize() for r in vis_regions]
x_vis = np.arange(len(vis_regions))

accs = [vis_data[r]["accuracy"] * 100 for r in vis_regions]
err_low = [max(0, (vis_data[r]["accuracy"] - vis_data[r]["ci_low"]) * 100) for r in vis_regions]
err_high = [max(0, (vis_data[r]["ci_high"] - vis_data[r]["accuracy"]) * 100) for r in vis_regions]
baselines = [vis_data[r]["baseline_acc"] * 100 for r in vis_regions]

bars_vis = ax.bar(
    x_vis,
    accs,
    yerr=[err_low, err_high],
    capsize=4,
    color=C_GREEN,
    edgecolor="black",
    label="MobileNetV2 (95% CI)",
)
ax.scatter(x_vis, baselines, color="red", marker="D", s=40, zorder=5, label="Color-Hist Baseline")

for i, r in enumerate(vis_regions):
    if vis_data[r]["shortcut_detected"]:
        bars_vis[i].set_hatch("//")
    # Small sample annotation
    if vis_data[r]["small_sample"]:
        ax.text(i, accs[i] + err_high[i] + 2, "small sample", ha="center", va="bottom", fontsize=7, color="brown")
    else:
        ax.text(i, accs[i] + err_high[i] + 2, f"{accs[i]:.1f}%", ha="center", va="bottom", fontsize=8)

ax.set_ylabel("Held-Out Test Accuracy (%)", fontsize=10, fontweight="bold")
ax.set_title("(b) Vision v2 Models: Accuracy with 95% CI vs Baseline", fontsize=11, fontweight="bold")
ax.set_xticks(x_vis)
ax.set_xticklabels(vis_labels, fontsize=9, rotation=20)
ax.set_ylim(0, 115)
ax.legend(loc="upper right", fontsize=8)
ax.grid(axis="y", linestyle=":", alpha=0.6)

# --------------------------------------------------------------------------
# Panel C: Ranked Horizontal Bar Chart of All Models
# --------------------------------------------------------------------------
ax = axes[1, 0]
all_models = []

for p in profiles:
    leak_suffix = " [leakage]" if p == "with_labs" else ""
    all_models.append((f"Tabular XGB ({p}){leak_suffix}", tab_data[p]["xgb_acc"] * 100, p == "with_labs", False))
    all_models.append((f"Tabular LGB ({p}){leak_suffix}", tab_data[p]["lgb_acc"] * 100, p == "with_labs", False))

for r in vis_regions:
    sc = vis_data[r]["shortcut_detected"]
    all_models.append((f"Vision v2 ({r.capitalize()})", vis_data[r]["accuracy"] * 100, False, sc))

all_models.sort(key=lambda t: t[1])
y_pos = np.arange(len(all_models))
names = [m[0] for m in all_models]
scores = [m[1] for m in all_models]
is_leakage = [m[2] for m in all_models]
is_shortcut = [m[3] for m in all_models]

colors = [C_BLUE if "Tabular" in n else C_GREEN for n in names]
bars_all = ax.barh(y_pos, scores, color=colors, edgecolor="black", height=0.65)

for i, (bar, leak, sc) in enumerate(zip(bars_all, is_leakage, is_shortcut)):
    if leak or sc:
        bar.set_hatch("//")
    val = bar.get_width()
    ax.text(val + 1, bar.get_y() + bar.get_height() / 2, f"{val:.1f}%", ha="left", va="center", fontsize=7.5)

ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=8)
ax.set_xlabel("Held-Out Test Accuracy (%)", fontsize=10, fontweight="bold")
ax.set_title("(c) Ranked Model Accuracy (All 13 Models)", fontsize=11, fontweight="bold")
ax.set_xlim(0, 115)
ax.grid(axis="x", linestyle=":", alpha=0.6)

# --------------------------------------------------------------------------
# Panel D: Vision v1 vs v2 Accuracy Comparison
# --------------------------------------------------------------------------
ax = axes[1, 1]
common_regions = [r for r in ["eyes", "hair", "nails", "skin", "tongue", "combined"] if r in vis_data]
x_d = np.arange(len(common_regions))
w_d = 0.35

v1_scores = [v1_data.get(r, 0.0) * 100 for r in common_regions]
v2_scores = [vis_data[r]["accuracy"] * 100 for r in common_regions]

b1 = ax.bar(x_d - w_d / 2, v1_scores, w_d, label="Vision v1 (Legacy)", color=C_GREY, edgecolor="black")
b2 = ax.bar(x_d + w_d / 2, v2_scores, w_d, label="Vision v2 (Current)", color=C_SKY, edgecolor="black")

for bar in b1:
    h = bar.get_height()
    label_txt = f"{h:.1f}%" if h > 0 else "n/a"
    ax.text(bar.get_x() + bar.get_width() / 2, max(h, 2) + 1, label_txt, ha="center", va="bottom", fontsize=7.5)

for bar in b2:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, h + 1, f"{h:.1f}%", ha="center", va="bottom", fontsize=7.5)

ax.set_xticks(x_d)
ax.set_xticklabels([r.capitalize() for r in common_regions], fontsize=9)
ax.set_ylabel("Held-Out Test Accuracy (%)", fontsize=10, fontweight="bold")
ax.set_title("(d) Vision v1 vs v2 Accuracy Progression", fontsize=11, fontweight="bold")
ax.set_ylim(0, 115)
ax.legend(loc="upper right", fontsize=8)
ax.grid(axis="y", linestyle=":", alpha=0.6)

# Footnote
fig.text(0.5, 0.02, FOOTNOTE, ha="center", fontsize=8.5, style="italic", color="#333333")

# Save outputs
fig_png = OUTPUT_DIR / "01_model_accuracy_comparison.png"
fig_csv = OUTPUT_DIR / "01_model_accuracy_comparison.csv"
plt.savefig(fig_png, dpi=DPI, bbox_inches="tight")
print(f"\n[Saved Figure] {fig_png}")

# Write summary CSV
with open(fig_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["model_family", "model_name", "test_accuracy_pct", "ci_95_low", "ci_95_high", "baseline_pct", "is_leakage", "shortcut_detected", "small_sample"])
    for p in profiles:
        writer.writerow(["Tabular XGB", p, f"{tab_data[p]['xgb_acc']*100:.2f}", "", "", f"{MAJORITY_BASELINE*100:.2f}", tab_data[p]["leakage"], False, False])
        writer.writerow(["Tabular LGB", p, f"{tab_data[p]['lgb_acc']*100:.2f}", "", "", f"{MAJORITY_BASELINE*100:.2f}", tab_data[p]["leakage"], False, False])
    for r in vis_regions:
        v = vis_data[r]
        writer.writerow(["Vision v2", r, f"{v['accuracy']*100:.2f}", f"{v['ci_low']*100:.2f}", f"{v['ci_high']*100:.2f}", f"{v['baseline_acc']*100:.2f}", False, v["shortcut_detected"], v["small_sample"]])
print(f"[Saved CSV] {fig_csv}")

# Print summary table
print("\n" + "=" * 65)
print(f"{'Model Name':<32} | {'Accuracy (%)':<14} | {'Baseline / Notes':<15}")
print("=" * 65)
for name, acc, leak, sc in sorted(all_models, key=lambda x: -x[1]):
    note = "Leakage" if leak else ("Shortcut" if sc else "Valid")
    print(f"{name:<32} | {acc:<14.2f} | {note:<15}")
print("=" * 65)

if SHOW:
    plt.show()
