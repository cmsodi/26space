"""
Context document loading: YAML research briefings, text files, manual URLs.

Provides ContextLoaderMixin, mixed into StrategicOrchestrator via inheritance.
All methods access orchestrator state through self.state, self._vprint, etc.
"""

from pathlib import Path

import yaml

from .models import Source, TextDocument
from .ui import ask_user, get_input


class ContextLoaderMixin:
    """
    Context document loading methods for StrategicOrchestrator.

    Handles: YAML research briefing parsing, text file loading (.md/.txt),
    manual URL entry, and interactive context document management menu.
    """

    def _load_research_briefing(self, path: str):
        """Load and parse research_briefing.yaml into context_documents."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if "sources" in data:
                for src in data["sources"]:
                    self.state.context_documents.append(Source(
                        url=src.get("url", ""),
                        title=src.get("title", ""),
                        type=src.get("type", "unknown"),
                        anchor_suggestion=src.get("anchor_suggestion", src.get("title", "")),
                        level="L0",
                        relevance=src.get("relevance", "")
                    ))
                self._vprint(f"  Loaded {len(self.state.context_documents)} L0 sources")

        except Exception as e:
            self._vprint(f"  Warning: Failed to parse research briefing: {e}")

    def _add_context_documents(self):
        """Allow user to add context documents (L0 sources) with URLs or text files."""
        # Show current documents if any
        if self.state.context_documents:
            print(f"\n  Currently loaded: {len(self.state.context_documents)} L0 source(s)")
            for i, doc in enumerate(self.state.context_documents[:5], 1):
                print(f"    {i}. {doc.title[:50]}{'...' if len(doc.title) > 50 else ''}")
            if len(self.state.context_documents) > 5:
                print(f"    ... and {len(self.state.context_documents) - 5} more")
        if self.state.text_documents:
            print(f"  Text documents: {len(self.state.text_documents)} file(s)")
            for td in self.state.text_documents:
                label = f" ({td.label})" if td.label else ""
                print(f"    - {td.filename}{label} [{len(td.content)} chars]")

        options = [
            "Load from YAML file (research_briefing.yaml format)",
            "Load text file (.md or .txt for inline context)",
            "Add single URL manually",
            "Clear all context documents",
            "Done - return to proposal"
        ]

        while True:
            choice = ask_user("Context documents:", options, allow_other=False)

            if "YAML" in choice:
                # List available YAML files in context_documents/
                context_dir = Path("context_documents")
                if context_dir.exists():
                    yaml_files = sorted([f.name for f in context_dir.glob("*.yaml")] +
                                      [f.name for f in context_dir.glob("*.yml")])
                    if yaml_files:
                        print(f"\n  Available YAML files in context_documents/:")
                        for f in yaml_files:
                            print(f"    - {f}")
                    else:
                        print(f"  No YAML files found in context_documents/")
                else:
                    print(f"  Warning: context_documents/ directory not found")

                # Prompt for file(s)
                print(f"\n  Enter one or more filenames (comma-separated)")
                print(f"  Example: test.yaml  or  test.yaml, briefing.yaml")
                filenames = get_input("Filenames (or press Enter to skip)")

                if not filenames:
                    # User chose to skip
                    continue

                # Process comma-separated list
                loaded_count = 0
                for filename in [f.strip() for f in filenames.split(",")]:
                    if not filename:
                        continue

                    # Always look in context_documents/
                    file_path = context_dir / filename

                    if file_path.exists():
                        try:
                            self._load_research_briefing(str(file_path))
                            loaded_count += 1
                            print(f"  ✓ Loaded: {filename}")
                        except Exception as e:
                            print(f"  ✗ Error loading {filename}: {e}")
                    else:
                        print(f"  ✗ File not found: {filename}")

                if loaded_count > 0:
                    print(f"\n  Total loaded: {loaded_count} file(s), {len(self.state.context_documents)} L0 source(s)")

            elif "text file" in choice.lower():
                # List available .md and .txt files in context_documents/
                context_dir = Path("context_documents")
                if context_dir.exists():
                    text_files = sorted(
                        [f.name for f in context_dir.glob("*.md")] +
                        [f.name for f in context_dir.glob("*.txt")]
                    )
                    if text_files:
                        print(f"\n  Available text files in context_documents/:")
                        for f in text_files:
                            print(f"    - {f}")
                    else:
                        print(f"  No .md or .txt files found in context_documents/")
                else:
                    print(f"  Warning: context_documents/ directory not found")

                print(f"\n  Enter one or more filenames (comma-separated)")
                print(f"  Example: notes.md  or  notes.md, background.txt")
                filenames = get_input("Filenames (or press Enter to skip)")

                if not filenames:
                    continue

                loaded_count = 0
                for filename in [f.strip() for f in filenames.split(",")]:
                    if not filename:
                        continue
                    file_path = context_dir / filename
                    if file_path.exists() and file_path.suffix in (".md", ".txt"):
                        try:
                            content = file_path.read_text(encoding="utf-8")
                            self.state.text_documents.append(TextDocument(
                                filename=filename,
                                content=content
                            ))
                            loaded_count += 1
                            print(f"  ✓ Loaded: {filename} ({len(content)} chars)")
                        except Exception as e:
                            print(f"  ✗ Error loading {filename}: {e}")
                    elif file_path.exists():
                        print(f"  ✗ Unsupported extension: {filename} (only .md and .txt)")
                    else:
                        print(f"  ✗ File not found: {filename}")

                if loaded_count > 0:
                    print(f"\n  Total text documents: {len(self.state.text_documents)}")

            elif "single URL" in choice:
                url = get_input("Enter URL")
                if url:
                    title = get_input("Enter title/description", default="User-provided source")
                    self.state.context_documents.append(Source(
                        url=url,
                        title=title,
                        type="user-provided",
                        anchor_suggestion=title[:30],
                        level="L0",
                        relevance="User-provided context"
                    ))
                    print(f"  Added: {title[:40]}...")

            elif "Clear" in choice:
                self.state.context_documents = []
                self.state.text_documents = []
                print("  All context documents cleared")

            elif "Done" in choice:
                break

        # Summary
        if self.state.context_documents:
            print(f"\n  Total L0 sources: {len(self.state.context_documents)}")
        if self.state.text_documents:
            print(f"  Total text documents: {len(self.state.text_documents)}")
