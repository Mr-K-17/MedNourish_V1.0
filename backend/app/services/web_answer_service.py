"""Web Answer Service for Medical and Nutritional Reference Inquiries.

Spec: Phase 4 / Owner amendments C-33..C-38:
- Queries official medical reference services (MedlinePlus Web Service / NIH ODS).
- Enforces strict domain allowlist: wsearch.nlm.nih.gov, medlineplus.gov, ods.od.nih.gov.
- Bounded network calls: 5.0s timeout, max 2 attempts.
- In-memory cache with 24-hour TTL.
- Strips HTML/XML and strictly truncates output to <= 600 characters.
- Zero privacy leaks: never logs question content, sends zero user identifiers.
- Graceful offline/network failure fallback.
"""

import logging
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Optional
import httpx

logger = logging.getLogger(__name__)

ALLOWED_DOMAINS = {
    "wsearch.nlm.nih.gov",
    "medlineplus.gov",
    "ods.od.nih.gov",
}

CACHE_TTL_SECONDS = 86400  # 24 hours
FALLBACK_MESSAGE = "Could not reach medical reference services. Please consult a qualified clinician."


class WebAnswerService:
    """Service for querying NIH / MedlinePlus reference fact sheets with caching and allowlist enforcement."""

    def __init__(self):
        self._cache: Dict[str, Dict] = {}

    def _normalize_query_key(self, query: str) -> str:
        """Normalizes search query for cache keying."""
        cleaned = re.sub(r"[^\w\s]", "", query.lower().strip())
        return " ".join(cleaned.split())

    def _is_url_allowed(self, url: str) -> bool:
        """Verifies hostname belongs to the approved medical reference allowlist."""
        try:
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False
            hostname = hostname.lower()
            return hostname in ALLOWED_DOMAINS or any(
                hostname.endswith("." + domain) for domain in ALLOWED_DOMAINS
            )
        except Exception:
            return False

    def _clean_and_truncate_text(self, raw_html: str, max_chars: int = 600) -> str:
        """Strips HTML/XML tags and cleanly truncates to max_chars with ellipsis."""
        # Strip XML/HTML tags
        clean = re.sub(r"<[^>]+>", " ", raw_html)
        # Normalize whitespace
        clean = " ".join(clean.split())
        if len(clean) <= max_chars:
            return clean
        truncated = clean[: max_chars - 3]
        # Truncate at last word boundary if possible
        last_space = truncated.rfind(" ")
        if last_space > max_chars - 50:
            truncated = truncated[:last_space]
        return truncated.rstrip() + "..."

    async def fetch_web_answer(self, query: str) -> Dict[str, Optional[str]]:
        """Queries MedlinePlus Web Service for factual reference sheets with caching and fallback."""
        norm_key = self._normalize_query_key(query)
        if not norm_key:
            return {
                "reply": FALLBACK_MESSAGE,
                "source_name": None,
                "source_url": None,
                "is_web_answer": False,
            }

        # 1. Check in-memory cache
        now = time.time()
        if norm_key in self._cache:
            entry = self._cache[norm_key]
            if now - entry["cached_at"] < CACHE_TTL_SECONDS:
                return {
                    "reply": entry["reply"],
                    "source_name": entry["source_name"],
                    "source_url": entry["source_url"],
                    "is_web_answer": True,
                }
            else:
                del self._cache[norm_key]

        # 2. Build MedlinePlus API request URL
        encoded_term = urllib.parse.quote_plus(norm_key)
        target_url = f"https://wsearch.nlm.nih.gov/ws/query?db=healthTopics&term={encoded_term}"

        # 3. Verify allowlist
        if not self._is_url_allowed(target_url):
            logger.warning("Web request blocked: host not in allowed medical domains.")
            return {
                "reply": FALLBACK_MESSAGE,
                "source_name": None,
                "source_url": None,
                "is_web_answer": False,
            }

        # 4. Bounded HTTP request (5.0s timeout, max 2 attempts)
        response_text = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(target_url, headers={"User-Agent": "MedNourish-Academic-Demo/2.0"})
                    if resp.status_code == 200:
                        response_text = resp.text
                        break
            except Exception as e:
                logger.debug(f"Web query attempt {attempt + 1} failed: {type(e).__name__}")

        if not response_text:
            return {
                "reply": FALLBACK_MESSAGE,
                "source_name": None,
                "source_url": None,
                "is_web_answer": False,
            }

        # 5. Parse XML
        try:
            root = ET.fromstring(response_text)
            # Find document elements
            documents = root.findall(".//document")
            if not documents:
                return {
                    "reply": FALLBACK_MESSAGE,
                    "source_name": None,
                    "source_url": None,
                    "is_web_answer": False,
                }

            # Select first relevant document
            first_doc = documents[0]
            doc_url = first_doc.get("url") or "https://medlineplus.gov"
            if not self._is_url_allowed(doc_url):
                doc_url = "https://medlineplus.gov"

            # Extract FullSummary or snippet
            summary_content = None
            title_content = None
            for content_tag in first_doc.findall(".//content"):
                c_name = content_tag.get("name")
                if c_name == "FullSummary" and content_tag.text:
                    summary_content = content_tag.text
                    break
                elif c_name == "snippet" and content_tag.text and not summary_content:
                    summary_content = content_tag.text
                elif c_name == "title" and content_tag.text:
                    title_content = content_tag.text

            body_text = summary_content or title_content
            if not body_text:
                return {
                    "reply": FALLBACK_MESSAGE,
                    "source_name": None,
                    "source_url": None,
                    "is_web_answer": False,
                }

            cleaned_reply = self._clean_and_truncate_text(body_text, max_chars=600)
            source_name = "MedlinePlus (National Library of Medicine)"

            # Cache the successful result
            self._cache[norm_key] = {
                "reply": cleaned_reply,
                "source_name": source_name,
                "source_url": doc_url,
                "cached_at": now,
            }

            return {
                "reply": cleaned_reply,
                "source_name": source_name,
                "source_url": doc_url,
                "is_web_answer": True,
            }
        except Exception as e:
            logger.debug(f"Failed to parse reference response: {type(e).__name__}")
            return {
                "reply": FALLBACK_MESSAGE,
                "source_name": None,
                "source_url": None,
                "is_web_answer": False,
            }


web_answer_service = WebAnswerService()
