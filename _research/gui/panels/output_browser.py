"""
Output browser — browse past analyses in the output/ folder.

Lists output folders, shows file contents, renders markdown reports.
"""

from pathlib import Path
from datetime import datetime
from nicegui import ui

from gui.components.markdown_viewer import create_markdown_viewer, create_markdown_dialog


PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'output'


def create_output_browser():
    """Create the output folder browser panel."""

    ui.label('Output Browser').classes('text-h5 q-mb-md')
    ui.label('Browse past analyses and view generated reports.').classes(
        'text-subtitle2 text-grey q-mb-md'
    )

    content_area = ui.column().classes('w-full')

    def refresh_folders():
        content_area.clear()
        with content_area:
            if not OUTPUT_DIR.exists():
                ui.label('No output/ directory found.').classes('text-grey')
                return

            folders = sorted(
                [d for d in OUTPUT_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')],
                key=lambda d: d.stat().st_mtime,
                reverse=True,
            )

            if not folders:
                ui.label('No analyses found in output/').classes('text-grey')
                return

            for folder in folders:
                _render_folder_card(folder)

    def _render_folder_card(folder: Path):
        """Render a card for an output folder."""
        md_files = sorted(folder.glob('*.md'))
        yaml_files = list(folder.glob('*.yaml'))
        mtime = datetime.fromtimestamp(folder.stat().st_mtime)

        with ui.card().classes('w-full q-mb-sm'):
            with ui.row().classes('w-full justify-between items-center'):
                with ui.column():
                    ui.label(folder.name).classes('text-subtitle1 text-bold')
                    ui.label(
                        f'{len(md_files)} md files, {len(yaml_files)} yaml | '
                        f'Modified: {mtime:%Y-%m-%d %H:%M}'
                    ).classes('text-caption text-grey')

                ui.button(
                    icon='expand_more',
                    on_click=lambda f=folder: _show_folder_contents(f),
                ).props('flat round')

    def _show_folder_contents(folder: Path):
        """Show the contents of a folder in an expansion panel."""
        content_area.clear()
        with content_area:
            # Back button
            ui.button('Back to folders', icon='arrow_back',
                      on_click=refresh_folders).props('flat no-caps')
            ui.separator().classes('q-my-sm')

            ui.label(folder.name).classes('text-h6')

            files = sorted(folder.iterdir())
            md_files = [f for f in files if f.suffix == '.md']
            yaml_files = [f for f in files if f.suffix in ('.yaml', '.yml')]

            # Quick-view buttons for key files
            index_file = folder / 'index.md'
            outline_file = folder / 'outline.md'

            with ui.row().classes('q-gutter-sm q-mb-md'):
                if index_file.exists():
                    ui.button(
                        'View Report',
                        icon='article',
                        on_click=lambda: _view_file(index_file),
                    ).props('color=primary')
                if outline_file.exists():
                    ui.button(
                        'View Outline',
                        icon='format_list_bulleted',
                        on_click=lambda: _view_file(outline_file),
                    ).props('color=secondary outline')

            # File list
            ui.label('All files:').classes('text-subtitle2')

            for f in files:
                with ui.row().classes('items-center q-gutter-xs'):
                    if f.suffix == '.md':
                        icon = 'description'
                        color = 'primary'
                    elif f.suffix in ('.yaml', '.yml'):
                        icon = 'data_object'
                        color = 'warning'
                    else:
                        icon = 'insert_drive_file'
                        color = 'grey'

                    ui.icon(icon, color=color, size='xs')

                    size_kb = f.stat().st_size / 1024
                    btn = ui.button(
                        f'{f.name}  ({size_kb:.1f} KB)',
                        on_click=lambda file=f: _view_file(file),
                    ).props('flat no-caps dense')

    def _view_file(filepath: Path):
        """Open a file in the viewer."""
        try:
            text = filepath.read_text(encoding='utf-8')
        except Exception as e:
            ui.notify(f'Failed to read file: {e}', type='negative')
            return

        if filepath.suffix == '.md':
            create_markdown_dialog(text, title=filepath.name)
        elif filepath.suffix in ('.yaml', '.yml'):
            with ui.dialog().props('maximized') as dialog, ui.card().classes('w-full'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label(filepath.name).classes('text-h5')
                    ui.button(icon='close', on_click=dialog.close).props('flat round')
                ui.separator()
                ui.code(text, language='yaml').classes('w-full').style(
                    'max-height: 80vh; overflow-y: auto;'
                )
            dialog.open()
        else:
            with ui.dialog() as dialog, ui.card():
                ui.label(filepath.name).classes('text-h6')
                ui.code(text).classes('w-full')
                ui.button('Close', on_click=dialog.close)
            dialog.open()

    # Initial render
    refresh_folders()

    # Refresh button
    ui.button('Refresh', icon='refresh', on_click=refresh_folders).props(
        'flat no-caps'
    ).classes('q-mt-sm')
