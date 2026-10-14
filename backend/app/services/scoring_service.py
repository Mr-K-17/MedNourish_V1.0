"""Scoring Service for Deterministic Reference Match Calculations.

Implements Phase 2 / docs/SCORING_SPEC.md:
- Inverse Document Frequency (IDF) weighting for condition row keywords.
- Small-evidence shrinkage so single tags cannot yield 100% (capped at 95.0%).
- Noisy-OR aggregation across adult-eligible condition rows for each nutrient group.
- Demo risk bands: High (>= 60), Moderate (30-59), Low (< 30).
- Retains old tag-count fields for transparency ("why" details).
- Strictly preserves SAF-09 (nutritional only) and SAF-10 (pediatric exclusions).
- Fully deterministic and monotonic.
"""

import math
from typing import Any, Dict, List, Optional, Set
from app.services.knowledge_service import (
    KnowledgeRepository,
    ReferenceEntry,
    knowledge_repo,
    normalize_tag,
    PACKAGE_VERSION,
    MATCHER_VERSION,
)

KIND_REFERENCE_MATCH = "Reference match %"
RISK_BAND_LABEL = "Demo risk band (heuristic, not clinical)"
EXPLANATION_REFERENCE_MATCH = (
    "Deterministic coverage of reference database symptom patterns, not a clinical diagnosis or test."
)

# Thresholds per docs/SCORING_SPEC.md & owner amendments
THRESHOLD_HIGH = 60.0
THRESHOLD_MODERATE = 30.0


def calculate_risk_band(pct: float) -> str:
    """Returns heuristic demo risk band."""
    if pct >= THRESHOLD_HIGH:
        return "High"
    elif pct >= THRESHOLD_MODERATE:
        return "Moderate"
    return "Low"


class ScoringEngine:
    """Computes IDF-weighted reference match percentages and noisy-OR nutrient groupings."""

    def __init__(self, repo: Optional[KnowledgeRepository] = None):
        self.repo = repo or knowledge_repo
        self.idf_cache: Dict[str, float] = {}
        self._compute_idf_table()

    def _compute_idf_table(self) -> None:
        """Precomputes smoothed IDF weights for all keywords in eligible entries."""
        eligible = self.repo.eligible_entries
        total_docs = len(eligible)
        df_counts: Dict[str, int] = {}

        for entry in eligible:
            for kw in entry.normalized_keywords:
                df_counts[kw] = df_counts.get(kw, 0) + 1

        for kw, df in df_counts.items():
            # Smoothed IDF: ln((N + 1) / (df + 1)) + 1.0
            self.idf_cache[kw] = math.log((total_docs + 1.0) / (df + 1.0)) + 1.0

    def get_idf(self, keyword: str) -> float:
        """Returns IDF for normalized keyword, with fallback for unseen keywords."""
        if keyword in self.idf_cache:
            return self.idf_cache[keyword]
        total_docs = len(self.repo.eligible_entries)
        return math.log(total_docs + 1.0) + 1.0

    def score_condition_row(self, entry: ReferenceEntry, user_tags: Set[str]) -> Dict[str, Any]:
        """Calculates IDF-weighted match percentage and shrinkage for a condition row."""
        matched = entry.normalized_keywords.intersection(user_tags)
        m = len(matched)
        total_kw = len(entry.normalized_keywords)

        if m == 0 or total_kw == 0:
            return {
                "class_label": entry.class_label,
                "body_region": entry.body_region,
                "category": entry.category,
                "vitamin_deficiency": entry.vitamin_deficiency,
                "row_match_percentage": 0.0,
                "matched_tags": [],
                "match_count": 0,
                "total_condition_tags": total_kw,
            }

        sum_matched_idf = sum(self.get_idf(kw) for kw in matched)
        sum_total_idf = sum(self.get_idf(kw) for kw in entry.normalized_keywords)
        raw_ratio = sum_matched_idf / sum_total_idf if sum_total_idf > 0 else 0.0

        # Small-evidence shrinkage factor: m / (m + 0.2)
        # Prevents 1 tag from ever yielding 100% or near-100%
        shrinkage = m / (m + 0.2)
        raw_pct = 100.0 * raw_ratio * shrinkage

        # Hard cap at 95.0%
        row_pct = min(95.0, round(raw_pct, 1))

        return {
            "class_label": entry.class_label,
            "body_region": entry.body_region,
            "category": entry.category,
            "vitamin_deficiency": entry.vitamin_deficiency,
            "row_match_percentage": row_pct,
            "matched_tags": sorted(list(matched)),
            "match_count": m,
            "total_condition_tags": total_kw,
        }

    def evaluate_tags(
        self, user_tags: List[str], region_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluates user tags across all eligible rows and aggregates by nutrient via noisy-OR."""
        norm_inputs = {normalize_tag(t) for t in user_tags if normalize_tag(t)}

        # If empty, return standard INSUFFICIENT_INFORMATION structure
        if not norm_inputs:
            return {
                "status": "INSUFFICIENT_INFORMATION",
                "message": "Fewer tags than the minimum required were selected. Please select one or more symptom tags.",
                "disclaimer": self.repo.match_symptoms([])["disclaimer"],
                "nutrient_scores": [],
                "matched_entries": [],
                "unmatched_user_tags": [],
                "package_version": PACKAGE_VERSION,
                "matcher_version": MATCHER_VERSION,
            }

        candidates = self.repo.eligible_entries
        if region_filter:
            reg_norm = region_filter.strip().upper()
            candidates = [c for c in candidates if c.body_region == reg_norm]

        # Group rows by nutrient
        nutrient_rows: Dict[str, List[Dict[str, Any]]] = {}
        all_matched_tags: Set[str] = set()
        active_condition_matches: List[Dict[str, Any]] = []

        for entry in candidates:
            res = self.score_condition_row(entry, norm_inputs)
            if res["match_count"] > 0:
                all_matched_tags.update(res["matched_tags"])
                active_condition_matches.append(res)
                nut = entry.vitamin_deficiency.strip() or "General Nutritional"
                if nut not in nutrient_rows:
                    nutrient_rows[nut] = []
                nutrient_rows[nut].append(res)

        unmatched = sorted(list(norm_inputs - all_matched_tags))

        if not active_condition_matches:
            return {
                "status": "INSUFFICIENT_INFORMATION",
                "message": (
                    "No educational reference associations match the selected symptom tags. "
                    "This does not indicate absence of health conditions. Consult a qualified clinician for professional evaluation."
                ),
                "disclaimer": self.repo.match_symptoms(["dummy"])["disclaimer"],
                "nutrient_scores": [],
                "matched_entries": [],
                "unmatched_user_tags": unmatched,
                "package_version": PACKAGE_VERSION,
                "matcher_version": MATCHER_VERSION,
            }

        # Compute noisy-OR per nutrient group
        nutrient_scores: List[Dict[str, Any]] = []
        for nutrient, rows in nutrient_rows.items():
            # Combine probabilities: 1 - prod(1 - p_r / 100)
            prod_complement = 1.0
            nut_matched_tags: Set[str] = set()
            for r in rows:
                p_r = r["row_match_percentage"] / 100.0
                prod_complement *= (1.0 - p_r)
                nut_matched_tags.update(r["matched_tags"])

            noisy_or_pct = min(95.0, round(100.0 * (1.0 - prod_complement), 1))
            risk_band = calculate_risk_band(noisy_or_pct)

            # Sort contributing rows by row_match_percentage descending
            sorted_rows = sorted(
                rows,
                key=lambda x: (-x["row_match_percentage"], -x["match_count"], x["class_label"]),
            )

            nutrient_scores.append({
                "nutrient": nutrient,
                "percentage": noisy_or_pct,
                "percentage_kind": KIND_REFERENCE_MATCH,
                "percentage_explanation": EXPLANATION_REFERENCE_MATCH,
                "risk_band": risk_band,
                "risk_band_label": RISK_BAND_LABEL,
                "matched_tags": sorted(list(nut_matched_tags)),
                "contributing_rows": sorted_rows,
                "kind": "reference_match",
            })

        # Sort nutrient scores descending by percentage, then nutrient name
        nutrient_scores.sort(key=lambda x: (-x["percentage"], x["nutrient"]))

        # Format matched_entries for backward compatibility with existing tests and UI
        formatted_matches: List[Dict[str, Any]] = []
        sorted_condition_matches = sorted(
            active_condition_matches,
            key=lambda x: (-x["match_count"], -(x["match_count"] / x["total_condition_tags"]), x["class_label"]),
        )
        for m in sorted_condition_matches:
            formatted_matches.append({
                "class_label": m["class_label"],
                "body_region": m["body_region"],
                "category": m["category"],
                "vitamin_deficiency_association": m["vitamin_deficiency"],
                "matched_tags": m["matched_tags"],
                "match_count": m["match_count"],
                "total_condition_tags": m["total_condition_tags"],
                "row_match_percentage": m["row_match_percentage"],
                "review_status": "unreviewed draft",
            })

        return {
            "status": "MATCHES_FOUND",
            "message": f"Identified {len(nutrient_scores)} nutrient reference patterns across {len(formatted_matches)} conditions.",
            "disclaimer": self.repo.match_symptoms(["dummy"])["disclaimer"],
            "nutrient_scores": nutrient_scores,
            "matched_entries": formatted_matches,
            "unmatched_user_tags": unmatched,
            "package_version": PACKAGE_VERSION,
            "matcher_version": MATCHER_VERSION,
        }


scoring_service = ScoringEngine()
