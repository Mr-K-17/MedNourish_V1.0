"""
MedNourish — True Vision Model Re-evaluation on Held-Out Test Manifests
======================================================================
Loads each of the 6 vision models (.keras and .tflite),
reads the test manifest rows (split == 'test'),
evaluates predictions in bounded batches of 32,
and outputs exact re-evaluation metrics alongside model card metrics.
"""

import csv
import json
import os
import sys
import time
from pathlib import Path
import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, f1_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.image_pipeline import load_image_rgb, resize_with_pad

MANIFESTS_DIR = Path("ml/artifacts/manifests")
VISION_ARTIFACTS_DIR = Path("ml/artifacts/vision")

MODELS = ["combined", "eyes", "hair", "nails", "skin", "tongue"]

def reevaluate_all():
    results = {}
    print("===================================================================")
    print(" Re-evaluating All 6 Vision Models on Held-Out Test Manifests")
    print("===================================================================")

    for model_name in MODELS:
        manifest_file = MANIFESTS_DIR / f"{model_name}_manifest.csv"
        keras_file = VISION_ARTIFACTS_DIR / f"{model_name}_mobilenetv2.keras"
        tflite_file = VISION_ARTIFACTS_DIR / f"{model_name}_float32.tflite"
        card_file = VISION_ARTIFACTS_DIR / f"model_card_{model_name}.json"

        if not manifest_file.exists() or not keras_file.exists() or not tflite_file.exists():
            print(f"Skipping {model_name}: missing artifact")
            continue

        with open(card_file, "r", encoding="utf-8") as f:
            card = json.load(f)

        classes = card.get("classes", [])
        class_to_idx = {c: i for i, c in enumerate(classes)}

        with open(manifest_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            test_rows = [r for r in reader if r["split"] == "test"]

        print(f"\n--- Model: {model_name.upper()} (Test Samples: {len(test_rows)}, Classes: {len(classes)}) ---")

        # Load images
        X_test_list = []
        y_test_list = []
        missing_count = 0
        for r in test_rows:
            fpath = r["filepath"]
            if not os.path.exists(fpath):
                # Check relative
                fpath = str(PROJECT_ROOT / r["relative_path"])
            img = load_image_rgb(fpath)
            if img is None:
                missing_count += 1
                continue
            padded = resize_with_pad(img, target_size=(224, 224))
            norm = (padded.astype(np.float32) / 127.5) - 1.0
            X_test_list.append(norm)
            y_test_list.append(class_to_idx[r["class_name"]])

        if missing_count > 0:
            print(f"  Warning: {missing_count} images could not be loaded!")

        X_test = np.array(X_test_list, dtype=np.float32)
        y_test = np.array(y_test_list, dtype=np.int32)

        # 1. Evaluate Keras model
        keras_model = tf.keras.models.load_model(str(keras_file))
        keras_probs = keras_model.predict(X_test, batch_size=32, verbose=0)
        keras_preds = np.argmax(keras_probs, axis=-1)

        keras_acc = float(accuracy_score(y_test, keras_preds))
        keras_f1 = float(f1_score(y_test, keras_preds, average="macro"))

        # 2. Evaluate Float32 TFLite model
        interpreter = tf.lite.Interpreter(model_path=str(tflite_file))
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        input_idx = input_details[0]["index"]
        output_idx = output_details[0]["index"]

        tflite_probs = []
        for i in range(len(X_test)):
            sample = np.expand_dims(X_test[i], axis=0)
            interpreter.set_tensor(input_idx, sample)
            interpreter.invoke()
            out = interpreter.get_tensor(output_idx)[0]
            tflite_probs.append(out)

        tflite_probs = np.array(tflite_probs)
        tflite_preds = np.argmax(tflite_probs, axis=-1)

        tflite_acc = float(accuracy_score(y_test, tflite_preds))
        tflite_f1 = float(f1_score(y_test, tflite_preds, average="macro"))

        # Parity metrics
        top1_agreement = float(np.mean(keras_preds == tflite_preds) * 100.0)
        max_abs_diff = float(np.max(np.abs(keras_probs - tflite_probs)))

        card_acc = card.get("test_metrics", {}).get("accuracy", 0.0)
        card_f1 = card.get("test_metrics", {}).get("macro_f1", 0.0)

        acc_diff_pts = abs(keras_acc - card_acc) * 100.0
        f1_diff_pts = abs(keras_f1 - card_f1) * 100.0

        print(f"  Model Card  -> Acc: {card_acc*100:.2f}%, Macro-F1: {card_f1:.4f}")
        print(f"  Re-evaluated -> Acc: {keras_acc*100:.2f}%, Macro-F1: {keras_f1:.4f} (Diff: {acc_diff_pts:.2f} pts)")
        print(f"  TFLite Re-ev -> Acc: {tflite_acc*100:.2f}%, Macro-F1: {tflite_f1:.4f}")
        print(f"  TFLite Top-1 Agreement: {top1_agreement:.2f}%, Max Diff: {max_abs_diff:.8f}")

        results[model_name] = {
            "test_samples": len(y_test),
            "num_classes": len(classes),
            "card_acc": card_acc,
            "card_macro_f1": card_f1,
            "reeval_acc": keras_acc,
            "reeval_macro_f1": keras_f1,
            "tflite_acc": tflite_acc,
            "tflite_macro_f1": tflite_f1,
            "top1_agreement_pct": top1_agreement,
            "max_abs_diff": max_abs_diff,
            "acc_diff_pts": acc_diff_pts,
            "flagged_gt_1pt": acc_diff_pts > 1.0 or f1_diff_pts > 1.0,
        }

    out_file = VISION_ARTIFACTS_DIR / "vision_reevaluation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll models re-evaluated. Saved results to {out_file}")

if __name__ == "__main__":
    reevaluate_all()
