"""Reference Knowledge Service & Deterministic Matcher Engine.

Implements M1B.1 & M1B.2:
- Loads curated reference CSVs from knowledge/curated/
- Enforces strict safety exclusions:
    * SAF-09: Excludes non-nutritional and normal rows from user matching.
    * SAF-10: Excludes pediatric/infant-specific records (e.g. Menkes disease).
    * SAF-16, SAF-02: Excludes unreviewed treatment, drug, dosage, and supplement details.
- Normalizes input symptom tags.
- Performs deterministic set intersection matching.
- Deterministic ranking:
    1. Match count descending (k)
    2. Ratio of matched tags descending (k / total_keywords)
    3. Lexicographical Class_Label ascending
- Insufficient information rule (SAF-06): k < 1 or empty input returns INSUFFICIENT_INFORMATION.
- Educational prototype disclaimers attached to all outputs (SAF-01, SAF-07).
"""

import csv
import logging
import os
import re
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

PACKAGE_VERSION = "curated_v1.0"
MATCHER_VERSION = "matcher_spec_v1.0"

# Explicit pediatric terms to exclude from adult (18+) matching results per SAF-10
PEDIATRIC_TERMS = {
    "infant",
    "infants",
    "child",
    "children",
    "pediatric",
    "paediatric",
    "menkes",
    "newborn",
    "neonatal",
    "toddler",
}


def normalize_tag(tag: str) -> str:
    """Normalizes an anatomical symptom tag to canonical alphanumeric string.

    Lowercases, removes punctuation, trims spaces, replaces underscores/hyphens.
    """
    if not tag:
        return ""
    # Lowercase and convert hyphens/underscores to spaces
    t = tag.lower().strip()
    t = re.sub(r"[_\-\/\(\)]+", " ", t)
    # Remove any extra punctuation
    t = re.sub(r"[^a-z0-9\s]", "", t)
    # Collapse multiple whitespaces
    t = re.sub(r"\s+", " ", t).strip()
    return t


class ReferenceEntry:
    """Represents a curated reference condition class."""

    def __init__(
        self,
        class_label: str,
        body_region: str,
        category: str,
        vitamin_deficiency: str,
        keywords_raw: str,
        is_nutritional: bool = True,
        is_adult_eligible: bool = True,
    ):
        self.class_label = class_label.strip()
        self.body_region = body_region.strip().upper()
        self.category = category.strip()
        self.vitamin_deficiency = vitamin_deficiency.strip()
        self.is_nutritional = is_nutritional
        self.is_adult_eligible = is_adult_eligible

        # Split and normalize keywords
        raw_list = [k.strip() for k in keywords_raw.split(";") if k.strip()]
        self.raw_keywords = raw_list
        self.normalized_keywords: Set[str] = {normalize_tag(k) for k in raw_list if normalize_tag(k)}

    def to_summary_dict(self) -> Dict[str, str]:
        return {
            "class_label": self.class_label,
            "body_region": self.body_region,
            "category": self.category,
            "vitamin_deficiency": self.vitamin_deficiency,
        }


class KnowledgeRepository:
    """In-memory loaded and validated repository of curated reference tables."""

    def __init__(self, curated_dir: Optional[str] = None):
        if curated_dir is None:
            # Default to repo knowledge/curated path relative to backend
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            curated_dir = os.path.join(base_dir, "knowledge", "curated")
        self.curated_dir = curated_dir
        self.entries: List[ReferenceEntry] = []
        self.eligible_entries: List[ReferenceEntry] = []
        self.tags_by_region: Dict[str, List[Dict[str, str]]] = {}
        self.load_data()

    def load_data(self) -> None:
        """Loads and filters curated reference tables."""
        master_file = os.path.join(
            self.curated_dir, "MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv"
        )
        if not os.path.exists(master_file):
            logger.error("Curated master file not found at %s", master_file)
            return

        entries: List[ReferenceEntry] = []
        with open(master_file, "r", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                class_label = row.get("Class_Label", "").strip()
                body_region = row.get("Body_Region", "").strip().upper()
                category = row.get("Category", "").strip()
                vitamin_def = row.get("Vitamin_Deficiency", "").strip()
                keywords = row.get("Symptom_Keywords", "").strip()

                # Safety Check 1: Exclude Normal and Non_Nutritional categories (SAF-09, C-18)
                is_nutritional = (category == "Nutritional")

                # Safety Check 2: Exclude Pediatric & infant-specific records (SAF-10)
                full_text = f"{class_label} {category} {vitamin_def} {keywords}".lower()
                is_pediatric = any(term in full_text for term in PEDIATRIC_TERMS)
                is_adult_eligible = not is_pediatric

                entry = ReferenceEntry(
                    class_label=class_label,
                    body_region=body_region,
                    category=category,
                    vitamin_deficiency=vitamin_def,
                    keywords_raw=keywords,
                    is_nutritional=is_nutritional,
                    is_adult_eligible=is_adult_eligible,
                )
                entries.append(entry)

        self.entries = entries

        # Eligible for adult reference exploration (SAF-09, SAF-10)
        self.eligible_entries = [
            e for e in self.entries if e.is_nutritional and e.is_adult_eligible
        ]

        # Build browseable tags grouped by body region
        region_map: Dict[str, Dict[str, str]] = {}
        for entry in self.eligible_entries:
            reg = entry.body_region
            if reg not in region_map:
                region_map[reg] = {}
            for raw_kw in entry.raw_keywords:
                norm = normalize_tag(raw_kw)
                if norm and norm not in region_map[reg]:
                    region_map[reg][norm] = raw_kw

        self.tags_by_region = {
            reg: [{"tag": norm, "label": raw} for norm, raw in sorted(tags.items())]
            for reg, tags in sorted(region_map.items())
        }
        logger.info(
            "KnowledgeRepository loaded %d total entries, %d adult nutritional entries across %d regions.",
            len(self.entries),
            len(self.eligible_entries),
            len(self.tags_by_region),
        )

    def match_symptoms(
        self, user_tags: List[str], region_filter: Optional[str] = None
    ) -> Dict:
        """Executes deterministic reference matching per docs/REFERENCE_MATCHER_SPEC.md."""
        disclaimer = (
            "MEDNOURISH is an educational prototype. Results are reference-table matches and general health education, "
            "never medical diagnoses, predictions, or risk assessments. Discuss any symptom concerns with a qualified clinician."
        )

        # 1. Normalize input tags
        normalized_inputs = {normalize_tag(t) for t in user_tags if normalize_tag(t)}

        # 2. Check for empty inputs (SAF-06 Insufficient Information)
        if not normalized_inputs:
            return {
                "status": "INSUFFICIENT_INFORMATION",
                "message": "Fewer tags than the minimum required were selected. Please select one or more symptom tags to look up educational reference associations, or speak with a clinician.",
                "disclaimer": disclaimer,
                "matched_entries": [],
                "unmatched_user_tags": [],
                "package_version": PACKAGE_VERSION,
                "matcher_version": MATCHER_VERSION,
            }

        # 3. Filter candidate pool by region if specified
        candidates = self.eligible_entries
        if region_filter:
            norm_filter = region_filter.strip().upper()
            candidates = [c for c in candidates if c.body_region == norm_filter]

        # 4. Perform set intersection and score
        matched_results = []
        all_matched_tags: Set[str] = set()

        for entry in candidates:
            intersection = normalized_inputs.intersection(entry.normalized_keywords)
            k = len(intersection)
            if k > 0:
                all_matched_tags.update(intersection)
                total_kw = len(entry.normalized_keywords)
                ratio = k / total_kw if total_kw > 0 else 0.0
                matched_results.append({
                    "entry": entry,
                    "matched_tags": sorted(list(intersection)),
                    "match_count": k,
                    "total_condition_tags": total_kw,
                    "match_ratio": ratio,
                })

        # 5. Deterministic tie-breaking sort:
        #    Primary: match_count descending
        #    Secondary: match_ratio descending
        #    Tertiary: class_label ascending
        matched_results.sort(
            key=lambda x: (-x["match_count"], -x["match_ratio"], x["entry"].class_label)
        )

        unmatched_tags = sorted(list(normalized_inputs - all_matched_tags))

        # 6. Check for zero matches (SAF-06)
        if not matched_results:
            return {
                "status": "INSUFFICIENT_INFORMATION",
                "message": "No educational reference associations match the selected symptom tags. This does not indicate absence of health conditions. Consult a qualified clinician for professional evaluation.",
                "disclaimer": disclaimer,
                "matched_entries": [],
                "unmatched_user_tags": unmatched_tags,
                "package_version": PACKAGE_VERSION,
                "matcher_version": MATCHER_VERSION,
            }

        # 7. Format clean, safe user-facing payload (prohibits diagnosis, probabilities, or treatment fields)
        formatted_matches = []
        for res in matched_results:
            e: ReferenceEntry = res["entry"]
            formatted_matches.append({
                "class_label": e.class_label,
                "body_region": e.body_region,
                "category": e.category,
                "vitamin_deficiency_association": e.vitamin_deficiency,
                "matched_tags": res["matched_tags"],
                "match_count": res["match_count"],
                "total_condition_tags": res["total_condition_tags"],
                "review_status": "unreviewed draft",
            })

        return {
            "status": "MATCHES_FOUND",
            "message": f"Identified {len(formatted_matches)} reference-table associations matching selected tags.",
            "disclaimer": disclaimer,
            "matched_entries": formatted_matches,
            "unmatched_user_tags": unmatched_tags,
            "package_version": PACKAGE_VERSION,
            "matcher_version": MATCHER_VERSION,
        }


# Global singleton repository instance
knowledge_repo = KnowledgeRepository()
