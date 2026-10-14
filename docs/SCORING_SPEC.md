# MedNourish — Reference Match Scoring Specification (v2.0)
============================================================
Document: docs/SCORING_SPEC.md
Author: MedNourish Engineering
Status: Active / Canonical Reference
Amendments: C-34, C-35

## 1. Overview and Clinical Safety Guardrails

MedNourish calculates deterministic **Reference Match %** scores from user-reported symptom tags against curated reference database associations.
In strict adherence to owner amendments **C-34** and **C-35**:
1. All percentage values are explicitly labelled by kind: **"Reference match %"** (or in multi-source pipelines, "Model %" / "Image model %").
2. Percentages represent **deterministic database pattern coverage**, NEVER medical disease or deficiency probabilities.
3. Risk bands are strictly educational demo heuristics:
   - **High**: $\ge 60\%$
   - **Moderate**: $30\% - 59\%$
   - **Low**: $< 30\%$
   - Label: `"Demo risk band (heuristic, not clinical)"`
4. Pediatric and non-nutritional records remain strictly excluded from adult matching (SAF-09, SAF-10).

---

## 2. Mathematical Formulation

### 2.1 Inverse Document Frequency (IDF) Weighting
Let $N$ be the total number of adult nutritional condition rows in the curated reference knowledge base ($N \approx 95$).
For each canonical symptom keyword $w$, let $df(w)$ be the document frequency (number of condition rows where $w$ appears).
Smoothed IDF is computed as:
$$\text{IDF}(w) = \ln\left(\frac{N + 1}{df(w) + 1}\right) + 1.0$$

Keywords with lower document frequency (rarer symptoms such as `spoonshapednails` or `nightblindness`) receive higher weights than ubiquitous symptoms (such as `fatigue`).

### 2.2 Condition Row Match Percentage ($P_r$)
For a given condition row $r$ with canonical keyword set $K_r$ and user selected tag set $U$:
- Matched keywords: $M_r = K_r \cap U$
- Matched count: $m = |M_r|$
- If $m = 0$, $P_r = 0.0$

If $m > 0$, the raw IDF coverage ratio is:
$$S_r = \frac{\sum_{w \in M_r} \text{IDF}(w)}{\sum_{w \in K_r} \text{IDF}(w)}$$

To prevent a single isolated symptom from producing misleadingly high certainty, a **small-evidence shrinkage factor** $\sigma(m)$ is applied:
$$\sigma(m) = \frac{m}{m + 0.2}$$

The final condition row match percentage is capped at $95.0\%$:
$$P_r = \min\left(95.0, \text{round}\left(100.0 \times S_r \times \sigma(m), 1\right)\right)$$

### 2.3 Nutrient Group Aggregation (Noisy-OR)
Multiple condition rows often point to the same underlying nutrient deficiency (e.g. Vitamin A manifests across Eye and Skin conditions).
To aggregate multiple independent line items into an overall nutrient match without naive linear addition exceeding 100%, a **noisy-OR** combination rule is applied over all eligible condition rows $R_g$ for nutrient $g$:

$$Q_g = \prod_{r \in R_g} \left(1.0 - \frac{P_r}{100.0}\right)$$
$$P_{\text{nutrient}} = \min\left(95.0, \text{round}\left(100.0 \times (1.0 - Q_g), 1\right)\right)$$

If no rows match for nutrient $g$, $P_{\text{nutrient}} = 0.0$.

---

## 3. Properties and Invariants

1. **Determinism**: For identical input tag sets $U$, output percentages and ranking are bitwise identical across all runs.
2. **Monotonicity**: Adding an additional symptom tag $t \notin U$ will never decrease any row percentage $P_r$ or nutrient group percentage $P_{\text{nutrient}}$.
3. **Evidence Bounds**:
   - $0.0 \le P_r \le 95.0$
   - $0.0 \le P_{\text{nutrient}} \le 95.0$
   - A single matching tag can NEVER yield 100% match.
4. **Transparency ("Why" Details)**:
   Every nutrient group output retains the full breakdown:
   - Matched tags ($M_r$)
   - Total condition tags ($|K_r|$)
   - Raw match counts ($m$)
   - Contributing condition rows with their individual row percentages.

---

## 4. Output Schema Representation

```json
{
  "nutrient": "Vitamin A",
  "percentage": 78.4,
  "percentage_kind": "Reference match %",
  "percentage_explanation": "Deterministic coverage of reference database symptom patterns, not a clinical diagnosis or test.",
  "risk_band": "High",
  "risk_band_label": "Demo risk band (heuristic, not clinical)",
  "matched_tags": ["nightblindness", "eyedryness"],
  "contributing_rows": [
    {
      "class_label": "Bitot's spots",
      "body_region": "EYES",
      "row_match_percentage": 78.4,
      "matched_tags": ["nightblindness", "eyedryness"],
      "total_condition_tags": 3,
      "match_count": 2
    }
  ]
}
```
