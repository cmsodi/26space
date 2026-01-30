"""
Step indicator — reusable horizontal stepper component.

Used by the progress panel and state inspector to show workflow progress.
"""

from nicegui import ui


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


def create_step_badges(current_step: str):
    """Create a row of step badges showing workflow progress.

    Args:
        current_step: The current Step enum value string
    """
    current_idx = STEP_ORDER.index(current_step) if current_step in STEP_ORDER else 0

    with ui.row().classes('q-gutter-xs flex-wrap'):
        for i, step_key in enumerate(STEP_ORDER):
            label = STEP_LABELS[step_key]
            if i < current_idx:
                ui.badge(label, color='positive').props('outline')
            elif i == current_idx:
                ui.badge(label, color='primary')
            else:
                ui.badge(label, color='grey-4').props('outline')
