"""
Progress panel — visual stepper showing workflow phases.

Renders a horizontal stepper with the 9 Step enum values,
updated in real-time by polling the bridge's current_step.
"""

from nicegui import ui

from gui.bridge import InteractionBridge


STEP_LABELS = {
    "init": "Start",
    "problem_parsed": "Problem",
    "sources_decided": "Sources",
    "clarified": "Clarified",
    "proposal_approved": "Proposal",
    "analysts_complete": "Analysts",
    "outline_approved": "Outline",
    "citations_mapped": "Citations",
    "complete": "Complete",
}

STEP_ORDER = list(STEP_LABELS.keys())
STEP_ICONS = {
    "init": "play_arrow",
    "problem_parsed": "psychology",
    "sources_decided": "source",
    "clarified": "help_outline",
    "proposal_approved": "thumb_up",
    "analysts_complete": "groups",
    "outline_approved": "article",
    "citations_mapped": "format_quote",
    "complete": "check_circle",
}


def create_progress_panel(bridge: InteractionBridge):
    """Create the phase stepper that tracks workflow progress."""

    stepper_container = ui.row().classes('w-full justify-center q-pa-sm')
    step_elements = {}

    with stepper_container:
        for i, step_key in enumerate(STEP_ORDER):
            with ui.column().classes('items-center q-px-xs') as col:
                icon = ui.icon(
                    STEP_ICONS.get(step_key, 'circle'),
                    size='sm',
                    color='grey-5',
                )
                label = ui.label(STEP_LABELS[step_key]).classes(
                    'text-caption text-grey-5'
                ).style('font-size: 10px;')
                step_elements[step_key] = {'icon': icon, 'label': label}

            # Arrow between steps (except last)
            if i < len(STEP_ORDER) - 1:
                ui.icon('arrow_forward', size='xs', color='grey-4').classes(
                    'self-center'
                )

    def update_stepper():
        """Update step colors based on current progress."""
        current = bridge.current_step
        current_idx = STEP_ORDER.index(current) if current in STEP_ORDER else 0

        for i, step_key in enumerate(STEP_ORDER):
            els = step_elements[step_key]
            if i < current_idx:
                # Completed — show checkmark
                els['icon'].props('color=positive name=check_circle')
                els['label'].classes(replace='text-caption text-positive')
            elif i == current_idx:
                # Current — restore original icon
                original_icon = STEP_ICONS.get(step_key, 'circle')
                els['icon'].props(f'color=primary name={original_icon}')
                els['label'].classes(replace='text-caption text-primary text-bold')
            else:
                # Pending — restore original icon
                original_icon = STEP_ICONS.get(step_key, 'circle')
                els['icon'].props(f'color=grey-5 name={original_icon}')
                els['label'].classes(replace='text-caption text-grey-5')

    ui.timer(0.5, update_stepper)

    return stepper_container
