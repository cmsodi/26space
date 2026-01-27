"""
Exa web search integration for L2 source enrichment.
"""

import time
from datetime import date
from typing import Optional

from .config import MODEL_FAST
from .models import Source
from .logging_setup import logger

# Exa SDK for L2 web searches (optional)
try:
    from exa_py import Exa
    EXA_AVAILABLE = True
except ImportError:
    EXA_AVAILABLE = False
    Exa = None


# ============== EXA CLIENT AND STATE ==============

_exa_client: Optional[object] = None  # Type hint avoids import dependency
_exa_search_count = 0  # Global counter for search limit
EXA_MAX_SEARCHES = 3  # Maximum L2 searches per analysis


def get_exa_client():
    """Lazy initialization of Exa client."""
    global _exa_client
    import os

    if not EXA_AVAILABLE:
        raise RuntimeError("Exa SDK not installed. Run: pip install exa-py")

    if _exa_client is None:
        api_key = os.environ.get("EXA_API_KEY")
        if not api_key:
            raise RuntimeError("EXA_API_KEY environment variable not set")
        _exa_client = Exa(api_key)
    return _exa_client


def reset_exa_search_count():
    """Reset the Exa search counter (call at start of each analysis)."""
    global _exa_search_count
    _exa_search_count = 0


def get_exa_search_count() -> int:
    """Get current Exa search count."""
    return _exa_search_count


# ============== EXA SEARCH FUNCTIONS ==============

def exa_search(
    query: str,
    num_results: int = 5,
    include_domains: Optional[list[str]] = None,
    start_date: Optional[str] = None,
    category: Optional[str] = None
) -> list[dict]:
    """
    Perform an Exa web search (L2 source).

    Args:
        query: Search query
        num_results: Number of results to return (default 5)
        include_domains: Optional list of domains to include
        start_date: Optional start date filter (YYYY-MM-DD)
        category: Optional category filter (news, company, research_paper, etc.)

    Returns:
        List of dicts with url, title, text, published_date

    Raises:
        RuntimeError: If search limit exceeded or API fails
    """
    global _exa_search_count

    if _exa_search_count >= EXA_MAX_SEARCHES:
        raise RuntimeError(f"Exa search limit reached ({EXA_MAX_SEARCHES} per analysis)")

    try:
        exa = get_exa_client()

        # Build search parameters
        kwargs = {
            "num_results": num_results,
            "text": {"max_characters": 1500},  # Get text content
        }

        if include_domains:
            kwargs["include_domains"] = include_domains
        if start_date:
            kwargs["start_published_date"] = start_date
        if category:
            kwargs["category"] = category

        # Perform search
        start_time = time.time()
        results = exa.search_and_contents(query, **kwargs)
        elapsed = time.time() - start_time

        _exa_search_count += 1
        logger.debug(f"Exa search {_exa_search_count}/{EXA_MAX_SEARCHES}: '{query[:60]}' ({elapsed:.2f}s)")

        # Parse results
        parsed = []
        for r in results.results:
            parsed.append({
                "url": r.url,
                "title": r.title or "Untitled",
                "text": getattr(r, "text", "")[:500] if hasattr(r, "text") else "",
                "published_date": getattr(r, "published_date", None),
                "score": getattr(r, "score", 0.0)
            })

        logger.debug(f"  Exa returned {len(parsed)} results")
        return parsed

    except Exception as e:
        logger.warning(f"Exa search failed: {e}")
        return []


def exa_search_for_citation(
    claim: str,
    context: str = "",
    language: str = "en"
) -> Optional[Source]:
    """
    Search for a source to back a specific claim.
    NOTE: All searches are performed in English for better results.

    Args:
        claim: The claim needing a citation
        context: Additional context about the topic
        language: Source language (used to trigger translation if not English)

    Returns:
        Source object if found, None otherwise
    """
    # Import llm_call here to avoid circular import
    from .llm import llm_call

    # Translate to English if needed (all web searches must be in English)
    if language != "en":
        try:
            text_to_translate = f"{context}: {claim}" if context else claim
            translated = llm_call(
                system="Translate the following text to English. Return ONLY the translation, nothing else.",
                user=text_to_translate,
                max_tokens=300,
                model=MODEL_FAST,
                temperature=0.1
            )
            query = translated.strip()
            logger.debug(f"Translated query for search: {query[:60]}...")
        except Exception as e:
            logger.warning(f"Translation failed, using original: {e}")
            query = f"{context}: {claim}" if context else claim
    else:
        query = f"{context}: {claim}" if context else claim

    # Add year filter for freshness
    current_year = date.today().year
    start_date = f"{current_year - 1}-01-01"

    results = exa_search(query, num_results=3, start_date=start_date)

    if not results:
        return None

    # Pick the best result (highest score or first)
    best = results[0]

    return Source(
        url=best["url"],
        title=best["title"],
        type="web",  # L2 sources are generic web
        anchor_suggestion=best["title"][:50] if best["title"] else claim[:30],
        level="L2",
        relevance=f"Found via Exa for: {claim[:50]}"
    )
