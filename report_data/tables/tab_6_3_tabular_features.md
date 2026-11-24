# Tabular Feature Profiles Specification (Table 6.3)

Evaluated across the 4,000-row tabular dataset (`vitamin_deficiency_disease_dataset_20260123.csv`) to benchmark the **Clinical Feature Leakage Gap**.

| Feature Identifier | Category | Representation | `with_labs` (32) | `no_labs` (18) | `symptoms_only` (10) | Clinical Reality & Leakage Analysis |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| `age` | Demographics | Integer | YES | YES | YES | Baseline physiological vulnerability across age brackets |
| `gender` | Demographics | Categorical | YES | YES | YES | Biological sex associations (e.g. anemia in menstruating females) |
| `height_cm` | Demographics | Float | YES | YES | NO | Physical stature anthropometry |
| `weight_kg` | Demographics | Float | YES | YES | NO | Body mass indicator |
| `bmi` | Demographics | Float | YES | YES | NO | Body Mass Index ($kg/m^2$) |
| `smoking_status` | Lifestyle | Categorical | YES | YES | YES | Accelerates vitamin C catabolism |
| `alcohol_consumption` | Lifestyle | Categorical | YES | YES | YES | Impairs thiamine (B1) and folate enterocyte transport |
| `physical_activity_level` | Lifestyle | Categorical | YES | YES | YES | Modulates micronutrient turnover rates |
| `sun_exposure_hours` | Lifestyle | Float | YES | YES | YES | Cutaneous pre-vitamin D3 synthesis indicator |
| `diet_type` | Lifestyle | Categorical | YES | YES | YES | Vegan/Vegetarian risk factor for B12 and heme iron |
| `fatigue` | Symptoms | Binary | YES | YES | YES | Non-specific clinical marker (Anemia, B12, Iron) |
| `dry_skin` | Symptoms | Binary | YES | YES | YES | Cutaneous epithelial integrity failure (Vitamin A) |
| `night_blindness` | Symptoms | Binary | YES | YES | YES | Rhodopsin photopigment resynthesis defect (Vitamin A) |
| `brittle_nails` | Symptoms | Binary | YES | YES | YES | Keratin plate matrix defect (Iron, Zinc, Biotin) |
| `bleeding_gums` | Symptoms | Binary | YES | YES | YES | Defective collagen prolyl hydroxylation (Vitamin C Scurvy) |
| `bone_pain` | Symptoms | Binary | YES | YES | YES | Unmineralized osteoid matrix distension (Vitamin D) |
| `hair_loss` | Symptoms | Binary | YES | YES | YES | Telogen effluvium from follicular arrest (Zinc, Iron) |
| `mouth_ulcers` | Symptoms | Binary | YES | YES | YES | Mucosal epithelial atrophy (B-Complex, Iron) |
| `diet_vitamin_a_pct` | Dietary RDA % | Float | YES | YES | NO | Daily dietary intake percentage against recommended allowance |
| `diet_vitamin_c_pct` | Dietary RDA % | Float | YES | YES | NO | Daily dietary intake percentage against recommended allowance |
| `diet_vitamin_d_pct` | Dietary RDA % | Float | YES | YES | NO | Daily dietary intake percentage against recommended allowance |
| `diet_iron_pct` | Dietary RDA % | Float | YES | YES | NO | Daily dietary intake percentage against recommended allowance |
| `diet_calcium_pct` | Dietary RDA % | Float | YES | YES | NO | Daily dietary intake percentage against recommended allowance |
| `serum_retinol_ug_dl` | Lab Biomarker | Float | YES | NO | NO | **DIRECT TARGET LEAKAGE:** Clinical definition of Vitamin A deficiency |
| `serum_ascorbic_acid_mg_dl` | Lab Biomarker | Float | YES | NO | NO | **DIRECT TARGET LEAKAGE:** Clinical definition of Scurvy |
| `serum_25_hydroxy_d_ng_ml` | Lab Biomarker | Float | YES | NO | NO | **DIRECT TARGET LEAKAGE:** Clinical definition of Rickets / Osteomalacia |
| `serum_ferritin_ng_ml` | Lab Biomarker | Float | YES | NO | NO | **DIRECT TARGET LEAKAGE:** Direct diagnostic determinant of Anemia |
| `hemoglobin_g_dl` | Lab Biomarker | Float | YES | NO | NO | **DIRECT TARGET LEAKAGE:** Direct diagnostic cutoff for Anemia |
| `serum_calcium_mg_dl` | Lab Biomarker | Float | YES | NO | NO | Calcium homeostasis biomarker |
| `serum_alk_phosphatase_u_l`| Lab Biomarker | Float | YES | NO | NO | Marker of active osteomalacia bone turnover |
| `serum_b12_pg_ml` | Lab Biomarker | Float | YES | NO | NO | Lab determinant of megaloblastic anemia |
| `serum_folate_ng_ml` | Lab Biomarker | Float | YES | NO | NO | Lab determinant of megaloblastic anemia |
