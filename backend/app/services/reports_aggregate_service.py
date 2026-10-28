"""Reports Aggregate & Multi-Engine Analytics Service (Phase 5).

Guarantees:
- Aggregates up to 5 most recent SavedSummary snapshots with recency weights:
  Base weights = [0.35, 0.25, 0.20, 0.12, 0.08] normalized to sum 1.0.
- Blends Reference %, XGBoost %, LightGBM %, and Image %.
- Generates payloads for all 6 Recharts visual components:
  1. Grouped Bar (nutrient x engine source)
  2. Ranked Horizontal Bar (final % and risk band)
  3. Radar (multi-axial nutrient pattern)
  4. Donut (risk band counts)
  5. Timeline (longitudinal tracking over check-in dates)
  6. Heatmap (body-region x nutrient matrix)
- Generates Final Report Card with probable deficiencies, demo risk band, supporting sources, and suggested measures.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.user import SavedSummary
from app.schemas.reports import (
    AggregatedNutrientItem,
    ChartDataPayload,
    FinalReportCard,
    ReportsAggregateResponse,
)

logger = logging.getLogger(__name__)

BASE_RECENCY_WEIGHTS = [0.35, 0.25, 0.20, 0.12, 0.08]


class ReportsAggregateService:
    """Computes recency-weighted multi-engine aggregation and chart structures."""

    def compute_aggregate(self, db: Session, user_id: str) -> ReportsAggregateResponse:
        # Fetch latest up to 5 summaries for user, ordered by creation date desc
        summaries: List[SavedSummary] = (
            db.query(SavedSummary)
            .filter(SavedSummary.user_id == user_id)
            .order_by(SavedSummary.created_at.desc())
            .limit(5)
            .all()
        )

        n = len(summaries)
        if n == 0:
            return self._empty_response()

        # Calculate normalized recency weights
        raw_weights = BASE_RECENCY_WEIGHTS[:n]
        total_weight = sum(raw_weights)
        norm_weights = [round(w / total_weight, 4) for w in raw_weights]

        # Extract snapshot scores per summary
        # summary_scores[i] = { nutrient: { "ref": float, "xgb": float, "lgb": float, "img": float, "final": float, "region": str } }
        parsed_snapshots: List[Dict[str, Dict[str, float]]] = []
        snapshot_metadata: List[Dict[str, Any]] = []

        for summary in summaries:
            scores_map: Dict[str, Dict[str, float]] = {}
            region = summary.body_region_filter or "General"
            snapshot_metadata.append({
                "id": summary.id,
                "created_at": summary.created_at.strftime("%Y-%m-%d %H:%M"),
                "region": region,
            })

            # Check snapshot_scores_json first
            if summary.snapshot_scores_json:
                try:
                    loaded = json.loads(summary.snapshot_scores_json)
                    for nut, data in loaded.items():
                        scores_map[nut] = {
                            "reference_pct": float(data.get("reference_pct", 0.0)),
                            "xgboost_pct": float(data.get("xgboost_pct", 0.0)),
                            "lightgbm_pct": float(data.get("lightgbm_pct", 0.0)),
                            "image_pct": float(data.get("image_pct", 0.0)),
                            "final_pct": float(data.get("final_pct", 0.0)),
                            "body_region": region,
                        }
                except Exception as e:
                    logger.debug(f"Failed to parse snapshot_scores_json for {summary.id}: {e}")

            # Fallback to matched_entries_json if snapshot_scores_json is empty
            if not scores_map and summary.matched_entries_json:
                try:
                    entries = json.loads(summary.matched_entries_json)
                    for entry in entries:
                        # Extract deficiency/nutrient name
                        def_name = entry.get("deficiency_name") or entry.get("title") or entry.get("deficiency") or "General"
                        match_pct = float(entry.get("match_percentage", 0.0))
                        scores_map[def_name] = {
                            "reference_pct": match_pct,
                            "xgboost_pct": 0.0,
                            "lightgbm_pct": 0.0,
                            "image_pct": 0.0,
                            "final_pct": match_pct,
                            "body_region": region,
                        }
                except Exception as e:
                    logger.debug(f"Failed to parse matched_entries_json for {summary.id}: {e}")

            parsed_snapshots.append(scores_map)

        # Collect all unique nutrient keys
        all_nutrients = set()
        for snap in parsed_snapshots:
            all_nutrients.update(snap.keys())

        # Aggregate nutrient scores using recency weights
        aggregated_items: List[AggregatedNutrientItem] = []
        for nut in all_nutrients:
            agg_ref = 0.0
            agg_xgb = 0.0
            agg_lgb = 0.0
            agg_img = 0.0
            agg_final = 0.0

            for i, snap in enumerate(parsed_snapshots):
                w = norm_weights[i]
                if nut in snap:
                    data = snap[nut]
                    agg_ref += w * data["reference_pct"]
                    agg_xgb += w * data["xgboost_pct"]
                    agg_lgb += w * data["lightgbm_pct"]
                    agg_img += w * data["image_pct"]
                    agg_final += w * data["final_pct"]

            final_pct_val = round(agg_final, 1)
            # Determine demo risk band
            if final_pct_val >= 60.0:
                band = "High (heuristic, not clinical)"
            elif final_pct_val >= 30.0:
                band = "Moderate (heuristic, not clinical)"
            else:
                band = "Low (heuristic, not clinical)"

            aggregated_items.append(
                AggregatedNutrientItem(
                    nutrient=nut,
                    reference_pct=round(agg_ref, 1),
                    xgboost_pct=round(agg_xgb, 1),
                    lightgbm_pct=round(agg_lgb, 1),
                    image_pct=round(agg_img, 1),
                    final_pct=final_pct_val,
                    demo_risk_band=band,
                )
            )

        # Sort aggregated items descending by final_pct
        aggregated_items.sort(key=lambda x: x.final_pct, reverse=True)

        # Build Chart Payloads
        # 1. Grouped Bar
        grouped_bar = [
            {
                "nutrient": item.nutrient,
                "reference_pct": item.reference_pct,
                "xgboost_pct": item.xgboost_pct,
                "lightgbm_pct": item.lightgbm_pct,
                "image_pct": item.image_pct,
            }
            for item in aggregated_items[:8]
        ]

        # 2. Ranked Horizontal
        ranked_horizontal = [
            {
                "nutrient": item.nutrient,
                "final_pct": item.final_pct,
                "demo_risk_band": item.demo_risk_band,
            }
            for item in aggregated_items[:8]
        ]

        # 3. Radar Chart (multi-axial)
        radar_items = [
            {
                "nutrient": item.nutrient,
                "final_pct": item.final_pct,
                "fullMark": 100,
            }
            for item in aggregated_items[:6]
        ]
        # Pad radar to at least 3 points if needed
        while len(radar_items) < 3 and len(aggregated_items) < 3:
            radar_items.append({"nutrient": f"Baseline {len(radar_items)+1}", "final_pct": 0.0, "fullMark": 100})

        # 4. Donut Risk Band Counts
        band_counts = {"High": 0, "Moderate": 0, "Low": 0}
        for item in aggregated_items:
            if "high" in item.demo_risk_band.lower():
                band_counts["High"] += 1
            elif "moderate" in item.demo_risk_band.lower():
                band_counts["Moderate"] += 1
            else:
                band_counts["Low"] += 1

        donut_risk = [
            {"band": "High Risk Band", "count": band_counts["High"]},
            {"band": "Moderate Risk Band", "count": band_counts["Moderate"]},
            {"band": "Low Risk Band", "count": band_counts["Low"]},
        ]

        # 5. Timeline (chronological order)
        timeline = []
        top_nutrients_list = [item.nutrient for item in aggregated_items[:4]]
        # Iterate in chronological order (reverse of desc)
        for i in reversed(range(n)):
            meta = snapshot_metadata[i]
            point: Dict[str, Any] = {"date": meta["created_at"]}
            snap = parsed_snapshots[i]
            for top_nut in top_nutrients_list:
                point[top_nut] = snap.get(top_nut, {}).get("final_pct", 0.0)
            timeline.append(point)

        # 6. Heatmap (body_region x nutrient)
        heatmap = []
        regions_found = set()
        for snap in parsed_snapshots:
            for nut, data in snap.items():
                r = data.get("body_region", "General")
                regions_found.add(r)

        for r in sorted(list(regions_found)):
            for item in aggregated_items[:6]:
                # Find maximum match value in this region across snapshots
                max_val = 0.0
                for snap in parsed_snapshots:
                    if item.nutrient in snap and snap[item.nutrient].get("body_region") == r:
                        max_val = max(max_val, snap[item.nutrient]["final_pct"])
                heatmap.append({
                    "body_region": r,
                    "nutrient": item.nutrient,
                    "value": round(max_val, 1),
                })

        chart_payload = ChartDataPayload(
            grouped_bar=grouped_bar,
            ranked_horizontal=ranked_horizontal,
            radar=radar_items,
            donut_risk=donut_risk,
            timeline=timeline,
            heatmap=heatmap,
        )

        # Final Report Card
        top_significant = [item for item in aggregated_items if item.final_pct >= 30.0]
        if top_significant:
            prob_def = "Screening summary: probable deficiency pattern(s): " + ", ".join(
                [f"{it.nutrient} ({it.final_pct}%)" for it in top_significant[:3]]
            )
        else:
            prob_def = "Screening summary: No high-risk deficiency patterns observed above 30% threshold."

        # Maximum risk band across top nutrients
        max_band = "Low (heuristic, not clinical)"
        if any("high" in it.demo_risk_band.lower() for it in aggregated_items[:3]):
            max_band = "High (heuristic, not clinical)"
        elif any("moderate" in it.demo_risk_band.lower() for it in aggregated_items[:3]):
            max_band = "Moderate (heuristic, not clinical)"

        supporting_sources = [
            "Curated Nutritional Literature Symptom Reference Mapping",
            "Multi-Class Tabular ML Model (XGBoost, unverified data)",
            "Multi-Class Tabular ML Model (LightGBM, unverified data)",
            "Anatomical Computer Vision Assessment (MobileNetV2 Float32 TFLite)",
        ]

        suggested_measures = [
            "Prioritize varied, nutrient-dense whole foods rich in highlighted vitamins and minerals.",
            "Maintain consistent daily hydration, adequate restorative sleep, and moderate physical activity.",
            "Consult a licensed dietitian or physician for diagnostic serum blood testing before considering major dietary interventions.",
        ]
        if "high" in max_band.lower():
            suggested_measures.insert(
                0,
                "Consult a qualified healthcare professional soon regarding physical signs and laboratory evaluation (no timeframes implied).",
            )

        final_card = FinalReportCard(
            probable_deficiencies=prob_def,
            demo_risk_band=max_band,
            supporting_sources=supporting_sources,
            suggested_measures=suggested_measures,
            disclaimer="Educational prototype: not a medical diagnosis, clinical treatment plan, or medication prescription.",
            emergency_link="/emergency",
        )

        return ReportsAggregateResponse(
            entries_count=n,
            recency_weights=norm_weights,
            aggregated_nutrients=aggregated_items,
            chart_data=chart_payload,
            final_report_card=final_card,
        )

    def _empty_response(self) -> ReportsAggregateResponse:
        return ReportsAggregateResponse(
            entries_count=0,
            recency_weights=[],
            aggregated_nutrients=[],
            chart_data=ChartDataPayload(
                grouped_bar=[],
                ranked_horizontal=[],
                radar=[],
                donut_risk=[],
                timeline=[],
                heatmap=[],
            ),
            final_report_card=FinalReportCard(
                probable_deficiencies="No saved checks available to aggregate.",
                demo_risk_band="Low (heuristic, not clinical)",
                supporting_sources=[],
                suggested_measures=[
                    "Perform a check in MedBot, Symptom Explorer, or MedScan to generate assessment reports."
                ],
                disclaimer="Educational prototype: not a medical diagnosis or clinical treatment plan.",
                emergency_link="/emergency",
            ),
        )


reports_aggregate_service = ReportsAggregateService()
