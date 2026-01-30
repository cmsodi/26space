"""
Workflow panel — launch forms for all four workflow modes.

Tabbed interface: New Analysis | Resume | From Folder | Recipe
"""

from pathlib import Path
from nicegui import ui

from gui.bridge import InteractionBridge
from gui.runner import WorkflowRunner


PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'output'
CONTEXT_DIR = PROJECT_ROOT / 'context_documents'


def create_workflow_panel(bridge: InteractionBridge, runner: WorkflowRunner):
    """Create the workflow launch panel with tabs for each mode."""

    with ui.card().classes('w-full'):
        with ui.tabs().classes('w-full') as tabs:
            tab_new = ui.tab('New Analysis', icon='add_circle')
            tab_resume = ui.tab('Resume', icon='play_circle')
            tab_folder = ui.tab('From Folder', icon='folder_open')
            tab_recipe = ui.tab('Recipe', icon='menu_book')

        with ui.tab_panels(tabs, value=tab_new).classes('w-full'):
            # --- New Analysis ---
            with ui.tab_panel(tab_new):
                _new_analysis_form(bridge, runner)

            # --- Resume ---
            with ui.tab_panel(tab_resume):
                _resume_form(bridge, runner)

            # --- From Folder ---
            with ui.tab_panel(tab_folder):
                _from_folder_form(bridge, runner)

            # --- Recipe ---
            with ui.tab_panel(tab_recipe):
                _recipe_form(bridge, runner)


def _new_analysis_form(bridge: InteractionBridge, runner: WorkflowRunner):
    """Form for starting a new analysis."""
    ui.label('Enter your analysis problem or research question:').classes('text-subtitle2')

    problem_input = ui.textarea(
        placeholder='e.g., "Analyze European space launch autonomy challenges and strategic options"',
    ).classes('w-full').props('outlined autogrow')

    with ui.row().classes('q-gutter-sm'):
        parallel = ui.checkbox('Parallel analysts', value=True)
        auto_save = ui.checkbox('Auto-save checkpoints', value=True)
        verbose = ui.checkbox('Verbose output', value=True)

    def start():
        problem = problem_input.value.strip()
        if not problem:
            ui.notify('Please enter an analysis problem', type='warning')
            return
        if runner.is_running:
            ui.notify('A workflow is already running', type='negative')
            return
        try:
            runner.start_run(
                problem=problem,
                parallel=parallel.value,
                auto_save=auto_save.value,
                verbose=verbose.value,
            )
            ui.notify('Workflow started', type='positive')
        except Exception as e:
            ui.notify(f'Failed to start: {e}', type='negative')

    ui.button('Start Analysis', on_click=start, icon='rocket_launch').props(
        'color=primary size=lg'
    ).classes('q-mt-md')


def _resume_form(bridge: InteractionBridge, runner: WorkflowRunner):
    """Form for resuming from a checkpoint."""
    ui.label('Select a workflow state file to resume:').classes('text-subtitle2')

    # Find existing state files
    state_files = []
    if OUTPUT_DIR.exists():
        state_files = sorted(OUTPUT_DIR.rglob('workflow_state.yaml'))

    if state_files:
        options = {str(f): f.parent.name for f in state_files}
        state_select = ui.select(
            options=options,
            label='State file',
        ).classes('w-full').props('outlined')
    else:
        ui.label('No workflow_state.yaml files found in output/').classes(
            'text-caption text-grey'
        )
        state_select = None

    with ui.row().classes('q-gutter-sm'):
        parallel = ui.checkbox('Parallel analysts', value=True)
        verbose = ui.checkbox('Verbose output', value=True)

    def start():
        if not state_select or not state_select.value:
            ui.notify('Please select a state file', type='warning')
            return
        if runner.is_running:
            ui.notify('A workflow is already running', type='negative')
            return
        try:
            runner.start_resume(
                state_file=state_select.value,
                parallel=parallel.value,
                verbose=verbose.value,
            )
            ui.notify('Resume started', type='positive')
        except Exception as e:
            ui.notify(f'Failed to resume: {e}', type='negative')

    ui.button('Resume Workflow', on_click=start, icon='play_arrow').props(
        'color=primary size=lg'
    ).classes('q-mt-md')


def _from_folder_form(bridge: InteractionBridge, runner: WorkflowRunner):
    """Form for loading from an output folder."""
    ui.label('Select an output folder to reuse analyst reports:').classes('text-subtitle2')

    # Find output folders that contain analyst reports
    folders = []
    if OUTPUT_DIR.exists():
        for d in sorted(OUTPUT_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith('.'):
                md_count = len(list(d.glob('*.md')))
                if md_count > 0:
                    folders.append(d)

    if folders:
        options = {str(f): f"{f.name}  ({len(list(f.glob('*.md')))} files)" for f in folders}
        folder_select = ui.select(
            options=options,
            label='Output folder',
        ).classes('w-full').props('outlined')
    else:
        ui.label('No output folders found').classes('text-caption text-grey')
        folder_select = None

    with ui.row().classes('q-gutter-sm'):
        parallel = ui.checkbox('Parallel analysts', value=True)
        verbose = ui.checkbox('Verbose output', value=True)

    def start():
        if not folder_select or not folder_select.value:
            ui.notify('Please select a folder', type='warning')
            return
        if runner.is_running:
            ui.notify('A workflow is already running', type='negative')
            return
        try:
            runner.start_from_folder(
                folder_path=folder_select.value,
                parallel=parallel.value,
                verbose=verbose.value,
            )
            ui.notify('Loading from folder...', type='positive')
        except Exception as e:
            ui.notify(f'Failed to load: {e}', type='negative')

    ui.button('Load & Resume', on_click=start, icon='folder_open').props(
        'color=primary size=lg'
    ).classes('q-mt-md')


def _recipe_form(bridge: InteractionBridge, runner: WorkflowRunner):
    """Form for running a recipe."""
    ui.label('Select and run a self-contained recipe:').classes('text-subtitle2')

    # Discover recipes
    try:
        from src.recipe import discover_recipes, load_recipe
        recipe_names = discover_recipes()
    except Exception:
        recipe_names = []

    if recipe_names:
        recipe_info = {}
        for name in recipe_names:
            try:
                r = load_recipe(name)
                recipe_info[name] = f"{name} — {r.description}" if hasattr(r, 'description') else name
            except Exception:
                recipe_info[name] = name

        recipe_select = ui.select(
            options=recipe_info,
            label='Recipe',
        ).classes('w-full').props('outlined')
    else:
        ui.label('No recipes found in .claude/recipes/').classes(
            'text-caption text-grey'
        )
        recipe_select = None

    topic_input = ui.input(
        label='Topic',
        placeholder='e.g., "European Launch Autonomy"',
    ).classes('w-full').props('outlined')

    # Context file (optional)
    context_files = []
    if CONTEXT_DIR.exists():
        context_files = sorted(CONTEXT_DIR.glob('*.yaml'))

    context_select = None
    if context_files:
        options = {'': '(none)'} | {str(f): f.name for f in context_files}
        context_select = ui.select(
            options=options,
            value='',
            label='Context document (optional)',
        ).classes('w-full').props('outlined')

    verbose = ui.checkbox('Verbose output', value=True)

    def start():
        if not recipe_select or not recipe_select.value:
            ui.notify('Please select a recipe', type='warning')
            return
        topic = topic_input.value.strip()
        if not topic:
            ui.notify('Please enter a topic', type='warning')
            return
        if runner.is_running:
            ui.notify('A workflow is already running', type='negative')
            return
        try:
            ctx = context_select.value if context_select and context_select.value else None
            runner.start_recipe(
                recipe_name=recipe_select.value,
                topic=topic,
                context_yaml=ctx,
                verbose=verbose.value,
            )
            ui.notify('Recipe started', type='positive')
        except Exception as e:
            ui.notify(f'Failed to start recipe: {e}', type='negative')

    ui.button('Run Recipe', on_click=start, icon='play_arrow').props(
        'color=primary size=lg'
    ).classes('q-mt-md')
