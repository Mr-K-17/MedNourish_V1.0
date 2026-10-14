"""Symptom Text Extraction Service for MedBot Free-Text Input.

Implements Phase 2 (c):
- Normalizes free-text symptom descriptions.
- Matches against the 267 canonical reference keywords.
- Matches against knowledge/curated/synonyms.yaml (>=150 everyday phrasings).
- Enforces negation window ('no', 'not', 'without', "don't have", etc.) to skip negated symptoms.
- Uses difflib.SequenceMatcher with ratio >= 0.88 for fuzzy matching.
- Returns extracted chips with source phrase for user confirmation.
- Never stores raw user text in database or server logs (C-23, PRIV-01).
"""

import difflib
import logging
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from app.services.knowledge_service import knowledge_repo, normalize_tag

logger = logging.getLogger(__name__)

NEGATION_TOKENS = {
    "no",
    "not",
    "without",
    "dont",
    "don't",
    "havent",
    "haven't",
    "free",
    "neither",
    "nor",
    "never",
    "denies",
    "denied",
    "zero",
}


def load_synonyms_from_yaml(filepath: str) -> Dict[str, str]:
    """Parses synonyms.yaml cleanly without third-party dependencies."""
    synonyms: Dict[str, str] = {}
    if not os.path.exists(filepath):
        logger.warning("Synonyms file not found at %s", filepath)
        return synonyms

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("version:") or line.startswith("synonyms:"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k_clean = k.strip()
                v_clean = v.strip()
                # Remove inline comment if present
                if "#" in v_clean:
                    v_clean = v_clean.split("#", 1)[0].strip()
                synonyms[k_clean.lower()] = v_clean.lower()
    return synonyms


class SymptomExtractor:
    """Extracts confirmed canonical symptom tags from free-text using synonyms, negation, and fuzzy match."""

    def __init__(self, curated_dir: Optional[str] = None):
        if curated_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            curated_dir = os.path.join(base_dir, "knowledge", "curated")
        self.curated_dir = curated_dir

        # Load canonical keywords
        self.canonical_keywords: Set[str] = set()
        for entry in knowledge_repo.entries:
            self.canonical_keywords.update(entry.normalized_keywords)

        # Load synonyms
        yaml_path = os.path.join(self.curated_dir, "synonyms.yaml")
        self.synonyms = load_synonyms_from_yaml(yaml_path)

        # Also map normalized forms of canonical tags
        self.all_phrasings: Dict[str, str] = {}
        for phrase, canonical in self.synonyms.items():
            self.all_phrasings[phrase.lower()] = canonical
        for kw in self.canonical_keywords:
            self.all_phrasings[kw] = kw

    def extract_symptoms(self, text: Optional[str]) -> Dict[str, Any]:
        """Extracts symptoms from text, returning extracted chips with source phrases."""
        if not text or not text.strip():
            return {
                "status": "INSUFFICIENT_INFORMATION",
                "message": "No text provided for extraction.",
                "tags": [],
                "chips": [],
            }

        # Split text into clauses/sentences to respect punctuation boundaries
        clauses = re.split(r"[.!?,;\n]+", text.lower())
        extracted_chips: List[Dict[str, Any]] = []
        seen_tags: Set[str] = set()

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            words = clause.split()
            n_words = len(words)

            # Build list of (word, is_negated) based on negation window (window = 4 words)
            negated_indices: Set[int] = set()
            for i, w in enumerate(words):
                w_clean = re.sub(r"[^a-z0-9']", "", w)
                if w_clean in NEGATION_TOKENS:
                    # Negate next 4 words
                    for j in range(i + 1, min(i + 5, n_words)):
                        negated_indices.add(j)

            # Check phrases of length 6 down to 1
            matched_word_indices: Set[int] = set()
            for length in range(6, 0, -1):
                for start in range(n_words - length + 1):
                    end = start + length
                    # If any word in this span already matched, skip
                    if any(idx in matched_word_indices for idx in range(start, end)):
                        continue

                    # Check if any word in this span is negated
                    is_negated = any(idx in negated_indices for idx in range(start, end))
                    span_words = words[start:end]
                    raw_phrase = " ".join(span_words)
                    clean_phrase = re.sub(r"[^a-z0-9\s]", "", raw_phrase).strip()
                    collapsed_phrase = clean_phrase.replace(" ", "")

                    if not clean_phrase:
                        continue

                    matched_tag: Optional[str] = None
                    confidence = 1.0

                    # 1. Exact match in synonyms or canonical keywords
                    if clean_phrase in self.all_phrasings:
                        matched_tag = self.all_phrasings[clean_phrase]
                    elif collapsed_phrase in self.all_phrasings:
                        matched_tag = self.all_phrasings[collapsed_phrase]
                    elif clean_phrase in self.canonical_keywords:
                        matched_tag = clean_phrase
                    elif collapsed_phrase in self.canonical_keywords:
                        matched_tag = collapsed_phrase

                    # 2. Fuzzy match with difflib >= 0.88 if no exact match
                    if not matched_tag and len(clean_phrase) >= 4:
                        best_match = None
                        best_ratio = 0.0
                        for candidate_phrase, target_tag in self.all_phrasings.items():
                            ratio = difflib.SequenceMatcher(None, clean_phrase, candidate_phrase).ratio()
                            if ratio >= 0.88 and ratio > best_ratio:
                                best_ratio = ratio
                                best_match = target_tag

                        if best_match:
                            matched_tag = best_match
                            confidence = round(best_ratio, 2)

                    if matched_tag:
                        if is_negated:
                            # Skip negated symptom!
                            for idx in range(start, end):
                                matched_word_indices.add(idx)
                            continue

                        for idx in range(start, end):
                            matched_word_indices.add(idx)

                        if matched_tag not in seen_tags:
                            seen_tags.add(matched_tag)
                            extracted_chips.append({
                                "tag": matched_tag,
                                "source_phrase": raw_phrase,
                                "confidence": confidence,
                            })

        if not extracted_chips:
            return {
                "status": "INSUFFICIENT_INFORMATION",
                "message": "No recognized nutritional symptoms detected in description.",
                "tags": [],
                "chips": [],
            }

        return {
            "status": "SYMPTOMS_EXTRACTED",
            "message": f"Extracted {len(extracted_chips)} symptom tags.",
            "tags": sorted(list(seen_tags)),
            "chips": extracted_chips,
        }


symptom_extractor = SymptomExtractor()
