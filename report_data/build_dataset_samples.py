import os
import shutil

root = r"C:\Users\USER\Desktop\MedNourish-Dev"
samples_dir = os.path.join(root, "report_data", "dataset_samples")
os.makedirs(samples_dir, exist_ok=True)

# 1. Tabular sample
tab_src = os.path.join(root, "datasets", "tabular", "nutrition_disease_dataset.csv")
if os.path.exists(tab_src):
    with open(tab_src, "r", encoding="utf-8") as f:
        lines = [f.readline() for _ in range(21)]
    with open(os.path.join(samples_dir, "tabular_sample.csv"), "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Created tabular_sample.csv")

# 2. Food items sample
food_src = os.path.join(root, "knowledge", "curated", "food_items.csv")
if os.path.exists(food_src):
    with open(food_src, "r", encoding="utf-8") as f:
        lines = [f.readline() for _ in range(21)]
    with open(os.path.join(samples_dir, "curated_food_items_sample.csv"), "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Created curated_food_items_sample.csv")

# 3. Nutrient guidance sample
nutr_src = os.path.join(root, "knowledge", "curated", "nutrient_guidance.csv")
if os.path.exists(nutr_src):
    with open(nutr_src, "r", encoding="utf-8") as f:
        lines = [f.readline() for _ in range(21)]
    with open(os.path.join(samples_dir, "curated_nutrient_guidance_sample.csv"), "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Created curated_nutrient_guidance_sample.csv")

# 4. Synonyms YAML sample
syn_src = os.path.join(root, "knowledge", "curated", "synonyms.yaml")
if os.path.exists(syn_src):
    with open(syn_src, "r", encoding="utf-8") as f:
        lines = [f.readline() for _ in range(30)]
    with open(os.path.join(samples_dir, "curated_synonyms_sample.yaml"), "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Created curated_synonyms_sample.yaml")

# 5. Image samples: find 1 sample image per region
img_base = os.path.join(root, "datasets", "images")
regions = ["combined", "eyes", "hair", "lips", "nails", "skin", "tongue"]

for reg in regions:
    reg_path = os.path.join(img_base, reg)
    sample_found = None
    if os.path.exists(reg_path):
        for root_dir, dirs, files in os.walk(reg_path):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    sample_found = os.path.join(root_dir, file)
                    break
            if sample_found:
                break
    
    if sample_found:
        dst = os.path.join(samples_dir, f"sample_{reg}.png")
        # Copy or convert
        from PIL import Image
        im = Image.open(sample_found)
        im = im.resize((224, 224))
        im.save(dst)
        print(f"Saved sample_{reg}.png from {sample_found}")
    else:
        # Fallback to gradcam
        gc_src = os.path.join(root, "ml", "artifacts", "vision", "gradcam")
        gc_match = None
        if os.path.exists(gc_src):
            for f in os.listdir(gc_src):
                if reg in f.lower() and f.endswith(".png"):
                    gc_match = os.path.join(gc_src, f)
                    break
        if gc_match:
            shutil.copy(gc_match, os.path.join(samples_dir, f"sample_{reg}.png"))
            print(f"Fallback copied sample_{reg}.png from gradcam")
        else:
            print(f"NOT AVAILABLE: sample image for {reg}")

print("Dataset samples ready!")
