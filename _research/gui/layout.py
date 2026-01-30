"""
Main page layout — header, sidebar navigation, content area.

Assembles all panels into a cohesive single-page application.
"""

from nicegui import ui

from gui.bridge import InteractionBridge
from gui.runner import WorkflowRunner
from gui.components.dark_mode import create_dark_mode_toggle
from gui.panels.workflow_panel import create_workflow_panel
from gui.panels.interaction_panel import create_interaction_panel
from gui.panels.log_panel import create_log_panel
from gui.panels.progress_panel import create_progress_panel
from gui.panels.output_browser import create_output_browser
from gui.panels.recipe_catalog import create_recipe_catalog
from gui.panels.state_inspector import create_state_inspector


def create_main_page(bridge: InteractionBridge, runner: WorkflowRunner):
    """Build the complete page layout."""

    # --- Header ---
    with ui.header().classes('items-center justify-between q-px-md'):
        with ui.row().classes('items-center q-gutter-sm'):
            ui.icon('satellite_alt', size='md', color='white')
            ui.label('Strategic Research System').classes(
                'text-h6 text-white'
            )
        with ui.row().classes('items-center q-gutter-xs'):
            # Status indicator
            status_label = ui.label('Idle').classes('text-caption text-white')
            status_icon = ui.icon('circle', size='xs', color='grey')
            create_dark_mode_toggle()

    # --- Status updater ---
    def update_status():
        if bridge.is_running.is_set():
            status_label.text = f'Running — {bridge.current_step}'
            status_icon.props('color=positive')
        elif bridge.is_complete.is_set():
            if bridge.error:
                status_label.text = 'Error'
                status_icon.props('color=negative')
            else:
                status_label.text = 'Complete'
                status_icon.props('color=positive')
        else:
            status_label.text = 'Idle'
            status_icon.props('color=grey')

    ui.timer(0.5, update_status)

    # --- Main content with left drawer ---
    with ui.left_drawer(value=True, bordered=True).classes('q-pa-sm').style(
        'width: 220px'
    ) as drawer:
        ui.label('Navigation').classes('text-subtitle2 text-grey q-mb-sm')

        # Navigation items tracked so we can highlight active
        nav_items = {}

        def nav_button(label, icon, panel_name):
            btn = ui.button(label, icon=icon, on_click=lambda: show_panel(panel_name))
            btn.props('flat align=left no-caps').classes('w-full')
            nav_items[panel_name] = btn
            return btn

        nav_button('Workflow', 'rocket_launch', 'workflow')
        nav_button('Output Browser', 'folder_open', 'output')
        nav_button('Recipe Catalog', 'menu_book', 'recipes')
        nav_button('State Inspector', 'data_object', 'state')

        ui.separator().classes('q-my-md')

        # Completion notification area
        completion_container = ui.column().classes('w-full')

        def check_completion():
            if bridge.is_complete.is_set():
                completion_container.clear()
                with completion_container:
                    if bridge.error:
                        with ui.card().classes('w-full q-pa-xs'):
                            ui.label('Workflow failed').classes(
                                'text-caption text-negative text-bold'
                            )
                            ui.label(str(bridge.error)[:80]).classes(
                                'text-caption text-negative'
                            )
                    elif bridge.workflow_result:
                        with ui.card().classes('w-full q-pa-xs'):
                            ui.label('Workflow complete').classes(
                                'text-caption text-positive text-bold'
                            )
                            ui.label(bridge.workflow_result).classes(
                                'text-caption'
                            )

        ui.timer(1.0, check_completion)

    # --- Content panels ---
    content_area = ui.column().classes('w-full q-pa-md')
    panels = {}

    with content_area:
        # Workflow panel (default visible)
        with ui.column().classes('w-full') as workflow_section:
            create_progress_panel(bridge)
            ui.separator().classes('q-my-sm')
            create_workflow_panel(bridge, runner)
            ui.separator().classes('q-my-sm')
            ui.label('Interaction').classes('text-h6 q-mt-sm')
            create_interaction_panel(bridge)
            ui.separator().classes('q-my-sm')
            ui.label('Log Output').classes('text-h6 q-mt-sm')
            create_log_panel(bridge)
        panels['workflow'] = workflow_section

        # Output browser
        with ui.column().classes('w-full') as output_section:
            create_output_browser()
        output_section.set_visibility(False)
        panels['output'] = output_section

        # Recipe catalog
        with ui.column().classes('w-full') as recipe_section:
            create_recipe_catalog()
        recipe_section.set_visibility(False)
        panels['recipes'] = recipe_section

        # State inspector
        with ui.column().classes('w-full') as state_section:
            create_state_inspector()
        state_section.set_visibility(False)
        panels['state'] = state_section

    def show_panel(name: str):
        for key, panel in panels.items():
            panel.set_visibility(key == name)
        # Highlight active nav button
        for key, btn in nav_items.items():
            if key == name:
                btn.props('color=primary')
            else:
                btn.props(remove='color')
        # Set initial highlight
        if name in nav_items:
            nav_items[name].props('color=primary')

    # Initial state
    show_panel('workflow')
