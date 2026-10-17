"""MedScan Computer Vision Performance for MobileNetV2 Models.
============================================================
Plots:
  (a) Accuracy with 95% Bootstrap CI vs Color-Histogram Baseline across 7 anatomical regions.
  (b) CNN Advantage over Baseline in percentage points (highlighting negative/zero advantage in Hair & Nails).
  (c) Test Macro-F1 and Test Set Sample Sizes per model.
  (d) TFLite Float32 Runtime Parity: Max Absolute Difference on log scale with 0.01 gate line & Top-1 Agreement.
  (e) Model Footprint Reduction: Float32 (~8.5 MB) vs Dynamic Range Quantization DRQ (~2.4 MB).
  (f) Quality Gate & Domain Risk Audit Table (Shortcut Flags & Small-Sample Alerts).

Data Sources:
  - Vision v2 model cards: ml/artifacts/v2/vision/model_card_*.json
  - Vision v2 summary: ml/artifacts/v2/vision/vision_v2_summary.json
  - Benchmark records: docs/ML_RESULTS.md
"""

# %%
import sys
sys.dont_write_bytecode = True

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List

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
# Load Vision v2 Data
summary_path = ROOT / "ml" / "artifacts" / "v2" / "vision" / "vision_v2_summary.json"
if summary_path.exists():
    raw_data = load_json(summary_path)
else:
    raw_data = {}
    for r in ["combined", "eyes", "hair", "lips", "nails", "skin", "tongue"]:
        cp = ROOT / "ml" / "artifacts" / "v2" / "vision" / f"model_card_{r}.json"
        if cp.exists():
            raw_data[r] = load_json(cp)

regions = ["combined", "eyes", "hair", "lips", "nails", "skin", "tongue"]
display_names = [r.capitalize() for r in regions]

metrics = []
for r in regions:
    d = raw_data.get(r, {})
    em = d.get("evaluation_metrics", {})
    sc = d.get("source_shortcut_check", {})
    tf = d.get("tflite_verification", {})

    acc = em.get("test_accuracy", 0.0)
    ci = em.get("bootstrap_95_ci_accuracy", [acc, acc])
    base_acc = sc.get("test_accuracy", 0.0)
    advantage = (acc - base_acc) * 100

    metrics.append({
        "region": r,
        "name": r.capitalize(),
        "classes_count": d.get("num_classes", len(d.get("classes", []))),
        "test_samples": em.get("test_set_size", 0),
        "test_accuracy": acc * 100,
        "ci_low": ci[0] * 100,
        "ci_high": ci[1] * 100,
        "baseline_acc": base_acc * 100,
        "advantage_pp": advantage,
        "macro_f1": em.get("test_macro_f1", 0.0),
        "tflite_max_diff": tf.get("max_abs_difference", 1e-5),
        "tflite_agreement": tf.get("top1_agreement_pct", 100.0),
        "size_float32": tf.get("file_size_mb", 8.5),
        "size_drq": tf.get("drq_file_size_mb", 2.4),
        "shortcut_flag": sc.get("shortcut_detected", False) or (base_acc > 0.70),
        "small_sample": d.get("has_small_sample_classes", False) or (em.get("test_set_size", 0) < 100),
    })

# %%
# Palette
C_BLUE = "#0072B2"
C_VERMILION = "#D55E00"
C_GREEN = "#009E73"
C_PURPLE = "#CC79A7"
C_GREY = "#999999"

fig, axes = plt.subplots(3, 2, figsize=(16, 15), dpi=DPI)
fig.subplots_adjust(hspace=0.45, wspace=0.25, bottom=0.08)

x = np.arange(len(regions))

# --------------------------------------------------------------------------
# (a) Accuracy with 95% CI vs Color-Histogram Baseline
# --------------------------------------------------------------------------
ax = axes[0, 0]
accs = [m["test_accuracy"] for m in metrics]
yerr_low = [max(0, m["test_accuracy"] - m["ci_low"]) for m in metrics]
yerr_high = [max(0, m["ci_high"] - m["test_accuracy"]) for m in metrics]
bases = [m["baseline_acc"] for m in metrics]

bars_a = ax.bar(x, accs, yerr=[yerr_low, yerr_high], capsize=4, color=C_BLUE, edgecolor="black", label="MobileNetV2 (95% CI)")
ax.scatter(x, bases, color="red", marker="D", s=45, zorder=5, label="Color-Hist Baseline")

for i, m in enumerate(metrics):
    if m["shortcut_flag"]:
        bars_a[i].set_hatch("//")
    ax.text(i, m["ci_high"] + 2, f"{m['test_accuracy']:.1f}%", ha="center", va="bottom", fontsize=8)

ax.set_ylabel("Accuracy (%)", fontsize=10, fontweight="bold")
ax.set_title("(a) MobileNetV2 Accuracy vs Color-Histogram Baseline", fontsize=11, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(display_names, fontsize=9)
ax.set_ylim(0, 115)
ax.legend(loc="upper right", fontsize=8)
ax.grid(axis="y", linestyle=":", alpha=0.6)

# --------------------------------------------------------------------------
# (b) CNN Advantage over Baseline in Percentage Points
# --------------------------------------------------------------------------
ax = axes[0, 1]
advs = [m["advantage_pp"] for m in metrics]
bar_colors = [C_GREEN if a > 0.5 else (C_VERMILION if a < -0.5 else C_GREY) for a in advs]

bars_b = ax.bar(x, advs, color=bar_colors, edgecolor="black")
ax.axhline(0, color="black", linestyle="-", linewidth=1.0)

for i, m in enumerate(metrics):
    val = m["advantage_pp"]
    offset = 1.0 if val >= 0 else -2.5
    ax.text(i, val + offset, f"{val:+.1f} pp", ha="center", va="bottom" if val >= 0 else "top", fontsize=8, fontweight="bold")

ax.set_ylabel("Advantage (Percentage Points)", fontsize=10, fontweight="bold")
ax.set_title("(b) CNN Advantage over Baseline (Hair/Nails Show ~0 or Negative)", fontsize=11, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(display_names, fontsize=9)
ax.set_ylim(min(advs) - 6, max(advs) + 6)
ax.grid(axis="y", linestyle=":", alpha=0.6)

# --------------------------------------------------------------------------
# (c) Macro-F1 and Test-Set Sizes
# --------------------------------------------------------------------------
ax = axes[1, 0]
f1s = [m["macro_f1"] for m in metrics]
samples = [m["test_samples"] for m in metrics]

bars_c = ax.bar(x, f1s, color=C_PURPLE, edgecolor="black", label="Test Macro-F1")
for i, m in enumerate(metrics):
    h = m["macro_f1"]
    sample_txt = f"N={m['test_samples']}"
    if m["small_sample"]:
        sample_txt += "\n(small sample)"
    ax.text(i, h + 0.02, f"{h:.3f}\n{sample_txt}", ha="center", va="bottom", fontsize=7.5)

ax.set_ylabel("Macro-F1 Score (0-1)", fontsize=10, fontweight="bold")
ax.set_title("(c) Macro-F1 and Held-Out Test Set Sample Sizes", fontsize=11, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(display_names, fontsize=9)
ax.set_ylim(0, 1.25)
ax.grid(axis="y", linestyle=":", alpha=0.6)

# --------------------------------------------------------------------------
# (d) TFLite Float32 Max-Abs-Difference (Log Scale) & Top-1 Agreement
# --------------------------------------------------------------------------
ax = axes[1, 1]
max_diffs = [max(1e-8, m["tflite_max_diff"]) for m in metrics]
w_d = 0.55

bars_d = ax.bar(x, max_diffs, width=w_d, color=C_BLUE, edgecolor="black", label="Max Abs Difference")
ax.axhline(0.01, color="red", linestyle="--", linewidth=1.5, label="Parity Gate Threshold (0.01)")
ax.set_yscale("log")

for i, m in enumerate(metrics):
    diff = m["tflite_max_diff"]
    ax.text(i, diff * 2.0, f"{diff:.1e}\n(100% Top1)", ha="center", va="bottom", fontsize=7)

ax.set_ylabel("Max Abs Difference (Log Scale)", fontsize=10, fontweight="bold")
ax.set_title("(d) TFLite Float32 Parity Verification vs Keras", fontsize=11, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(display_names, fontsize=9)
ax.set_ylim(1e-7, 1e-1)
ax.legend(loc="upper right", fontsize=8)
ax.grid(axis="y", linestyle=":", alpha=0.6)

# --------------------------------------------------------------------------
# (e) Model Size: Float32 vs Dynamic Range Quantization (DRQ)
# --------------------------------------------------------------------------
ax = axes[2, 0]
w_e = 0.35
s_f32 = [m["size_float32"] for m in metrics]
s_drq = [m["size_drq"] for m in metrics]

be1 = ax.bar(x - w_e / 2, s_f32, w_e, label="Float32 TFLite", color=C_GREY, edgecolor="black")
be2 = ax.bar(x + w_e / 2, s_drq, w_e, label="DRQ Quantized", color=C_GREEN, edgecolor="black")

for i in range(len(metrics)):
    reduction = (1 - s_drq[i] / s_f32[i]) * 100
    ax.text(x[i] + w_e / 2, s_drq[i] + 0.3, f"-{reduction:.0f}%", ha="center", va="bottom", fontsize=7.5, color="darkgreen", fontweight="bold")

ax.set_ylabel("Model File Size (MB)", fontsize=10, fontweight="bold")
ax.set_title("(e) Edge Deployment: Model Footprint Reduction via DRQ", fontsize=11, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(display_names, fontsize=9)
ax.set_ylim(0, 11)
ax.legend(loc="upper right", fontsize=8)
ax.grid(axis="y", linestyle=":", alpha=0.6)

# --------------------------------------------------------------------------
# (f) Quality Gate & Domain Risk Audit Table
# --------------------------------------------------------------------------
ax = axes[2, 1]
ax.axis("off")

table_data = []
for m in metrics:
    sc_text = "YES (Hatched)" if m["shortcut_flag"] else "LOW"
    ss_text = "Small Sample" if m["small_sample"] else "Adequate"
    table_data.append([
        m["name"],
        f"{m['classes_count']}",
        f"{m['test_samples']}",
        f"{m['test_accuracy']:.1f}%",
        f"{m['baseline_acc']:.1f}%",
        f"{m['advantage_pp']:+.1f} pp",
        sc_text,
        ss_text,
    ])

col_labels = ["Model", "Classes", "Test N", "Acc", "Baseline", "Advantage", "Shortcut Risk", "Sample Gate"]
table = ax.table(
    cellText=table_data,
    colLabels=col_labels,
    cellLoc="center",
    loc="center",
)
table.auto_set_font_size(False)
table.set_fontsize(8)
table.scale(1.0, 1.6)

# Color header and highlight shortcut rows
for j in range(len(col_labels)):
    table[(0, j)].set_facecolor("#E0E0E0")
    table[(0, j)].set_text_props(fontweight="bold")

for i, m in enumerate(metrics):
    if m["shortcut_flag"]:
        for j in range(len(col_labels)):
            table[(i + 1, j)].set_facecolor("#FFF0F0")

ax.set_title("(f) Quality Gates, Shortcut Risks & Methodological Audit", fontsize=11, fontweight="bold", pad=20)

fig.text(0.5, 0.02, FOOTNOTE, ha="center", fontsize=8.5, style="italic", color="#333333")

fig_png = OUTPUT_DIR / "03_medscan_cv_performance.png"
fig_csv = OUTPUT_DIR / "03_medscan_cv_performance.csv"
fig.savefig(fig_png, dpi=DPI, bbox_inches="tight")
print(f"[Saved Figure] {fig_png}")

# CSV export
with open(fig_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "region", "num_classes", "test_set_size", "test_accuracy_pct", "ci_95_low", "ci_95_high",
        "baseline_accuracy_pct", "advantage_pp", "macro_f1", "tflite_max_abs_diff", "tflite_agreement_pct",
        "float32_size_mb", "drq_size_mb", "shortcut_risk", "sample_gate"
    ])
    for m in metrics:
        writer.writerow([
            m["region"], m["classes_count"], m["test_samples"], f"{m['test_accuracy']:.2f}",
            f"{m['ci_low']:.2f}", f"{m['ci_high']:.2f}", f"{m['baseline_acc']:.2f}",
            f"{m['advantage_pp']:.2f}", f"{m['macro_f1']:.4f}", f"{m['tflite_max_diff']:.2e}",
            f"{m['tflite_agreement']:.2f}", f"{m['size_float32']:.2f}", f"{m['size_drq']:.2f}",
            m["shortcut_flag"], m["small_sample"]
        ])
print(f"[Saved CSV] {fig_csv}")

# Print summary table
print("\n" + "=" * 80)
print(f"{'Region':<12} | {'Acc (%)':<10} | {'Base (%)':<10} | {'Adv (pp)':<10} | {'Macro-F1':<10} | {'Shortcut':<10}")
print("=" * 80)
for m in metrics:
    print(f"{m['name']:<12} | {m['test_accuracy']:<10.2f} | {m['baseline_acc']:<10.2f} | {m['advantage_pp']:<+10.2f} | {m['macro_f1']:<10.4f} | {'FLAGGED' if m['shortcut_flag'] else 'LOW':<10}")
print("=" * 80)

if SHOW:
    plt.show()
