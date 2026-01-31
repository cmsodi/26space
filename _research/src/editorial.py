"""
Editorial workflow — interactive topic selection, NotebookLM deep research,
and handoff to the Strategic Orchestrator.

Usage:
    python run.py --editorial
"""

import re
import time
import asyncio
from datetime import date
from pathlib import Path
from typing import Optional

from .logging_setup import logger
from .utils import generate_slug, ensure_unique_slug
from .ui import (
    ask_user, confirm, get_input,
    print_section_header,
)
from .notebooklm_client import (
    NOTEBOOKLM_AVAILABLE,
    list_notebooks,
    list_sources,
    create_notebook,
    query_notebook,
    start_research,
    poll_research,
    import_research_sources,
    close_client,
)

# ============== CONSTANTS ==============

EDITORIAL_PLAN_PATH = Path(__file__).parent.parent / "editorial_plan.yaml"
CONTEXT_DOCUMENTS_PATH = Path(__file__).parent.parent / "context_documents"
CUSTOM_ID_START = 10001
POLL_INTERVAL = 10   # seconds between polling
POLL_TIMEOUT = 300   # 5 minutes max
IMPORT_BATCH_SIZE = 10  # sources per import call (avoids RPC timeout)


# ============== EDITORIAL PLAN CRUD ==============

def load_editorial_plan() -> list[dict]:
    """Load editorial plan from YAML file.

    Uses text-based parsing to avoid issues with special characters
    (e.g. \\$ in titles) that break yaml.safe_load.
    """
    if not EDITORIAL_PLAN_PATH.exists():
        raise FileNotFoundError(
            f"Editorial plan not found: {EDITORIAL_PLAN_PATH}\n"
            "Expected file: editorial_plan.yaml in project root"
        )

    content = EDITORIAL_PLAN_PATH.read_text(encoding="utf-8")
    items = []
    current = {}

    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            if current:
                items.append(current)
                current = {}
            continue

        if stripped.startswith("- id:"):
            if current:
                items.append(current)
            current = {"id": int(stripped.split(":", 1)[1].strip())}
        elif stripped.startswith("id:") and not current:
            current = {"id": int(stripped.split(":", 1)[1].strip())}
        elif ":" in stripped and current:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            # Strip inline YAML comments (e.g. "tbd" # tbd | drafting | ...)
            if val.startswith('"') and '"' in val[1:]:
                end_q = val.index('"', 1)
                val = val[1:end_q]
            elif val.startswith("'") and "'" in val[1:]:
                end_q = val.index("'", 1)
                val = val[1:end_q]
            else:
                # Unquoted value: strip from first ' #'
                if " #" in val:
                    val = val[:val.index(" #")].rstrip()
                val = val.strip('"').strip("'")
            if key in ("id",):
                current[key] = int(val)
            else:
                current[key] = val

    if current:
        items.append(current)

    return items


def save_editorial_plan(items: list[dict]):
    """Save editorial plan back to YAML file.

    Uses text-based serialization to preserve special characters.
    """
    lines = []
    for item in items:
        lines.append("")
        for key in ("id", "title", "core_evidence", "analytical_angle",
                     "deep_prompt", "slug", "status"):
            val = item.get(key)
            if val is None:
                continue
            if key == "id":
                lines.append(f"- id: {val}")
            elif isinstance(val, int):
                lines.append(f"  {key}: {val}")
            elif key == "status":
                lines.append(f'  {key}: "{val}" # tbd | drafting | editing | finalized')
            else:
                lines.append(f'  {key}: "{val}"')
    lines.append("")

    EDITORIAL_PLAN_PATH.write_text("\n".join(lines), encoding="utf-8")


def get_tbd_items(items: list[dict]) -> list[dict]:
    """Return items with status 'tbd' (or missing status for backward compat)."""
    return [item for item in items if item.get("status", "tbd") == "tbd"]


def get_drafting_items(items: list[dict]) -> list[dict]:
    """Return items with status 'drafting'."""
    return [item for item in items if item.get("status") == "drafting"]


def get_item_by_id(items: list[dict], item_id: int) -> Optional[dict]:
    """Find item by id."""
    return next((item for item in items if item["id"] == item_id), None)


def update_item_status(items: list[dict], item_id: int, new_status: str) -> list[dict]:
    """Update an item's status and persist to file."""
    for item in items:
        if item["id"] == item_id:
            item["status"] = new_status
            break
    save_editorial_plan(items)
    return items


def get_next_custom_id(items: list[dict]) -> int:
    """Get next available ID for custom items (>= 10001)."""
    custom_ids = [item["id"] for item in items if item["id"] >= CUSTOM_ID_START]
    return max(custom_ids) + 1 if custom_ids else CUSTOM_ID_START


def create_new_item(
    title: str,
    core_evidence: str,
    analytical_angle: str,
    deep_prompt: str,
    items: list[dict],
) -> dict:
    """Create a new editorial plan item and persist."""
    new_item = {
        "id": get_next_custom_id(items),
        "title": title,
        "core_evidence": core_evidence,
        "analytical_angle": analytical_angle,
        "deep_prompt": deep_prompt,
        "slug": generate_slug(title),
        "status": "drafting",
    }
    items.append(new_item)
    save_editorial_plan(items)
    return new_item


# ============== NOTEBOOKLM RESEARCH ==============

def build_research_query(item: dict) -> str:
    """Build a research query from editorial plan fields."""
    parts = [item["title"]]
    if item.get("core_evidence"):
        parts.append(f"Core evidence: {item['core_evidence']}")
    if item.get("analytical_angle"):
        parts.append(f"Analytical angle: {item['analytical_angle']}")
    return ". ".join(parts)


def get_extraction_prompt() -> str:
    """Return the YAML extraction prompt for NotebookLM query.

    Asks NotebookLM to analyze its imported sources and produce
    structured YAML suitable for the orchestrator's L0 source format.
    """
    return """Analyze ALL sources available in this notebook. For each source, extract structured information in YAML format.

Return ONLY valid YAML (no markdown fences, no commentary) with the following structure:

sources:
  - title: "Full title of the document or article"
    url: "https://original-url-if-available"
    type: "official_document|report|academic|industry|news"
    date: "YYYY-MM-DD or YYYY-MM or YYYY (best available)"
    takeaways:
      - "Key finding or data point 1"
      - "Key finding or data point 2"
      - "Key finding or data point 3"
    relevance: "One sentence explaining why this source matters for the analysis"
    anchor_suggestion: "Natural citation phrase for embedding in prose"

Example of a well-formed entry:

sources:
  - title: "Policy on Celestial Time Standardization"
    url: "https://whitehouse.gov/celestial-time-policy.pdf"
    type: "official_document"
    date: "2024-04-02"
    takeaways:
      - "LTC must provide traceability to UTC while maintaining operational independence"
      - "Time standardization is foundational for interoperability between partners"
    relevance: "Official U.S. directive establishing framework for extraterrestrial time standards"
    anchor_suggestion: "as mandated in the White House's April 2024 policy directive"

Rules for anchor_suggestion:
- Must read naturally when inserted mid-sentence: "The standard, [anchor_suggestion], requires..."
- Include source attribution (author or organization name)
- Use action verbs: "according to", "as detailed in", "per", "as outlined by"
- NEVER use bare citations like "Author 2024" or parenthetical "(NASA, 2025)"

Extract information from EVERY source in this notebook. Return between 5 and 30 source entries."""


def run_notebooklm_research(item: dict) -> Optional[Path]:
    """Run full NotebookLM deep research flow for an editorial item.

    Wraps the async implementation in a single asyncio.run() call
    so the NotebookLM client stays on one event loop throughout.

    Returns:
        Path to saved sources.yaml, or None on failure.
    """
    return asyncio.run(_async_notebooklm_research(item))


async def _async_notebooklm_research(item: dict) -> Optional[Path]:
    """Async implementation of the full NotebookLM research flow.

    All NotebookLM operations run on the same event loop, avoiding
    'Event loop is closed' errors from client reuse across loops.
    The client is closed in the finally block of this function.

    1. Create notebook
    2. Start deep research
    3. Poll until complete
    4. Import discovered sources
    5. Query notebook for structured extraction
    6. Save YAML result

    Returns:
        Path to saved sources.yaml, or None on failure.
    """
    slug = item["slug"]

    try:
        return await _do_notebooklm_research(slug, item)
    finally:
        try:
            await close_client()
        except Exception:
            pass


async def _do_notebooklm_research(slug: str, item: dict) -> Optional[Path]:
    """Core research logic, separated for clean try/finally in caller."""
    MIN_EXISTING_SOURCES = 5  # skip research if notebook already has enough sources

    # 1. Find existing or create notebook
    notebook_id = None
    notebook_is_new = False
    try:
        existing = await list_notebooks(limit=100)
        for nb in existing:
            if nb["title"] == slug:
                notebook_id = nb["id"]
                print(f"  Reusing existing notebook: {slug} ({notebook_id})")
                break
    except Exception as e:
        logger.debug(f"Could not list notebooks: {e}")

    if notebook_id is None:
        print(f"  Creating notebook: {slug}")
        try:
            nb = await create_notebook(slug)
        except Exception as e:
            print(f"  Failed to create notebook: {e}")
            return None
        notebook_id = nb["id"]
        notebook_is_new = True
        print(f"  Notebook created: {notebook_id}")

    # 2. Check if notebook already has imported sources (skip research if so)
    if not notebook_is_new:
        try:
            existing_sources = await list_sources(notebook_id)
            n_sources = len(existing_sources)
            if n_sources >= MIN_EXISTING_SOURCES:
                print(f"  Notebook already has {n_sources} sources — skipping research & import.")
                print(f"  Proceeding directly to structured extraction...")
                # Jump straight to extraction (step 5)
                return await _extract_and_save(notebook_id, slug)
            elif n_sources > 0:
                print(f"  Notebook has {n_sources} sources (< {MIN_EXISTING_SOURCES}). Running new research.")
        except Exception as e:
            logger.debug(f"Could not list sources: {e}")

    # 3. Start deep research
    query = build_research_query(item)
    print(f"  Starting deep research...")
    print(f"  Query: {query[:120]}{'...' if len(query) > 120 else ''}")
    try:
        task = await start_research(notebook_id, query, source="web", mode="deep")
    except Exception as e:
        print(f"  Research start failed: {e}")
        return None

    if not task:
        print("  Research start returned empty. Skipping.")
        return None

    task_id = task["task_id"]
    print(f"  Research task started: {task_id}")

    # 4. Poll until complete
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > POLL_TIMEOUT:
            print(f"  Research timed out after {POLL_TIMEOUT}s")
            return None

        try:
            result = await poll_research(notebook_id)
        except Exception as e:
            print(f"  Polling error: {e}")
            return None

        status = result.get("status", "unknown")

        if status == "completed":
            print(f"  Research completed ({elapsed:.0f}s)")
            break
        elif status == "in_progress":
            print(f"  Polling... ({elapsed:.0f}s elapsed)")
            await asyncio.sleep(POLL_INTERVAL)
        else:
            print(f"  Unexpected status: {status}")
            return None

    # 5. Import sources in batches (avoids RPC timeout with many sources)
    sources = result.get("sources", [])
    if not sources:
        print("  No sources discovered. Skipping import.")
        return None

    print(f"  Discovered {len(sources)} sources. Importing in batches of {IMPORT_BATCH_SIZE}...")
    total_imported = 0
    for i in range(0, len(sources), IMPORT_BATCH_SIZE):
        batch = sources[i:i + IMPORT_BATCH_SIZE]
        batch_num = i // IMPORT_BATCH_SIZE + 1
        try:
            imported = await import_research_sources(notebook_id, task_id, batch)
            total_imported += len(imported)
            print(f"  Batch {batch_num}: imported {len(imported)} sources")
        except Exception as e:
            print(f"  Batch {batch_num} import failed: {e}")
            # Continue with remaining batches
        if i + IMPORT_BATCH_SIZE < len(sources):
            await asyncio.sleep(2)

    if total_imported == 0:
        print("  No sources could be imported.")
        return None

    print(f"  Total imported: {total_imported}/{len(sources)} sources")

    # Wait for source processing
    await asyncio.sleep(5)

    # 6. Extract and save
    return await _extract_and_save(notebook_id, slug)


async def _extract_and_save(notebook_id: str, slug: str) -> Optional[Path]:
    """Query notebook for structured extraction and save YAML result."""
    extraction_prompt = get_extraction_prompt()
    print("  Extracting structured source data...")
    try:
        response = await query_notebook(notebook_id, extraction_prompt)
    except Exception as e:
        print(f"  Extraction query failed: {e}")
        return None

    answer = response.get("answer", "")
    if not answer:
        print("  Extraction query returned empty. Skipping.")
        return None

    # Clean and save YAML
    yaml_content = answer.strip()
    # Strip markdown fences if present
    if yaml_content.startswith("```"):
        lines = yaml_content.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        yaml_content = "\n".join(lines)

    return save_research_results(slug, yaml_content)


def save_research_results(slug: str, yaml_content: str) -> Path:
    """Save research results to context_documents/{slug}/sources.yaml.

    If sources.yaml already exists, uses numbered variants:
    sources1.yaml, sources2.yaml, sources3.yaml (max 3 numbered files).
    """
    output_dir = CONTEXT_DOCUMENTS_PATH / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find next available filename: sources.yaml → sources1..3.yaml
    base_path = output_dir / "sources.yaml"
    if not base_path.exists():
        output_path = base_path
    else:
        output_path = None
        for i in range(1, 4):  # sources1.yaml .. sources3.yaml
            candidate = output_dir / f"sources{i}.yaml"
            if not candidate.exists():
                output_path = candidate
                break
        if output_path is None:
            # All slots full — overwrite sources3.yaml
            output_path = output_dir / "sources3.yaml"
            print(f"  Warning: max sources files reached, overwriting {output_path.name}")

    output_path.write_text(yaml_content, encoding="utf-8")

    print(f"  Sources saved to: {output_path}")
    return output_path


# ============== TOPIC SELECTION ==============

def select_or_create_topic() -> tuple[list[dict], dict] | None:
    """Unified topic selection: pick from editorial plan by ID or create new.

    Shows available (tbd/drafting) items, then accepts either:
    - A numeric ID to select an existing item
    - Free-form text to create a new item (will ask for context info)

    Returns:
        (items, selected_item) tuple, or None if user aborts.
    """
    try:
        items = load_editorial_plan()
    except FileNotFoundError as e:
        print(f"\n  {e}")
        return None

    tbd_items = get_tbd_items(items)
    drafting_items = get_drafting_items(items)
    print(f"\n  Editorial plan: {len(items)} items ({len(tbd_items)} tbd, {len(drafting_items)} drafting)")

    # Show available topics
    if tbd_items:
        print(f"\n  Available topics (status='tbd'):")
        for item in tbd_items:
            print(f"    [{item['id']:>3}] {item['title'][:70]}")

    if drafting_items:
        print(f"\n  In-progress topics (status='drafting'):")
        for item in drafting_items:
            print(f"    [{item['id']:>3}] {item['title'][:70]}  [drafting]")

    # Unified prompt: ID or free-form problem
    user_input = get_input(
        "\n  Enter article ID or new analysis problem"
    )
    if not user_input:
        return None

    # Check if input is a numeric ID
    selected = None
    if user_input.strip().isdigit():
        item_id = int(user_input.strip())
        selected = get_item_by_id(items, item_id)
        if not selected:
            print(f"  Item {item_id} not found.")
            # Fall through to treat as free-form text
        else:
            item_status = selected.get("status", "tbd")
            if item_status not in ("tbd", "drafting"):
                print(f"  Item {item_id} has status '{item_status}', expected 'tbd' or 'drafting'. Aborting.")
                return None

            print(f"\n  Selected: [{selected['id']}] {selected['title']}")
            print(f"  Status: {item_status}")
            print(f"  Angle: {selected.get('analytical_angle', 'N/A')[:80]}")

            if not confirm("  Proceed with this topic?"):
                return None

    # Free-form: create new editorial plan item
    if selected is None:
        title = user_input  # Use what the user already typed as title
        print(f"\n  New topic: {title}")
        core_evidence = get_input("  Core evidence (key data points)", default="")
        analytical_angle = get_input("  Analytical angle", default="")
        deep_prompt = get_input("  Deep prompt (generation instructions)", default="")

        selected = create_new_item(title, core_evidence, analytical_angle, deep_prompt, items)
        items = load_editorial_plan()  # Reload after save
        print(f"\n  Created: [{selected['id']}] {selected['title']}")

    return items, selected


def build_problem_from_item(item: dict) -> str:
    """Extract the analysis problem statement from an editorial plan item."""
    if item.get("deep_prompt"):
        return item["deep_prompt"]
    elif item.get("analytical_angle"):
        return f"{item['title']}. {item['analytical_angle']}"
    return item["title"]


# ============== MAIN WORKFLOW ==============

def run_editorial_workflow(verbose: bool = False, **orchestrator_kwargs):
    """Interactive editorial workflow: pick topic, research, analyze.

    Args:
        verbose: Enable verbose output.
        **orchestrator_kwargs: Passed to StrategicOrchestrator constructor.
    """
    print_section_header("Editorial Workflow", emoji="📋")

    # --- Step 0-1: Select or create topic ---
    result = select_or_create_topic()
    if result is None:
        return
    items, selected = result

    # --- Step 2: Set status to "drafting" (tbd→drafting, drafting stays) ---
    if selected.get("status", "tbd") == "tbd":
        items = update_item_status(items, selected["id"], "drafting")
        print(f"  Status updated to 'drafting'")
    else:
        print(f"  Status remains '{selected['status']}'")

    # --- Step 3: Create context_documents/{slug}/ folder ---
    slug = selected["slug"]
    context_dir = CONTEXT_DOCUMENTS_PATH / slug
    context_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Context folder: {context_dir}")

    # --- Step 4: Optional NotebookLM deep research ---
    sources_yaml_path = None

    if NOTEBOOKLM_AVAILABLE:
        if confirm("  Run NotebookLM deep research for this topic?"):
            try:
                # Client lifecycle managed inside run_notebooklm_research
                sources_yaml_path = run_notebooklm_research(selected)
            except Exception as e:
                print(f"  NotebookLM error: {e}")
                logger.exception("NotebookLM research failed")
    else:
        print("  NotebookLM not available (notebooklm-py not installed)")
        print("  Skipping deep research step.")

    # Check if user wants to continue without research results
    if not sources_yaml_path:
        if not confirm("  Continue to analysis without NotebookLM sources?"):
            items = update_item_status(items, selected["id"], "tbd")
            print("  Status reverted to 'tbd'")
            return

    # --- Step 5: Hand off to orchestrator ---
    print_section_header("Starting Analysis", emoji="🚀")

    # Build problem statement from editorial item fields
    problem = build_problem_from_item(selected)

    # Lazy import to avoid circular dependency
    from .orchestrator import StrategicOrchestrator

    orch = StrategicOrchestrator(
        verbose=verbose,
        **orchestrator_kwargs,
    )

    # Pre-set slug from editorial item (with unique numbering for output)
    orch.state.slug = ensure_unique_slug(slug)

    # Pre-load research sources if available
    if sources_yaml_path and sources_yaml_path.exists():
        orch._load_research_briefing(str(sources_yaml_path))
        print(f"  Pre-loaded {len(orch.state.context_documents)} L0 sources")

    # Also load any other YAML files in the slug's context folder
    for yaml_file in sorted(context_dir.glob("*.yaml")):
        # Skip the file already loaded above to avoid duplicates
        if sources_yaml_path and yaml_file.resolve() == sources_yaml_path.resolve():
            continue
        orch._load_research_briefing(str(yaml_file))

    try:
        result = orch.run(problem)
        if result:
            # Update status to finalized
            items = load_editorial_plan()
            update_item_status(items, selected["id"], "finalized")
            print(f"  Editorial status updated to 'finalized'")

    except KeyboardInterrupt:
        print("\n\n  Interrupted by user")
        if confirm("  Save current state before exiting?"):
            orch.save_state()
    except Exception as e:
        print(f"\n  Analysis failed: {e}")
        logger.exception("Editorial workflow analysis failed")
