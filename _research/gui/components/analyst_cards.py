"""
Analyst status cards — grid showing analyst execution status.
"""

from nicegui import ui


STATUS_ICONS = {
    'complete': ('check_circle', 'positive'),
    'partial': ('warning', 'warning'),
    'failed': ('error', 'negative'),
    'running': ('sync', 'primary'),
    'pending': ('schedule', 'grey-5'),
}


def create_analyst_card(name: str, status: str = 'pending',
                        confidence: float = None, key_findings: int = 0):
    """Create a single analyst status card."""
    icon_name, color = STATUS_ICONS.get(status, ('help', 'grey'))

    with ui.card().classes('q-pa-sm').style('min-width: 180px;'):
        with ui.row().classes('items-center q-gutter-xs no-wrap'):
            ui.icon(icon_name, color=color, size='sm')
            ui.label(name.replace('-', ' ').title()).classes(
                'text-subtitle2 ellipsis'
            )

        if confidence is not None:
            with ui.row().classes('items-center q-gutter-xs q-mt-xs'):
                ui.label('Confidence:').classes('text-caption text-grey')
                ui.linear_progress(
                    value=confidence,
                    show_value=False,
                    size='8px',
                    color='primary',
                ).classes('flex-grow')
                ui.label(f'{confidence:.0%}').classes('text-caption')

        if key_findings > 0:
            ui.badge(f'{key_findings} findings', color='primary').props(
                'outline'
            ).classes('q-mt-xs')


def create_analyst_grid(analysts: dict):
    """Create a grid of analyst cards from analyst_outputs dict.

    Args:
        analysts: dict of {name: AnalystOutput} or {name: status_str}
    """
    with ui.row().classes('w-full q-gutter-sm flex-wrap'):
        for name, data in analysts.items():
            if isinstance(data, str):
                create_analyst_card(name, status=data)
            else:
                create_analyst_card(
                    name=name,
                    status=getattr(data, 'status', 'pending'),
                    confidence=getattr(data, 'confidence', None),
                    key_findings=len(getattr(data, 'key_findings', [])),
                )
