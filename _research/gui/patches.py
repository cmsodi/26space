"""
Monkey-patch UI functions on consumer modules.

The orchestrator and recipe modules import UI functions as local names
(e.g. `from .ui import ask_user`). Patching `src.ui` module wouldn't affect
the already-bound references. We must patch directly on the consumer modules.

Patches are installed before a workflow starts and removed after completion.
"""

from src.ui import RecoveryAction
from .bridge import InteractionBridge, InteractionRequest, InteractionType


def install_patches(bridge: InteractionBridge):
    """Replace UI functions in consumer modules with web-bridged versions."""
    import src.orchestrator as orch_mod
    import src.recipe as recipe_mod

    # --- Blocking interaction functions ---

    def web_ask_user(prompt: str, options: list[str], allow_other: bool = True) -> str:
        req = InteractionRequest(
            type=InteractionType.ASK_USER,
            prompt=prompt,
            options=list(options),
            allow_other=allow_other,
        )
        return bridge.post_request(req)

    def web_confirm(prompt: str) -> bool:
        req = InteractionRequest(
            type=InteractionType.CONFIRM,
            prompt=prompt,
        )
        return bridge.post_request(req)

    def web_get_input(prompt: str, default: str = "") -> str:
        req = InteractionRequest(
            type=InteractionType.GET_INPUT,
            prompt=prompt,
            default=default,
        )
        return bridge.post_request(req)

    def web_recovery_menu(
        error: Exception,
        context: str,
        options: list[RecoveryAction] = None
    ) -> RecoveryAction:
        if options is None:
            options = [RecoveryAction.RETRY, RecoveryAction.SKIP, RecoveryAction.ABORT]

        option_labels = {
            RecoveryAction.RETRY: "Retry the operation",
            RecoveryAction.SKIP: "Skip and continue",
            RecoveryAction.ABORT: "Abort the workflow",
            RecoveryAction.RETRY_FAILED: "Retry only failed items",
            RecoveryAction.CONTINUE_PARTIAL: "Continue with partial results",
        }

        # Check retryable
        from src.errors import is_retryable_error
        if not is_retryable_error(error):
            options = [o for o in options if o != RecoveryAction.RETRY]

        display_options = [option_labels.get(o, o.value) for o in options]

        req = InteractionRequest(
            type=InteractionType.RECOVERY_MENU,
            prompt=f"Error in: {context}",
            options=display_options,
            error=error,
            context=context,
        )
        response_label = bridge.post_request(req)

        # Map label back to enum
        for action, label in option_labels.items():
            if label == response_label:
                return action
        return RecoveryAction.ABORT

    # --- Display-only functions (non-blocking) ---

    def web_print_section_header(title: str, emoji: str = None, width: int = 60):
        # These are also captured by TeeStdout via print(), but we send a
        # structured event for better rendering in the UI
        from src.ui import section_header as _original_section_header
        formatted = _original_section_header(title, emoji, width)
        # Print so TeeStdout captures it for the log
        print(formatted)

    def web_display_section(title: str, content: str, width: int = 60, emoji: str = None):
        from src.ui import section_header as _original_section_header
        formatted = _original_section_header(title, emoji, width)
        print(formatted)
        print(content)
        print("=" * width)

    # --- Apply patches to orchestrator module ---
    orch_mod.ask_user = web_ask_user
    orch_mod.confirm = web_confirm
    orch_mod.get_input = web_get_input
    orch_mod.recovery_menu = web_recovery_menu
    orch_mod.print_section_header = web_print_section_header
    orch_mod.display_section = web_display_section
    # NOTE: section_header (returns string) is used with _vprint() — keep original.
    # The print() from _vprint() is captured by TeeStdout.

    # --- Apply patches to recipe module ---
    recipe_mod.get_input = web_get_input
    recipe_mod.print_section_header = web_print_section_header
    recipe_mod.confirm = web_confirm


def uninstall_patches():
    """Restore original UI functions from src.ui."""
    import src.orchestrator as orch_mod
    import src.recipe as recipe_mod
    from src.ui import (
        ask_user, confirm, get_input,
        section_header, print_section_header, display_section,
        recovery_menu
    )

    orch_mod.ask_user = ask_user
    orch_mod.confirm = confirm
    orch_mod.get_input = get_input
    orch_mod.recovery_menu = recovery_menu
    orch_mod.print_section_header = print_section_header
    orch_mod.display_section = display_section

    recipe_mod.get_input = get_input
    recipe_mod.print_section_header = print_section_header
    recipe_mod.confirm = confirm
