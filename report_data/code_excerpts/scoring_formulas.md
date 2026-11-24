# Code Excerpt: `scoring_formulas`

- **Repository Path**: [`backend/app/services/scoring_service.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/services/scoring_service.py#L32-L61)
- **Lines**: 32–61 (30 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Implements the Noisy-OR probabilistic combination and shrinkage scaling factor k = min(1.0, 0.4 + 0.2*m). Clamps probabilities to [0,1] and categorizes risk into High (>=60%), Moderate (>=30%), and Low bands.

```python
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
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
