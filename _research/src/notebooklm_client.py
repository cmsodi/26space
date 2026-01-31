"""
NotebookLM integration via notebooklm-py (optional).

Provides async helpers for interacting with Google NotebookLM:
- List/create/query notebooks
- Add sources (URL, text, file)
- Generate artifacts (audio, report, etc.)

This module is entirely optional. If notebooklm-py is not installed,
NOTEBOOKLM_AVAILABLE is False and all functions raise RuntimeError.

Install:  pip install "notebooklm-py[browser]"
Auth:     notebooklm login  (or convert existing cookies)
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Optional, Any

from .logging_setup import logger

# Optional import — no impact on project if not installed
try:
    from notebooklm import NotebookLMClient
    from notebooklm.auth import AuthTokens
    import notebooklm._chat as _nlm_chat
    NOTEBOOKLM_AVAILABLE = True
except ImportError:
    NOTEBOOKLM_AVAILABLE = False
    NotebookLMClient = None
    AuthTokens = None
    _nlm_chat = None


# ============== MONKEY-PATCH: fix answer detection ==============
# The library checks type_info[-1] == 1 to identify answers, but Google's
# API now returns 2 (or other values). We relax the check to accept any
# non-None value, which matches the actual observed behavior.
# This patch is safe: it only widens the acceptance criteria.

if NOTEBOOKLM_AVAILABLE and _nlm_chat is not None:
    _MIN_ANSWER_LENGTH = 20  # Same as library's constant

    _original_extract = _nlm_chat.ChatAPI._extract_answer_and_refs_from_chunk

    def _patched_extract(self, json_str):
        """Patched version that accepts type_info[-1] in {1, 2}."""
        refs = []
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return None, False, refs

        if not isinstance(data, list):
            return None, False, refs

        for item in data:
            if not isinstance(item, list) or len(item) < 3:
                continue
            if item[0] != "wrb.fr":
                continue

            inner_json = item[2]
            if not isinstance(inner_json, str):
                continue

            try:
                inner_data = json.loads(inner_json)
                if isinstance(inner_data, list) and len(inner_data) > 0:
                    first = inner_data[0]
                    if isinstance(first, list) and len(first) > 0:
                        text = first[0]
                        is_answer = False
                        if isinstance(text, str) and len(text) > _MIN_ANSWER_LENGTH:
                            if len(first) > 4 and isinstance(first[4], list):
                                type_info = first[4]
                                # Original: type_info[-1] == 1
                                # Patched: accept 1 or 2 (Google changed the format)
                                if len(type_info) > 0 and type_info[-1] in (1, 2):
                                    is_answer = True

                            refs = self._parse_citations(first)
                            return text, is_answer, refs
            except json.JSONDecodeError:
                continue

        return None, False, refs

    _nlm_chat.ChatAPI._extract_answer_and_refs_from_chunk = _patched_extract
    logger.debug("NotebookLM chat parser patched (type_info acceptance widened)")


# ============== CLIENT MANAGEMENT ==============

_client: Optional[Any] = None  # NotebookLMClient instance (async context)
_client_entered = False         # Whether __aenter__ has been called


async def get_client() -> Any:
    """Lazy initialization of NotebookLM async client.

    Returns connected NotebookLMClient ready for API calls.
    Reuses existing client if already connected.

    Raises:
        RuntimeError: If notebooklm-py not installed or auth missing.
    """
    global _client, _client_entered

    if not NOTEBOOKLM_AVAILABLE:
        raise RuntimeError(
            "notebooklm-py not installed. Run: pip install 'notebooklm-py[browser]'"
        )

    if _client is not None and _client_entered:
        return _client

    try:
        _client = await NotebookLMClient.from_storage()
        _client = await _client.__aenter__()
        _client_entered = True
        logger.debug("NotebookLM client connected")
        return _client
    except FileNotFoundError:
        raise RuntimeError(
            "NotebookLM auth not found. Run: notebooklm login"
        )
    except Exception as e:
        _client = None
        _client_entered = False
        raise RuntimeError(f"NotebookLM client init failed: {e}")


async def close_client():
    """Close the NotebookLM client if open."""
    global _client, _client_entered
    if _client is not None and _client_entered:
        try:
            await _client.__aexit__(None, None, None)
        except Exception:
            pass
    _client = None
    _client_entered = False


# ============== NOTEBOOK OPERATIONS ==============

async def list_notebooks(limit: int = 20) -> list[dict]:
    """List notebooks.

    Returns:
        List of dicts with 'id', 'title' keys.
    """
    client = await get_client()
    notebooks = await client.notebooks.list()
    results = []
    for nb in notebooks[:limit]:
        results.append({"id": nb.id, "title": nb.title})
    return results


async def create_notebook(title: str) -> dict:
    """Create a new notebook.

    Returns:
        Dict with 'id', 'title'.
    """
    client = await get_client()
    nb = await client.notebooks.create(title)
    logger.info(f"Created notebook: {nb.title} ({nb.id})")
    return {"id": nb.id, "title": nb.title}


async def add_source_url(notebook_id: str, url: str, wait: bool = True) -> dict:
    """Add a URL source to a notebook.

    Args:
        notebook_id: Target notebook ID.
        url: URL to add (web page or YouTube).
        wait: Wait for processing to complete.

    Returns:
        Dict with 'id', 'title', 'status'.
    """
    client = await get_client()
    source = await client.sources.add_url(notebook_id, url, wait=wait)
    logger.info(f"Added URL source: {url[:60]}...")
    return {"id": source.id, "title": source.title, "status": str(source.status)}


async def add_source_text(
    notebook_id: str,
    title: str,
    content: str,
    wait: bool = True
) -> dict:
    """Add text content as a source.

    Args:
        notebook_id: Target notebook ID.
        title: Display title for the source.
        content: Text content to add.
        wait: Wait for processing to complete.

    Returns:
        Dict with 'id', 'title', 'status'.
    """
    client = await get_client()
    source = await client.sources.add_text(notebook_id, title, content, wait=wait)
    logger.info(f"Added text source: {title}")
    return {"id": source.id, "title": source.title, "status": str(source.status)}


async def add_source_file(
    notebook_id: str,
    file_path: str,
    wait: bool = True
) -> dict:
    """Add a file as a source (PDF, markdown, text, docx).

    Args:
        notebook_id: Target notebook ID.
        file_path: Path to the file.
        wait: Wait for processing to complete.

    Returns:
        Dict with 'id', 'title', 'status'.
    """
    client = await get_client()
    source = await client.sources.add_file(notebook_id, file_path, wait=wait)
    logger.info(f"Added file source: {Path(file_path).name}")
    return {"id": source.id, "title": source.title, "status": str(source.status)}


async def list_sources(notebook_id: str) -> list[dict]:
    """List sources in a notebook.

    Returns:
        List of dicts with 'id', 'title', 'status'.
    """
    client = await get_client()
    sources = await client.sources.list(notebook_id)
    return [
        {"id": s.id, "title": s.title, "status": str(s.status)}
        for s in sources
    ]


# ============== QUERY / CHAT ==============

def _extract_answer_from_raw(raw_response: str) -> str:
    """Fallback parser for raw_response when library returns empty answer.

    The library's parser checks type_info[-1] == 1 to identify answers,
    but Google's API sometimes returns 2 instead. This extracts the
    longest text from the wrb.fr chunks regardless of type flag.
    """
    if not raw_response:
        return ""

    text = raw_response
    if text.startswith(")]}'"):
        text = text[4:]

    longest = ""
    # Find all wrb.fr JSON chunks
    for match in re.finditer(r'\["wrb\.fr",null,"(.+?)"\]\s*\]', text, re.DOTALL):
        inner_json_escaped = match.group(1)
        try:
            inner_str = json.loads(f'"{inner_json_escaped}"')
            inner_data = json.loads(inner_str)
            if isinstance(inner_data, list) and inner_data:
                first = inner_data[0]
                if isinstance(first, list) and first and isinstance(first[0], str):
                    candidate = first[0]
                    if len(candidate) > len(longest):
                        longest = candidate
        except (json.JSONDecodeError, IndexError, TypeError):
            continue

    return longest


async def query_notebook(
    notebook_id: str,
    question: str,
    source_ids: Optional[list[str]] = None,
    conversation_id: Optional[str] = None
) -> dict:
    """Ask a question about notebook sources.

    Args:
        notebook_id: Notebook to query.
        question: Question text.
        source_ids: Optional subset of source IDs to query.
        conversation_id: For follow-up questions in the same conversation.

    Returns:
        Dict with 'answer', 'conversation_id', 'sources'.
    """
    client = await get_client()
    result = await client.chat.ask(
        notebook_id,
        question,
        source_ids=source_ids,
        conversation_id=conversation_id
    )

    answer = result.answer
    # Fallback: library parser may fail on newer Google response formats
    if not answer and result.raw_response:
        answer = _extract_answer_from_raw(result.raw_response)
        if answer:
            logger.debug("Used fallback parser for NotebookLM answer")

    return {
        "answer": answer,
        "conversation_id": result.conversation_id,
        "sources": getattr(result, "references", []),
    }


# ============== SYNC WRAPPERS ==============
# For use in non-async code (e.g., orchestrator phases)

def sync_list_notebooks(limit: int = 20) -> list[dict]:
    """Sync wrapper for list_notebooks."""
    return asyncio.run(list_notebooks(limit))


def sync_create_notebook(title: str) -> dict:
    """Sync wrapper for create_notebook."""
    return asyncio.run(create_notebook(title))


def sync_add_source_url(notebook_id: str, url: str, wait: bool = True) -> dict:
    """Sync wrapper for add_source_url."""
    return asyncio.run(add_source_url(notebook_id, url, wait=wait))


def sync_add_source_text(
    notebook_id: str, title: str, content: str, wait: bool = True
) -> dict:
    """Sync wrapper for add_source_text."""
    return asyncio.run(add_source_text(notebook_id, title, content, wait=wait))


def sync_add_source_file(
    notebook_id: str, file_path: str, wait: bool = True
) -> dict:
    """Sync wrapper for add_source_file."""
    return asyncio.run(add_source_file(notebook_id, file_path, wait=wait))


def sync_list_sources(notebook_id: str) -> list[dict]:
    """Sync wrapper for list_sources."""
    return asyncio.run(list_sources(notebook_id))


def sync_query_notebook(
    notebook_id: str,
    question: str,
    source_ids: Optional[list[str]] = None,
    conversation_id: Optional[str] = None
) -> dict:
    """Sync wrapper for query_notebook."""
    return asyncio.run(query_notebook(
        notebook_id, question, source_ids, conversation_id
    ))


# ============== RESEARCH API ==============

async def start_research(
    notebook_id: str,
    query: str,
    source: str = "web",
    mode: str = "deep",
) -> Optional[dict]:
    """Start a research session in a notebook.

    Args:
        notebook_id: Target notebook ID.
        query: Research query text.
        source: "web" or "drive".
        mode: "fast" or "deep" (deep only for web).

    Returns:
        Dict with 'task_id', 'report_id', 'notebook_id', 'query', 'mode'.
    """
    client = await get_client()
    result = await client.research.start(notebook_id, query, source=source, mode=mode)
    if result:
        logger.info(f"Research started: task_id={result['task_id']}, mode={mode}")
    return result


async def poll_research(notebook_id: str) -> dict:
    """Poll for research results.

    Returns:
        Dict with 'task_id', 'status', 'query', 'sources', 'summary'.
    """
    client = await get_client()
    return await client.research.poll(notebook_id)


async def import_research_sources(
    notebook_id: str,
    task_id: str,
    sources: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Import discovered research sources into a notebook.

    Args:
        notebook_id: Target notebook ID.
        task_id: Research task ID from start_research.
        sources: List of dicts with 'url' and 'title'.

    Returns:
        List of imported sources with 'id' and 'title'.
    """
    client = await get_client()
    result = await client.research.import_sources(notebook_id, task_id, sources)
    logger.info(f"Imported {len(result)} research sources into notebook")
    return result


# Sync wrappers for research
def sync_start_research(
    notebook_id: str, query: str, source: str = "web", mode: str = "deep"
) -> Optional[dict]:
    """Sync wrapper for start_research."""
    return asyncio.run(start_research(notebook_id, query, source=source, mode=mode))


def sync_poll_research(notebook_id: str) -> dict:
    """Sync wrapper for poll_research."""
    return asyncio.run(poll_research(notebook_id))


def sync_import_research_sources(
    notebook_id: str, task_id: str, sources: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Sync wrapper for import_research_sources."""
    return asyncio.run(import_research_sources(notebook_id, task_id, sources))
