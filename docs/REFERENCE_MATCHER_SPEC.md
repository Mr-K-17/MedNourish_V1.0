# MEDNOURISH — Deterministic Reference-Matching Engine Specification

| Metadata | Specification |
|---|---|
| Milestone | M1B.1 (Knowledge Foundation & Matcher Design) |
| Applies to | MedBot (Questionnaire) & Symptom Reference Explorer |
| Authority | `docs/Architecture.md` Section 8.1, `docs/PRD.md` Section 1, `docs/Rules.md` Section 2 |
| Medical Safety | Educational Prototype (`SAF-01`, `SAF-07`, `C-08`, `C-18`) |

---

## 1. Purpose and Boundaries

The Reference-Matching Engine is a **deterministic, explainable rule engine**. It performs structured set intersection between selected symptom tags and cleaned reference tables (`knowledge/curated/`).

### Strict Negative Boundaries
- **NEVER a Diagnosis:** Matches indicate symptom co-occurrence in medical literature/reference tables, not patient disease confirmation (`SAF-01`).
- **NEVER a Predictive/Risk Score:** Outputs ordered tag counts, never percentages, probabilities, or Low/Moderate/High risk bands (`C-18`, `SAF-17`).
- **NEVER Clinical Treatment:** Recommends consulting a healthcare professional; excludes unreviewed drug doses, supplements, and urgency timeframes (`SAF-02`, `SAF-16`).
- **Adult Scope (18+):** Excludes infant/child-specific rows from adult matching results (`SAF-10`, `C-01`).

---

## 2. Data Sources & Schema Join

### 2.1 Primary Master Table
`knowledge/curated/MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv`
- `Body_Region`: Region string (e.g. `Eyes`, `Hair`, `Lips`, `Nails`, `Skin`, `Tongue`).
- `Category`: Condition group (e.g. `Night_Blindness`, `Hair_Loss`).
- `Nutrient_or_Deficiency`: Target nutrient reference (e.g. `Vitamin_A`, `Biotin_or_Iron`).
- `Symptom_Keywords`: Comma-separated list of normalized canonical keywords.

### 2.2 Regional Detail Tables
`knowledge/curated/{Region}_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- Joined on composite key: `(Body_Region, Category, Vitamin_Deficiency)` to provide safe narrative context and visible physical signs.

---

## 3. Algorithm & Matching Rules

### Step 1: Input Normalization
1. Lowercase all input strings.
2. Strip leading, trailing, and redundant internal whitespace.
3. Replace punctuation (hyphens, underscores, slashes) with space delimiters.
4. Normalize anatomical synonyms using standard vocabulary lookup (e.g., `"hair thinning"` → `"hair_thinning"`).

### Step 2: Set Intersection
Given:
- User selected symptom tag set: $U = \{t_1, t_2, \dots, t_n\}$
- Reference condition class $C_i$ with keyword set: $K_i = \{k_{i1}, k_{i2}, \dots, k_{im}\}$

Compute matched set:
$$M_i = U \cap K_i$$
Match Count:
$$S_i = |M_i|$$

### Step 3: Threshold & Ambiguity Handling
- **Minimum Information Rule (`SAF-06`):**
  If user selects fewer than 1 valid symptom tag, or if $\max_i(S_i) = 0$, return:
  `status: "INSUFFICIENT_INFORMATION"` with neutral prompt to speak with a healthcare provider. Never reassure or report "no problems detected".
- **Ranking & Deterministic Tie-Breaking:**
  1. Primary sort: descending by $S_i$ (match count).
  2. Secondary sort: descending by match ratio ($S_i / |K_i|$).
  3. Tertiary sort: alphabetical by condition class name `Class_Label` (guarantees 100% deterministic, reproducible output).

### Step 4: Output Structure
```json
{
  "status": "MATCHES_FOUND",
  "disclaimer": "MEDNOURISH is an educational prototype. Results are reference-table matches and general health education, not medical diagnoses or predictions.",
  "matched_entries": [
    {
      "body_region": "Eyes",
      "category": "Night_Blindness",
      "reference_label": "Vitamin A Association",
      "matched_tags": ["night_blindness", "dry_eyes"],
      "match_count": 2,
      "total_condition_tags": 4
    }
  ],
  "unmatched_user_tags": ["fatigue"],
  "package_version": "curated_v1.0"
}
```
