# Vision Models Class Maps & Edge Specifications (Table 6.4)

Verified against `ml/class_maps/*.yaml` and `ml/artifacts/v2/vision_v2_summary.json`. All 7 models passed **100.0% Float32 TFLite parity agreement**.

| Model ID | Region | Classes | Verified Class Labels | Support Gate | Test $N$ | Test Acc | Macro-F1 | Shortcut Risk | Float32 Size | DRQ Size |
|:---|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **`combined`** | Multi | 10 | `Angular_Cheilitis`, `Aphthous_Ulcer`, `Cheilitis`, `Eye_Blepharitis`, `Eye_Conjunctivitis`, `Eye_Normal`, `Hair_Alopecia_Areata`, `Hair_Normal`, `Nail_Koilonychia`, `Skin_Normal` | $\ge 40$ | 662 | **41.54%** | 0.4153 | LOW (25.5%) | 8.51 MB | 2.41 MB |
| **`eyes`** | Eyes | 3 | `Blepharitis`, `Conjunctivitis`, `Normal` | $\ge 40$ | 270 | **98.89%** | 0.9889 | HIGH (95.2%) | 8.47 MB | 2.40 MB |
| **`hair`** | Hair | 2 | `Alopecia_Areata`, `Normal` | $\ge 40$ | 115 | **93.04%** | 0.9056 | HIGH (94.8%) | 8.47 MB | 2.39 MB |
| **`lips`** | Lips | 3 | `Cheilitis`, `Herpes_Labialis`, `Normal` | $\ge 40$ | 114 | **90.35%** | 0.7432 | HIGH (83.3%) | 8.47 MB | 2.40 MB |
| **`nails`** | Nails | 3 | `Koilonychia`, `Normal`, `Onychomycosis` | $\ge 40$ | 118 | **73.73%** | 0.6480 | HIGH (73.7%) | 8.47 MB | 2.40 MB |
| **`skin`** | Skin | 6 | `Acne`, `Eczema`, `Hyperpigmentation`, `Normal`, `Pityriasis_Alba`, `Psoriasis` | $\ge 40$ | 227 | **81.06%** | 0.6290 | HIGH (72.3%) | 8.48 MB | 2.40 MB |
| **`tongue`** | Tongue | 4 | `Aphthous_Ulcer`, `Coated_Tongue`, `Glossitis`, `Normal` | $\ge 40$ | 149 | **86.58%** | 0.7748 | HIGH (75.2%) | 8.48 MB | 2.40 MB |
