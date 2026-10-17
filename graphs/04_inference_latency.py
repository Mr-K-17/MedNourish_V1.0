"""Prediction Time and Inference Latency Benchmarks for MedNourish Models.
========================================================================
Measures real live latency using time.perf_counter on the current machine:
  (a) Tabular Models: XGBoost and LightGBM single-row (N=1) and batch (N=100) prediction.
      (10 warm-up iterations, 200 timed iterations).
  (b) Vision Models: Image preprocessing (letterbox resize_with_pad + scaling) and
      inference across Keras, TFLite Float32, and TFLite DRQ for a 224x224x3 image.
      (5 warm-up iterations, 50 timed iterations, fixed thread count = 4).
  (c) Latency distribution: Median, p5, p95 (error bars = p5..p95).
  (d) Stacked bar chart: Image preprocessing time + Model inference time.

Memory & Safety:
  - Loads models one at a time, frees memory and executes garbage collection between runs.
  - Zero server processes launched.

Outputs:
  - graphs/output/04_inference_latency.png
  - graphs/output/04_inference_latency.csv (Summary table)
  - graphs/output/latency_results.csv (All raw timing iterations)
"""

# %%
import sys
sys.dont_write_bytecode = True

import csv
import gc
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Dict, List, Optional, Tuple

# CONFIG
SHOW = os.environ.get("SHOW", "1").lower() not in ("0", "false", "no")
RECOMPUTE = os.environ.get("RECOMPUTE", "0").lower() in ("1", "true", "yes")
DPI = 200
NUM_THREADS = 4

if not SHOW:
    import matplotlib
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

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
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# System Metadata
SYS_INFO = (
    f"Machine: {platform.machine()} | CPU: {platform.processor() or 'x86_64'} ({os.cpu_count()} logical cores) | "
    f"OS: {platform.system()} {platform.release()} | ThreadPool: {NUM_THREADS} threads\n"
    f"Note: Inference latency results are hardware-dependent and measured locally via time.perf_counter()."
)


# %%
# Helpers to find models


def find_vision_model(region: str, kind: str) -> Optional[Path]:
    vis_dir = ROOT / "ml" / "artifacts" / "v2" / "vision"
    if kind == "keras":
        patterns = [f"{region}_model.keras", f"{region}.keras", f"*{region}*.keras"]
    elif kind == "tflite_f32":
        patterns = [f"{region}_float32.tflite", f"{region}_model_float32.tflite", f"*{region}*float32*.tflite"]
    elif kind == "tflite_drq":
        patterns = [f"{region}_drq.tflite", f"{region}_model_drq.tflite", f"*{region}*drq*.tflite"]
    else:
        return None

    for pat in patterns:
        matches = list(vis_dir.glob(pat))
        if matches:
            return matches[0]
    return None


# %%
# Synthetic Inputs for Latency Testing


def generate_tabular_input(feature_count: int, batch_size: int = 1) -> np.ndarray:
    np.random.seed(42)
    return np.random.randn(batch_size, feature_count).astype(np.float32)


def generate_raw_image() -> Image.Image:
    # 640x480 RGB test image
    np.random.seed(42)
    arr = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    return Image.fromarray(arr)


def preprocess_image(img: Image.Image, target_size=(224, 224)) -> np.ndarray:
    w, h = img.size
    target_h, target_w = target_size
    scale = min(target_h / h, target_w / w)
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    resized = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    padded = Image.new("RGB", (target_w, target_h), (0, 0, 0))
    top = (target_h - new_h) // 2
    left = (target_w - new_w) // 2
    padded.paste(resized, (left, top))
    arr = np.array(padded, dtype=np.float32)
    return (arr / 127.5) - 1.0


# %%
# Benchmark Execution
raw_timing_records = []
summary_records = []

# --------------------------------------------------------------------------
# 1. Benchmark Tabular Models (XGBoost & LightGBM)
# --------------------------------------------------------------------------
import xgboost as xgb
import lightgbm as lgb

print("\n[*] Benchmarking Tabular Models (10 warm-up, 200 timed runs)...")
tab_profiles = ["symptom_lifestyle_only", "no_labs", "with_labs"]

for p in tab_profiles:
    card_path = ROOT / "ml" / "artifacts" / "tabular" / f"model_card_main_{p}.json"
    if not card_path.exists():
        continue
    with open(card_path, "r", encoding="utf-8") as f:
        card = json.load(f)
    n_features = card.get("feature_count", 18)

    # 1.1 XGBoost
    xgb_path = ROOT / "ml" / "artifacts" / "tabular" / f"xgboost_main_{p}.json"
    if xgb_path.exists():
        clf_xgb = xgb.XGBClassifier()
        clf_xgb.load_model(str(xgb_path))

        for batch_size in [1, 100]:
            X_in = generate_tabular_input(n_features, batch_size)
            # Warm-up
            for _ in range(10):
                _ = clf_xgb.predict(X_in)

            # Timed
            times_ms = []
            for _ in range(200):
                t0 = time.perf_counter()
                _ = clf_xgb.predict(X_in)
                t1 = time.perf_counter()
                times_ms.append((t1 - t0) * 1000.0)

            med = float(np.median(times_ms))
            p5 = float(np.percentile(times_ms, 5))
            p95 = float(np.percentile(times_ms, 95))
            model_lbl = f"XGBoost_{p}_batch{batch_size}"

            summary_records.append({
                "category": "Tabular",
                "model_name": model_lbl,
                "runtime": "XGBoost C++",
                "batch_size": batch_size,
                "preprocess_ms": 0.0,
                "inference_median_ms": med,
                "inference_p5_ms": p5,
                "inference_p95_ms": p95,
                "total_median_ms": med,
            })
            for i, val in enumerate(times_ms):
                raw_timing_records.append({"model": model_lbl, "iteration": i, "time_ms": val})

        del clf_xgb
        gc.collect()

    # 1.2 LightGBM
    lgb_path = ROOT / "ml" / "artifacts" / "tabular" / f"lightgbm_main_{p}.txt"
    if lgb_path.exists():
        booster = lgb.Booster(model_file=str(lgb_path))

        for batch_size in [1, 100]:
            X_in = generate_tabular_input(n_features, batch_size)
            # Warm-up
            for _ in range(10):
                _ = booster.predict(X_in)

            # Timed
            times_ms = []
            for _ in range(200):
                t0 = time.perf_counter()
                _ = booster.predict(X_in)
                t1 = time.perf_counter()
                times_ms.append((t1 - t0) * 1000.0)

            med = float(np.median(times_ms))
            p5 = float(np.percentile(times_ms, 5))
            p95 = float(np.percentile(times_ms, 95))
            model_lbl = f"LightGBM_{p}_batch{batch_size}"

            summary_records.append({
                "category": "Tabular",
                "model_name": model_lbl,
                "runtime": "LightGBM C++",
                "batch_size": batch_size,
                "preprocess_ms": 0.0,
                "inference_median_ms": med,
                "inference_p5_ms": p5,
                "inference_p95_ms": p95,
                "total_median_ms": med,
            })
            for i, val in enumerate(times_ms):
                raw_timing_records.append({"model": model_lbl, "iteration": i, "time_ms": val})

        del booster
        gc.collect()

# --------------------------------------------------------------------------
# 2. Benchmark Image Preprocessing
# --------------------------------------------------------------------------
print("[*] Benchmarking Image Preprocessing (10 warm-up, 100 timed runs)...")
sample_img = generate_raw_image()
for _ in range(10):
    _ = preprocess_image(sample_img)

prep_times = []
for _ in range(100):
    t0 = time.perf_counter()
    _ = preprocess_image(sample_img)
    t1 = time.perf_counter()
    prep_times.append((t1 - t0) * 1000.0)

prep_median_ms = float(np.median(prep_times))
prep_p5_ms = float(np.percentile(prep_times, 5))
prep_p95_ms = float(np.percentile(prep_times, 95))
print(f"  Image Preprocessing Latency: median={prep_median_ms:.2f} ms (p5={prep_p5_ms:.2f}, p95={prep_p95_ms:.2f})")

# --------------------------------------------------------------------------
# 3. Benchmark Vision Models (Keras, TFLite Float32, TFLite DRQ)
# --------------------------------------------------------------------------
import tensorflow as tf

print("[*] Benchmarking Vision Models across runtimes (5 warm-up, 50 timed runs, threads=4)...")
processed_arr = preprocess_image(sample_img)
input_tensor = np.expand_dims(processed_arr, axis=0)  # (1, 224, 224, 3)

vis_regions = ["combined", "eyes", "hair", "lips", "nails", "skin", "tongue"]

for r in vis_regions:
    print(f"  Testing region: {r}")

    # (a) TFLite Float32
    f32_path = find_vision_model(r, "tflite_f32")
    if f32_path and f32_path.exists():
        interp_f32 = tf.lite.Interpreter(model_path=str(f32_path), num_threads=NUM_THREADS)
        interp_f32.allocate_tensors()
        in_idx = interp_f32.get_input_details()[0]["index"]
        out_idx = interp_f32.get_output_details()[0]["index"]

        for _ in range(5):
            interp_f32.set_tensor(in_idx, input_tensor)
            interp_f32.invoke()
            _ = interp_f32.get_tensor(out_idx)

        times_ms = []
        for _ in range(50):
            t0 = time.perf_counter()
            interp_f32.set_tensor(in_idx, input_tensor)
            interp_f32.invoke()
            _ = interp_f32.get_tensor(out_idx)
            t1 = time.perf_counter()
            times_ms.append((t1 - t0) * 1000.0)

        med = float(np.median(times_ms))
        p5 = float(np.percentile(times_ms, 5))
        p95 = float(np.percentile(times_ms, 95))
        lbl = f"Vision_{r}_TFLite_F32"

        summary_records.append({
            "category": "Vision",
            "model_name": lbl,
            "runtime": "TFLite Float32",
            "batch_size": 1,
            "preprocess_ms": prep_median_ms,
            "inference_median_ms": med,
            "inference_p5_ms": p5,
            "inference_p95_ms": p95,
            "total_median_ms": prep_median_ms + med,
        })
        for i, val in enumerate(times_ms):
            raw_timing_records.append({"model": lbl, "iteration": i, "time_ms": val})

        del interp_f32
        gc.collect()

    # (b) TFLite DRQ Quantized
    drq_path = find_vision_model(r, "tflite_drq")
    if drq_path and drq_path.exists():
        interp_drq = tf.lite.Interpreter(model_path=str(drq_path), num_threads=NUM_THREADS)
        interp_drq.allocate_tensors()
        in_idx = interp_drq.get_input_details()[0]["index"]
        out_idx = interp_drq.get_output_details()[0]["index"]

        for _ in range(5):
            interp_drq.set_tensor(in_idx, input_tensor)
            interp_drq.invoke()
            _ = interp_drq.get_tensor(out_idx)

        times_ms = []
        for _ in range(50):
            t0 = time.perf_counter()
            interp_drq.set_tensor(in_idx, input_tensor)
            interp_drq.invoke()
            _ = interp_drq.get_tensor(out_idx)
            t1 = time.perf_counter()
            times_ms.append((t1 - t0) * 1000.0)

        med = float(np.median(times_ms))
        p5 = float(np.percentile(times_ms, 5))
        p95 = float(np.percentile(times_ms, 95))
        lbl = f"Vision_{r}_TFLite_DRQ"

        summary_records.append({
            "category": "Vision",
            "model_name": lbl,
            "runtime": "TFLite DRQ",
            "batch_size": 1,
            "preprocess_ms": prep_median_ms,
            "inference_median_ms": med,
            "inference_p5_ms": p5,
            "inference_p95_ms": p95,
            "total_median_ms": prep_median_ms + med,
        })
        for i, val in enumerate(times_ms):
            raw_timing_records.append({"model": lbl, "iteration": i, "time_ms": val})

        del interp_drq
        gc.collect()

    # (c) Keras Model
    keras_path = find_vision_model(r, "keras")
    if keras_path and keras_path.exists():
        try:
            k_model = tf.keras.models.load_model(str(keras_path), compile=False)
            for _ in range(3):
                _ = k_model(input_tensor, training=False)

            times_ms = []
            for _ in range(25):
                t0 = time.perf_counter()
                _ = k_model(input_tensor, training=False)
                t1 = time.perf_counter()
                times_ms.append((t1 - t0) * 1000.0)

            med = float(np.median(times_ms))
            p5 = float(np.percentile(times_ms, 5))
            p95 = float(np.percentile(times_ms, 95))
            lbl = f"Vision_{r}_Keras"

            summary_records.append({
                "category": "Vision",
                "model_name": lbl,
                "runtime": "Keras Native",
                "batch_size": 1,
                "preprocess_ms": prep_median_ms,
                "inference_median_ms": med,
                "inference_p5_ms": p5,
                "inference_p95_ms": p95,
                "total_median_ms": prep_median_ms + med,
            })
            for i, val in enumerate(times_ms):
                raw_timing_records.append({"model": lbl, "iteration": i, "time_ms": val})

            del k_model
            gc.collect()
        except Exception as e:
            print(f"  Warning: Keras benchmark failed for {r}: {e}")

# Save raw timings
raw_csv = OUTPUT_DIR / "latency_results.csv"
with open(raw_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["model", "iteration", "time_ms"])
    writer.writeheader()
    writer.writerows(raw_timing_records)
print(f"\n[Saved Raw Timings] {raw_csv} ({len(raw_timing_records)} iterations recorded)")

# %%
# Plotting Latency Results
fig, (ax_tab, ax_vis) = plt.subplots(1, 2, figsize=(16, 7.5), dpi=DPI)
fig.subplots_adjust(wspace=0.35, bottom=0.18)

# Color Palette
C_XGB = "#0072B2"
C_LGB = "#D55E00"
C_PREP = "#E69F00"
C_TF_F32 = "#009E73"
C_TF_DRQ = "#56B4E9"
C_KERAS = "#CC79A7"

# --------------------------------------------------------------------------
# (a) Tabular Latency: XGBoost vs LightGBM (Single vs Batch)
# --------------------------------------------------------------------------
tab_recs = [s for s in summary_records if s["category"] == "Tabular"]
tab_names = [f"{s['model_name'].replace('Tabular_', '')}" for s in tab_recs]
tab_meds = [s["inference_median_ms"] for s in tab_recs]
tab_err_low = [max(0, s["inference_median_ms"] - s["inference_p5_ms"]) for s in tab_recs]
tab_err_high = [max(0, s["inference_p95_ms"] - s["inference_median_ms"]) for s in tab_recs]

y_tab = np.arange(len(tab_recs))
colors_tab = [C_XGB if "XGB" in n else C_LGB for n in tab_names]

bars_tab = ax_tab.barh(
    y_tab,
    tab_meds,
    xerr=[tab_err_low, tab_err_high],
    color=colors_tab,
    edgecolor="black",
    capsize=3,
    height=0.65,
)

for bar, med in zip(bars_tab, tab_meds):
    w = bar.get_width()
    ax_tab.text(w + 0.05, bar.get_y() + bar.get_height() / 2, f"{med:.2f} ms", ha="left", va="center", fontsize=8)

ax_tab.set_yticks(y_tab)
ax_tab.set_yticklabels(tab_names, fontsize=8)
ax_tab.set_xlabel("Latency (ms, Median with p5..p95 error bars)", fontsize=9.5, fontweight="bold")
ax_tab.set_title("(a) Tabular Prediction Latency (N=1 and Batch N=100)", fontsize=11, fontweight="bold")
ax_tab.grid(axis="x", linestyle=":", alpha=0.6)

# --------------------------------------------------------------------------
# (b) Vision Latency: Preprocessing + Runtime Inference (Stacked Bar)
# --------------------------------------------------------------------------
vis_recs = [s for s in summary_records if s["category"] == "Vision" and "TFLite_F32" in s["model_name"]]
vis_labels = [s["model_name"].split("_")[1].capitalize() for s in vis_recs]

inf_meds = [s["inference_median_ms"] for s in vis_recs]
inf_err_low = [max(0, s["inference_median_ms"] - s["inference_p5_ms"]) for s in vis_recs]
inf_err_high = [max(0, s["inference_p95_ms"] - s["inference_median_ms"]) for s in vis_recs]

x_v = np.arange(len(vis_recs))
w_v = 0.55

p_prep = ax_vis.bar(x_v, [prep_median_ms] * len(vis_recs), w_v, label="Image Preprocess (Letterbox + Scale)", color=C_PREP, edgecolor="black")
p_inf = ax_vis.bar(
    x_v,
    inf_meds,
    w_v,
    bottom=[prep_median_ms] * len(vis_recs),
    yerr=[inf_err_low, inf_err_high],
    capsize=3,
    label="TFLite Float32 Inference",
    color=C_TF_F32,
    edgecolor="black",
)

for i, (med, total) in enumerate(zip(inf_meds, [prep_median_ms + m for m in inf_meds])):
    ax_vis.text(i, total + inf_err_high[i] + 1.0, f"{total:.1f} ms\n({med:.1f} inf)", ha="center", va="bottom", fontsize=7.5)

ax_vis.set_ylabel("Latency (ms, Median with p5..p95 error bars)", fontsize=9.5, fontweight="bold")
ax_vis.set_title("(b) Vision Latency: Preprocessing + TFLite Float32 Inference", fontsize=11, fontweight="bold")
ax_vis.set_xticks(x_v)
ax_vis.set_xticklabels(vis_labels, fontsize=9)
ax_vis.legend(loc="upper left", fontsize=8.5)
ax_vis.grid(axis="y", linestyle=":", alpha=0.6)

# Footnote with hardware specifications
fig.text(0.5, 0.05, SYS_INFO, ha="center", fontsize=8, color="#333333")
fig.text(0.5, 0.015, FOOTNOTE, ha="center", fontsize=8.5, style="italic", color="#333333")

fig_png = OUTPUT_DIR / "04_inference_latency.png"
fig_csv = OUTPUT_DIR / "04_inference_latency.csv"
fig.savefig(fig_png, dpi=DPI, bbox_inches="tight")
print(f"[Saved Figure] {fig_png}")

# Summary CSV export
with open(fig_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "category", "model_name", "runtime", "batch_size", "preprocess_ms",
            "inference_median_ms", "inference_p5_ms", "inference_p95_ms", "total_median_ms"
        ],
    )
    writer.writeheader()
    writer.writerows(summary_records)
print(f"[Saved Summary CSV] {fig_csv}")

# Print console summary
print("\n" + "=" * 80)
print(f"{'Model / Runtime':<35} | {'Batch':<6} | {'Inference Median (ms)':<22} | {'Total (ms)':<10}")
print("=" * 80)
for s in summary_records:
    print(f"{s['model_name']:<35} | {s['batch_size']:<6} | {s['inference_median_ms']:<22.2f} | {s['total_median_ms']:<10.2f}")
print("=" * 80)

if SHOW:
    plt.show()
