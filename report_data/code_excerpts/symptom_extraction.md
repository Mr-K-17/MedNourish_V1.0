# Code Excerpt: `symptom_extraction`

- **Repository Path**: [`backend/app/services/extraction_service.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/services/extraction_service.py#L85-L116)
- **Lines**: 85–116 (32 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Parses unstructured user text using clinical synonym dictionaries and negation detection rules ('no', 'not', 'denies'). Prevents false-positive symptom confirmation without requiring external LLM dependencies.

```python
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
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
