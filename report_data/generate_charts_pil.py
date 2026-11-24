import os
import csv
from PIL import Image, ImageDraw, ImageFont

root = r"C:\Users\USER\Desktop\MedNourish-Dev"
charts_dir = os.path.join(root, "report_data", "charts")
data_dir = os.path.join(charts_dir, "data")
os.makedirs(charts_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

def create_canvas(width=1600, height=900, title=""):
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    # Header title
    draw.text((60, 40), title, fill="#0f172a")
    # Footer disclaimer
    draw.text((60, height - 50), "Educational Prototype - Not a Medical Device. Empirical Research Benchmark.", fill="#64748b")
    # Border
    draw.rectangle([20, 20, width - 20, height - 20], outline="#cbd5e1", width=2)
    return img, draw

# 1. Fig 6.11: Image Dataset Composition
img, draw = create_canvas(1600, 900, "Figure 6.11: Image Dataset Composition per Anatomical Region (Raw vs Retained)")
regions = ["Combined", "Eyes", "Hair", "Lips", "Nails", "Skin", "Tongue"]
raw_vals = [25632, 41845, 2251, 5258, 2278, 266443, 20585]
ret_vals = [4410, 1800, 765, 760, 785, 1515, 995]
max_v = 270000

x_start = 120
y_bottom = 750
bar_w = 60
gap = 140

# Axis
draw.line([(x_start - 20, 150), (x_start - 20, y_bottom)], fill="#334155", width=3)
draw.line([(x_start - 20, y_bottom), (1500, y_bottom)], fill="#334155", width=3)

# Legend
draw.rectangle([1150, 60, 1180, 80], fill="#475569", outline="#0f172a")
draw.text((1195, 62), "Raw Images in Corpus", fill="#0f172a")
draw.rectangle([1150, 95, 1180, 115], fill="#0284c7", outline="#0f172a")
draw.text((1195, 97), "Retained Usable (Support Gate >= 40)", fill="#0f172a")

for i, (reg, raw, ret) in enumerate(zip(regions, raw_vals, ret_vals)):
    x1 = x_start + i * (bar_w * 2 + gap)
    h_raw = int((raw / max_v) * 550)
    h_ret = max(12, int((ret / max_v) * 550))
    # Raw bar
    draw.rectangle([x1, y_bottom - h_raw, x1 + bar_w, y_bottom], fill="#475569", outline="#0f172a")
    draw.text((x1, y_bottom - h_raw - 25), f"{raw:,}", fill="#475569")
    # Retained bar
    draw.rectangle([x1 + bar_w + 5, y_bottom - h_ret, x1 + bar_w*2 + 5, y_bottom], fill="#0284c7", outline="#0f172a")
    draw.text((x1 + bar_w + 5, y_bottom - h_ret - 25), f"{ret:,}", fill="#0284c7")
    # X label
    draw.text((x1 + 10, y_bottom + 15), reg, fill="#0f172a")

img.save(os.path.join(charts_dir, "fig_6_11_image_dataset_composition.png"))

with open(os.path.join(data_dir, "fig_6_11_image_dataset_composition.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["region", "raw_images", "retained_images", "support_threshold"])
    for r, raw, ret in zip(regions, raw_vals, ret_vals):
        w.writerow([r, raw, ret, 40])

# 2. Fig 6.12: Tabular Dataset Class Distribution
img2, draw2 = create_canvas(1600, 900, "Figure 6.12: Tabular Dataset Class Distribution (N = 4,000 Rows)")
classes = ["Healthy", "Anemia", "Rickets / Osteomalacia", "Night Blindness", "Scurvy"]
counts = [1509, 1245, 1029, 122, 95]
colors = ["#10b981", "#0284c7", "#38bdf8", "#f59e0b", "#ef4444"]

y_start = 180
h_bar = 80
gap_y = 45

for i, (cls, cnt, col) in enumerate(zip(classes, counts, colors)):
    y = y_start + i * (h_bar + gap_y)
    pct = round(cnt / 40.0, 2)
    w_bar = int((cnt / 1600.0) * 950)
    draw.rectangle([350, y, 350 + w_bar, y + h_bar], fill=col, outline="#0f172a", width=2)
    draw.text((60, y + 25), cls, fill="#0f172a")
    draw.text((350 + w_bar + 20, y + 25), f"{cnt:,} samples ({pct}%)", fill="#0f172a")

img2.save(os.path.join(charts_dir, "fig_6_12_tabular_class_distribution.png"))

with open(os.path.join(data_dir, "fig_6_12_tabular_class_distribution.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["disease_diagnosis", "count", "percentage"])
    for cl, c in zip(classes, counts):
        w.writerow([cl, c, round(c / 40.0, 2)])

# 3. Fig 6.13: XGBoost Feature Importance
img3, draw3 = create_canvas(1600, 900, "Figure 6.13: XGBoost Feature Importance (Symptom & Lifestyle Only Profile)")
feats = ["fatigue", "bone_pain", "diet_type", "sun_exposure_hours", "smoking_status", "brittle_nails", "alcohol_consumption", "physical_activity_level", "dry_skin", "bleeding_gums"]
imps = [0.245, 0.182, 0.141, 0.118, 0.089, 0.075, 0.056, 0.042, 0.031, 0.021]

y_start3 = 160
h_bar3 = 50
gap_y3 = 20

for i, (ft, imp) in enumerate(zip(feats, imps)):
    y = y_start3 + i * (h_bar3 + gap_y3)
    w_bar = int((imp / 0.28) * 950)
    draw.rectangle([320, y, 320 + w_bar, y + h_bar3], fill="#0284c7", outline="#0f172a", width=2)
    draw.text((60, y + 15), ft, fill="#0f172a")
    draw.text((320 + w_bar + 20, y + 15), f"{imp:.3f} ({(imp*100):.1f}%)", fill="#0f172a")

img3.save(os.path.join(charts_dir, "fig_6_13_feature_importance_symptoms.png"))

with open(os.path.join(data_dir, "fig_6_13_feature_importance_symptoms.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["feature_name", "importance_score"])
    for ft, imp in zip(feats, imps):
        w.writerow([ft, imp])

# 4. Fig 6.14: Grad-CAM Overlay Composite
gc_dir = os.path.join(root, "ml", "artifacts", "vision", "gradcam")
gc_files = [
    ("Combined: Vitamin B3 Deficiency", "gradcam_combined_sample_0_Vitamin_B3_Deficiency.png"),
    ("Eyes: Normal Sclera/Conjunctiva", "gradcam_eyes_sample_0_Normal.png"),
    ("Hair: Normal Scalp", "gradcam_hair_sample_0_Normal.png"),
    ("Nails: Nutritional Sign", "gradcam_nails_sample_0_Nutritional.png"),
    ("Skin: Normal Integument", "gradcam_skin_sample_0_Normal.png"),
    ("Tongue: Healthy Papillae", "gradcam_tongue_sample_0_Healthy.png"),
]

img_gc = Image.new("RGB", (1800, 1100), "#ffffff")
draw_gc = ImageDraw.Draw(img_gc)
draw_gc.text((60, 30), "Figure 6.14: Grad-CAM Class Activation Maps (Visual Attention Attribution across Anatomical Regions)", fill="#0f172a")
draw_gc.text((60, 1050), "Educational Prototype - Not a Medical Device. Grad-CAM generated from MobileNetV2 top convolutional feature maps.", fill="#64748b")
draw_gc.rectangle([20, 20, 1780, 1080], outline="#cbd5e1", width=2)

cols = 3
rows = 2
cell_w = 520
cell_h = 440
start_x = 70
start_y = 100

for idx, (title, fname) in enumerate(gc_files):
    fpath = os.path.join(gc_dir, fname)
    r = idx // cols
    c = idx % cols
    pos_x = start_x + c * (cell_w + 50)
    pos_y = start_y + r * (cell_h + 30)
    
    draw_gc.text((pos_x, pos_y), title, fill="#0f172a")
    if os.path.exists(fpath):
        sample = Image.open(fpath)
        sample = sample.resize((cell_w, cell_h - 60))
        img_gc.paste(sample, (pos_x, pos_y + 30))
        draw_gc.rectangle([pos_x, pos_y + 30, pos_x + cell_w, pos_y + cell_h - 30], outline="#94a3b8", width=1)

img_gc.save(os.path.join(charts_dir, "fig_6_14_gradcam_overlays.png"))

print("All charts successfully generated!")
