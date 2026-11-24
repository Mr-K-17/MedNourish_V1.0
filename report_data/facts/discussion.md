# Empirical Results & Technical Discussion: MEDNOURISH Evaluation

**Context**: Final-Year Computer Science Academic Project Report (Chapters 5–8)  
**Project**: MEDNOURISH Precision Health & Clinical Reference Architecture  
**Notice**: Educational Research Prototype — Not a Medical Device. Empirical Research Benchmark Only.

---

## 1. Summary of Empirical Findings

Across all experimental evaluations conducted within the MEDNOURISH architecture, the empirical data demonstrates that precision nutritional risk estimation can be achieved reliably on edge-tier consumer hardware without relying on cloud generative language models or uncalibrated diagnostic heuristics.

1. **Tabular Feature Profile Separation & Leakage Mitigation**:
   - In baseline experimentation (`with_labs`), models demonstrated synthetic 100.0% accuracy ($1.000$ Macro-F1). Technical audit revealed direct target leakage through biochemical serum markers (`Serum_Ferritin_ng_mL`, `Vitamin_D_ng_mL`, etc.), which are clinical proxies of the target diagnosis itself.
   - The engineered **V2 Pragmatic profile** (`no_labs`), relying exclusively on vital signs, lifestyle habits, and non-invasive patient metrics, yielded an honest **$88.25\%$ accuracy** ($0.874$ Macro-F1) using LightGBM and XGBoost.
   - The minimal **Telehealth Symptom-Only profile** (`symptoms_only`), operating with only 12 qualitative self-reported symptoms, achieved **$76.50\%$ accuracy** ($0.751$ Macro-F1). This represents a clinically realistic ceiling for remote intake when physical or biochemical biomarkers are absent.

2. **Mobile Multi-Region Computer Vision Performance**:
   - The 7 regional MobileNetV2 models (160×160 resolution) demonstrated strong classification efficacy on well-circumscribed anatomical regions:
     - **Lips**: $92.11\%$ Accuracy | $0.918$ Macro-F1 (95% CI: $[0.871, 0.965]$)
     - **Nails**: $86.62\%$ Accuracy | $0.854$ Macro-F1 (95% CI: $[0.798, 0.910]$)
     - **Hair**: $84.31\%$ Accuracy | $0.839$ Macro-F1 (95% CI: $[0.780, 0.898]$)
     - **Eyes**: $79.44\%$ Accuracy | $0.786$ Macro-F1 (95% CI: $[0.743, 0.829]$)
     - **Combined (10-Class)**: $77.10\%$ Accuracy | $0.762$ Macro-F1 (95% CI: $[0.734, 0.790]$)
     - **Tongue**: $71.36\%$ Accuracy | $0.702$ Macro-F1 (95% CI: $[0.638, 0.766]$)
     - **Skin**: $66.34\%$ Accuracy | $0.648$ Macro-F1 (95% CI: $[0.594, 0.702]$)
   - Quality filtering via Laplacian blur variance ($\ge 50.0$) and luminance boundaries ($[40, 225]$) successfully prevented out-of-focus or extreme illumination artifacts from degrading classification accuracy.

3. **Edge Quantization & Hardware Parity**:
   - Dynamic Range Quantization (DRQ INT8) reduced MobileNetV2 model footprints from $\sim 9.1\,\text{MB}$ (Float32) to $\sim 2.35\,\text{MB}$—a **$73.0\%$ storage reduction**.
   - Parity evaluation confirmed **$>98.6\%$ top-1 classification agreement** between quantized TFLite edge models and baseline Float32 Keras models, with median inference latency bounded at **$14.2\,\text{ms}$** on commodity CPU cores.

---

## 2. Architectural Tradeoffs & Engineering Decisions

| Architectural Choice | Alternative Considered | Technical Tradeoff Justification |
|---|---|---|
| **Deterministic Rule & Curated CSVs** | Generative Cloud LLMs (e.g. GPT-4, Claude) | Generative LLMs present severe clinical hallucination risks, non-deterministic outputs, latency overhead, and external cloud privacy exposure. Curated CSVs and inverted indexes provide $100\%$ explainable, instant, and reproducible guidance. |
| **MobileNetV2 (160×160)** | ResNet-50 / DenseNet-121 | Deep convolutional architectures exceed $25\text{M}$ parameters and $>90\,\text{MB}$ storage, causing thermal throttling and lag on mobile edge browsers. MobileNetV2 operates under $2.4\,\text{MB}$ with sub-20ms latency. |
| **Dynamic SQLite / MySQL Engine** | Rigid Cloud Database (DynamoDB / Firebase Firestore) | Dual-dialect architecture enables zero-config in-memory testing for fast CI pipelines (`DB_MODE=sqlite`) while supporting ACID-compliant relational schemas (`DB_MODE=mysql`) in deployment. |
| **Recency-Weighted Exponential Decay** | Flat Historical Averaging | Clinical symptoms attenuate or escalate over time. Flat averaging penalizes recovered historical symptoms; exponential decay ($t_{1/2} = 7\,\text{days}$) ensures current clinical acuity dominates the Virtual Ward trajectory. |

---

## 3. System Limitations & Clinical Boundaries

1. **Academic Prototype Status**: MEDNOURISH is developed strictly as an educational and technical research prototype. It does not possess FDA 510(k), CE mark, or SaMD (Software as a Medical Device) clinical clearance.
2. **Skin Image Confounding & Shortcut Vulnerability**: As indicated by the Grad-CAM audits, the Skin regional model exhibits moderate susceptibility to image background artifacts and lighting shortcuts. A confidence discount penalty factor ($0.55$) is applied programmatically to mitigate spurious overconfidence.
3. **Telehealth Symptom Boundary**: In self-reported telehealth evaluations, single-symptom queries lack discriminant power. The system rigorously enforces an **Insufficient Information Gate** when symptom count $m < 2$, refusing to issue speculative risk bands.

---

## 4. Recommendations for Future Research

- **Multi-Modal Attention Fusion**: Investigating early-fusion cross-attention networks combining patient dietary logs with regional vision feature tokens.
- **On-Device Continuous Learning**: Implementing local federated fine-tuning using differential privacy techniques to preserve patient anonymity.
- **Calibrated Uncertainty Quantification**: Extending deep ensemble Monte Carlo Dropout to output formal Bayesian predictive variance intervals alongside risk bands.
