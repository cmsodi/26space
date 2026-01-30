"""
Interaction panel — renders browser-based dialogs for orchestrator requests.

Polls the InteractionBridge queue and dynamically creates NiceGUI dialogs
for ask_user, confirm, get_input, and recovery_menu interactions.
"""

import queue
from nicegui import ui

from gui.bridge import InteractionBridge, InteractionRequest, InteractionType


def create_interaction_panel(bridge: InteractionBridge):
    """Create the interaction panel that polls for orchestrator requests."""

    interaction_container = ui.column().classes('w-full')

    async def check_interactions():
        """Poll for pending interaction requests (called every 100ms)."""
        try:
            request = bridge.request_queue.get_nowait()
        except queue.Empty:
            return

        if request.type == InteractionType.SECTION_HEADER:
            # Display-only — already handled by TeeStdout, skip
            return
        elif request.type == InteractionType.DISPLAY_SECTION:
            # Display-only — already handled by TeeStdout, skip
            return
        elif request.type == InteractionType.ASK_USER:
            _render_ask_user(interaction_container, bridge, request)
        elif request.type == InteractionType.CONFIRM:
            _render_confirm(interaction_container, bridge, request)
        elif request.type == InteractionType.GET_INPUT:
            _render_get_input(interaction_container, bridge, request)
        elif request.type == InteractionType.RECOVERY_MENU:
            _render_recovery_menu(interaction_container, bridge, request)

    ui.timer(0.1, check_interactions)

    return interaction_container


def _render_ask_user(container: ui.column, bridge: InteractionBridge,
                     request: InteractionRequest):
    """Render a choice dialog for ask_user()."""
    container.clear()

    with container:
        with ui.card().classes('w-full q-pa-md'):
            ui.label('Action Required').classes(
                'text-h6 text-primary'
            )
            ui.separator()
            ui.markdown(request.prompt).classes('q-my-sm')

            selected = {'value': request.options[0] if request.options else ''}
            custom_input = {'ref': None}

            with ui.column().classes('w-full q-gutter-xs'):
                radio = ui.radio(
                    options={opt: opt for opt in request.options},
                    value=request.options[0] if request.options else None,
                ).classes('w-full')
                radio.on_value_change(lambda e: selected.update({'value': e.value}))

                if request.allow_other:
                    with ui.row().classes('w-full items-center q-mt-sm'):
                        other_check = ui.checkbox('Custom response')
                        other_input = ui.input(
                            placeholder='Type custom response...'
                        ).classes('flex-grow').bind_visibility_from(other_check, 'value')
                        custom_input['ref'] = other_input

            def submit():
                if request.allow_other and custom_input['ref'] and other_check.value:
                    value = custom_input['ref'].value or ''
                    if value.strip():
                        bridge.respond(request, value.strip())
                        container.clear()
                        with container:
                            _render_answered(request.prompt, value.strip())
                        return
                bridge.respond(request, selected['value'])
                container.clear()
                with container:
                    _render_answered(request.prompt, selected['value'])

            ui.button('Submit', on_click=submit, icon='send').props(
                'color=primary'
            ).classes('q-mt-md')


def _render_confirm(container: ui.column, bridge: InteractionBridge,
                    request: InteractionRequest):
    """Render a yes/no dialog for confirm()."""
    container.clear()

    with container:
        with ui.card().classes('w-full q-pa-md'):
            ui.label('Confirmation Required').classes(
                'text-h6 text-warning'
            )
            ui.separator()
            ui.markdown(request.prompt).classes('q-my-sm')

            with ui.row().classes('q-mt-md q-gutter-sm'):
                def yes():
                    bridge.respond(request, True)
                    container.clear()
                    with container:
                        _render_answered(request.prompt, 'Yes')

                def no():
                    bridge.respond(request, False)
                    container.clear()
                    with container:
                        _render_answered(request.prompt, 'No')

                ui.button('Yes', on_click=yes, icon='check').props(
                    'color=positive'
                )
                ui.button('No', on_click=no, icon='close').props(
                    'color=negative outline'
                )


def _render_get_input(container: ui.column, bridge: InteractionBridge,
                      request: InteractionRequest):
    """Render a text input dialog for get_input()."""
    container.clear()

    with container:
        with ui.card().classes('w-full q-pa-md'):
            ui.label('Input Required').classes(
                'text-h6 text-primary'
            )
            ui.separator()
            ui.markdown(request.prompt).classes('q-my-sm')

            text_input = ui.input(
                value=request.default,
                placeholder='Type your response...',
            ).classes('w-full q-my-sm')

            def submit():
                value = text_input.value.strip() if text_input.value else ''
                if not value and request.default:
                    value = request.default
                bridge.respond(request, value)
                container.clear()
                with container:
                    _render_answered(request.prompt, value)

            # Submit on Enter key
            text_input.on('keydown.enter', submit)

            ui.button('Submit', on_click=submit, icon='send').props(
                'color=primary'
            )


def _render_recovery_menu(container: ui.column, bridge: InteractionBridge,
                          request: InteractionRequest):
    """Render an error recovery dialog for recovery_menu()."""
    container.clear()

    with container:
        with ui.card().classes('w-full q-pa-md'):
            ui.label('Error Recovery').classes(
                'text-h6 text-negative'
            )
            ui.separator()

            # Error details
            with ui.card().classes('w-full q-pa-sm').style(
                'border-left: 3px solid var(--q-negative)'
            ):
                ui.label(f'Context: {request.context}').classes('text-bold')
                if request.error:
                    ui.label(str(request.error)).classes(
                        'text-caption text-grey-8'
                    )

            ui.label('What would you like to do?').classes('q-mt-md')

            selected = {'value': request.options[0] if request.options else ''}

            radio = ui.radio(
                options={opt: opt for opt in request.options},
                value=request.options[0] if request.options else None,
            ).classes('w-full')
            radio.on_value_change(lambda e: selected.update({'value': e.value}))

            def submit():
                bridge.respond(request, selected['value'])
                container.clear()
                with container:
                    _render_answered('Recovery action', selected['value'])

            ui.button('Proceed', on_click=submit, icon='build').props(
                'color=warning'
            ).classes('q-mt-md')


def _render_answered(prompt: str, answer: str):
    """Show a compact record of a past interaction."""
    with ui.card().classes('w-full q-pa-xs q-mb-xs').style(
        'background-color: var(--q-dark-page, #f5f5f5); opacity: 0.7'
    ):
        with ui.row().classes('items-center q-gutter-xs'):
            ui.icon('check_circle', color='positive', size='xs')
            ui.label(prompt[:60]).classes('text-caption text-grey')
            ui.badge(answer[:40], color='grey-6').props('outline')
