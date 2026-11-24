# Verified Algorithmic Specifications & Mathematical Formulations

This document details the mathematical models, formulas, decision boundaries, constants, and tie-breaking logic implemented across the MEDNOURISH core services.

---

## 1. Deterministic Reference Matcher
**Source Implementation:** `backend/app/services/knowledge_service.py` & `backend/app/services/scoring_service.py`

### 1.1 Input & Pre-processing
- **Input:** Set of user-selected anatomical symptom tags $U = \{t_1, t_2, \dots, t_k\}$.
- **Corpus:** 116 curated expert condition rows $C = \{c_1, c_2, \dots, c_{116}\}$ distributed across 6 anatomical regions (Eyes, Hair, Lips, Nails, Skin, Tongue).
- **Safety Boundary (SAF-06):** If $|U| = 0$, the algorithm halts immediately and returns `status = INSUFFICIENT_INFORMATION`. Zero false reassurance or guessing is permitted.

### 1.2 Deterministic Ranking Logic
1. For each condition row $c_j$ with reference tags $T(c_j)$, compute set intersection:
   $$I(c_j) = U \cap T(c_j)$$
2. Compute raw match count: $m_j = |I(c_j)|$.
3. Rows are ordered deterministically using the composite key:
   $$\text{sort\_key}(c_j) = \Big( -m_j, \, |T(c_j)|, \, \text{class\_label}(c_j) \Big)$$
   - Primary: Highest intersection count ($m_j \downarrow$).
   - Secondary: Most specific condition ($|T(c_j)| \uparrow$ - fewer total tags).
   - Tertiary: Alphabetical tie-break on `class_label` ensuring 100% reproducible ordering.

---

## 2. Mathematical Scoring Model (Reference Match %)
**Source Implementation:** `backend/app/services/scoring_service.py` (lines 140–210)

To avoid misleading clinical probability claims while providing transparent match strength:

### 2.1 Inverse Document Frequency (IDF) Weighting
Rare clinical symptoms carry higher discriminative weight than ubiquitous symptoms (such as generic fatigue):
$$\text{IDF}(t) = \ln \left( 1 + \frac{N - n(t) + 0.5}{n(t) + 0.5} \right)$$
Where $N = 116$ total curated conditions, and $n(t)$ is the document frequency of tag $t$.

### 2.2 Small-Evidence Shrinkage Factor
To prevent a single isolated symptom match from generating a deceptive 100% score:
$$k_{\text{shrinkage}} = \min\big(1.0, \, 0.40 + 0.20 \times m_j\big)$$
- For 1 matched tag: $k = 0.60$ (maximum score achievable is discounted by 40%).
- For 2 matched tags: $k = 0.80$.
- For 3+ matched tags: $k = 1.00$ (full weight).

### 2.3 Row Match Strength
For each condition row $c_j$:
$$S_{\text{row}}(c_j) = k_{\text{shrinkage}} \times \left( \frac{\sum_{t \in I(c_j)} \text{IDF}(t)}{\sum_{t \in T(c_j)} \text{IDF}(t)} \right)$$

### 2.4 Noisy-OR Aggregation across Contributing Conditions
Multiple condition rows often point to the same underlying canonical nutrient group (e.g. Vitamin A deficiency exhibiting both night blindness and xerophthalmia). Individual row evidence is combined using independent failure complementation (Noisy-OR):
$$P_{\text{combined}}(\text{Nutrient}) = 1.0 - \prod_{c_j \in C_{\text{nut}}} \Big(1.0 - S_{\text{row}}(c_j)\Big)$$

### 2.5 Score Normalization and Heuristic Demo Risk Bands
$$\text{Reference Match \%} = \min\Big(95.0, \, \text{round}\big(100.0 \times P_{\text{combined}}, \, 1\big)\Big)$$
- Strictly capped at **95.0%** to reflect clinical non-definitiveness.
- **Demo Risk Bands:**
  - **High:** $\ge 60.0\%$
  - **Moderate:** $30.0\% \le \text{Score} < 60.0\%$
  - **Low:** $< 30.0\%$

---

## 3. Computer Vision Quality Gate & Shortcut Mitigation
**Source Implementation:** `backend/app/api/v1/medscan.py` & `ml/service/app.py`

### 3.1 Three-Point Automated Image Audit
1. **Payload Limit:** File buffer $\le 5,242,880 \text{ bytes}$ (5 MB).
2. **Sharpness Gate (Laplacian Variance):**
   $$\text{Var}(\Delta I) = \frac{1}{HW} \sum_{x,y} \Big(\nabla^2 I(x,y) - \mu_{\Delta}\Big)^2 \ge 50.0$$
   Images with variance $< 50.0$ are rejected as motion-blurred or out of focus.
3. **Illumination Gate (Mean Luminance):**
   $$40.0 \le \bar{Y} \le 225.0$$
   Where $Y = 0.299R + 0.587G + 0.114B$. Images outside this band are rejected as under-exposed or severely washed out.

### 3.2 Dataset-Shortcut Penalty Weighting
Because public medical image datasets carry sensor and background biases, vision model confidences are damped when proposing reference tags:
$$W_{\text{candidate}} = (1.0 - \lambda_{\text{penalty}}) \times C_{\text{model}} + B_{\text{checklist}}$$
- Eyes: $\lambda = 0.15$
- Hair: $\lambda = 0.15$
- Lips: $\lambda = 0.20$
- Skin: $\lambda = 0.25$
- Tongue: $\lambda = 0.25$
- Nails: $\lambda = 0.30$
- Combined: $\lambda = 0.50$
