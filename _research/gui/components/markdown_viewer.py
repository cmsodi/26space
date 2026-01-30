"""
Markdown viewer component — renders markdown content as formatted HTML.
"""

import markdown
from nicegui import ui


def create_markdown_viewer(content: str, title: str = None):
    """Render markdown content in a scrollable card.

    Args:
        content: Raw markdown text
        title: Optional title displayed above the content
    """
    with ui.card().classes('w-full q-pa-md'):
        if title:
            ui.label(title).classes('text-h6')
            ui.separator()

        # Separate YAML frontmatter if present
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                body = parts[2].strip()
                with ui.expansion('Frontmatter', icon='info').classes('w-full q-mb-sm'):
                    ui.code(frontmatter, language='yaml').classes('w-full')

        # Render markdown
        html_content = markdown.markdown(
            body,
            extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists'],
        )

        ui.html(html_content).classes('w-full markdown-body').style(
            'max-height: 600px; overflow-y: auto; padding: 8px;'
        )


def create_markdown_dialog(content: str, title: str = 'Document'):
    """Open markdown content in a fullscreen dialog."""
    with ui.dialog().props('maximized') as dialog, ui.card().classes('w-full'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label(title).classes('text-h5')
            ui.button(icon='close', on_click=dialog.close).props('flat round')
        ui.separator()
        create_markdown_viewer(content, title=None)

    dialog.open()
