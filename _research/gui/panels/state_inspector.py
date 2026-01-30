"""
State inspector — visual viewer for WorkflowState YAML files.

Loads workflow_state.yaml from output folders and displays
the state as a structured tree with badges and expandable sections.
"""

from pathlib import Path
from nicegui import ui

from gui.components.step_indicator import create_step_badges


PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'output'


def create_state_inspector():
    """Create the state inspector panel."""

    ui.label('State Inspector').classes('text-h5 q-mb-md')
    ui.label(
        'Load and inspect workflow checkpoint files.'
    ).classes('text-subtitle2 text-grey q-mb-md')

    # Find state files
    state_files = []
    if OUTPUT_DIR.exists():
        state_files = sorted(OUTPUT_DIR.rglob('workflow_state.yaml'), reverse=True)

    if not state_files:
        ui.label('No workflow_state.yaml files found in output/').classes('text-grey')
        return

    options = {str(f): f.parent.name for f in state_files}
    select = ui.select(
        options=options,
        label='Select state file',
    ).classes('w-full q-mb-md').props('outlined')

    display_area = ui.column().classes('w-full')

    def load_state():
        if not select.value:
            ui.notify('Select a state file first', type='warning')
            return

        display_area.clear()

        try:
            import yaml
            from src.state import workflow_state_from_dict

            with open(select.value, 'r') as f:
                raw = yaml.safe_load(f)

            state = workflow_state_from_dict(raw)
        except Exception as e:
            with display_area:
                ui.label(f'Failed to load state: {e}').classes('text-negative')
            return

        with display_area:
            _render_state(state, raw)

    ui.button('Load State', on_click=load_state, icon='download').props(
        'color=primary'
    )

    return display_area


def _render_state(state, raw_dict: dict):
    """Render a loaded WorkflowState."""

    # --- Overview ---
    with ui.card().classes('w-full q-pa-md q-mb-sm'):
        ui.label('Overview').classes('text-h6')
        ui.separator()

        with ui.row().classes('q-gutter-md'):
            _kv('Problem', state.problem[:100] if state.problem else '—')
            _kv('Language', state.language or '—')
            _kv('Slug', state.slug or '—')

        ui.label('Progress:').classes('text-subtitle2 q-mt-sm')
        step_val = state.current_step.value if hasattr(state.current_step, 'value') else str(state.current_step)
        create_step_badges(step_val)

    # --- Configuration ---
    with ui.card().classes('w-full q-pa-md q-mb-sm'):
        with ui.expansion('Configuration', icon='settings').classes('w-full'):
            with ui.row().classes('q-gutter-md'):
                _kv('Synthesizer', state.synthesizer or '—')
                _kv('Template', state.template or '—')
                _kv('Web Search', 'Enabled' if state.web_search_enabled else 'Disabled')

            if state.fixed_analysts:
                ui.label('Fixed analysts:').classes('text-subtitle2 q-mt-sm')
                with ui.row().classes('q-gutter-xs'):
                    for a in state.fixed_analysts:
                        ui.badge(a, color='primary').props('outline')

            if state.optional_analysts:
                ui.label('Optional analysts:').classes('text-subtitle2 q-mt-xs')
                with ui.row().classes('q-gutter-xs'):
                    for a in state.optional_analysts:
                        ui.badge(a, color='secondary').props('outline')

    # --- Synthesizer Scores ---
    if state.synthesizer_scores:
        with ui.card().classes('w-full q-pa-md q-mb-sm'):
            with ui.expansion('Synthesizer Scores', icon='bar_chart').classes('w-full'):
                for name, score in sorted(
                    state.synthesizer_scores.items(),
                    key=lambda x: x[1],
                    reverse=True,
                ):
                    with ui.row().classes('w-full items-center q-gutter-sm'):
                        ui.label(name).classes('text-body2').style('min-width: 200px;')
                        ui.linear_progress(
                            value=score, show_value=False, size='10px',
                        ).classes('flex-grow')
                        ui.label(f'{score:.2f}').classes('text-caption')

    # --- Analyst Outputs ---
    if state.analyst_outputs:
        with ui.card().classes('w-full q-pa-md q-mb-sm'):
            with ui.expansion(
                f'Analyst Outputs ({len(state.analyst_outputs)})',
                icon='groups',
            ).classes('w-full'):
                for name, output in state.analyst_outputs.items():
                    status = getattr(output, 'status', '?')
                    confidence = getattr(output, 'confidence', None)
                    findings = getattr(output, 'key_findings', [])

                    with ui.expansion(
                        f'{name} — {status}',
                        icon='person',
                    ).classes('w-full q-mb-xs'):
                        if confidence is not None:
                            _kv('Confidence', f'{confidence:.0%}')
                        if findings:
                            ui.label('Key findings:').classes('text-subtitle2')
                            for f in findings:
                                ui.label(f'  - {f}').classes('text-body2')
                        content = getattr(output, 'content', '')
                        if content:
                            _kv('Content length', f'{len(content)} chars')

    # --- Context Documents ---
    if state.context_documents:
        with ui.card().classes('w-full q-pa-md q-mb-sm'):
            with ui.expansion(
                f'Context Documents ({len(state.context_documents)})',
                icon='source',
            ).classes('w-full'):
                for doc in state.context_documents:
                    title = getattr(doc, 'title', '?')
                    level = getattr(doc, 'level', '?')
                    url = getattr(doc, 'url', '')
                    with ui.row().classes('items-center q-gutter-xs'):
                        ui.badge(level, color='grey').props('outline')
                        ui.label(title).classes('text-body2')

    # --- Errors & Warnings ---
    if state.errors or state.warnings:
        with ui.card().classes('w-full q-pa-md q-mb-sm'):
            with ui.expansion('Errors & Warnings', icon='warning').classes('w-full'):
                for err in (state.errors or []):
                    ui.label(f'ERROR: {err}').classes('text-negative text-body2')
                for warn in (state.warnings or []):
                    ui.label(f'WARNING: {warn}').classes('text-warning text-body2')

    # --- Raw YAML ---
    with ui.card().classes('w-full q-pa-md q-mb-sm'):
        with ui.expansion('Raw YAML', icon='code').classes('w-full'):
            import yaml
            ui.code(
                yaml.dump(raw_dict, default_flow_style=False, allow_unicode=True)[:5000],
                language='yaml',
            ).classes('w-full')


def _kv(key: str, value: str):
    """Render a key-value pair inline."""
    with ui.row().classes('items-center q-gutter-xs'):
        ui.label(f'{key}:').classes('text-caption text-grey text-bold')
        ui.label(value).classes('text-body2')
