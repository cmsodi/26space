"""
User interaction and terminal output formatting.
"""

from enum import Enum

from .errors import is_retryable_error
from .logging_setup import logger


# ============== USER INTERACTION ==============

def ask_user(prompt: str, options: list[str], allow_other: bool = True) -> str:
    """
    CLI user interaction with numbered options.

    Args:
        prompt: Question to display
        options: List of choices
        allow_other: If True, user can type 'other' for custom input

    Returns:
        Selected option text or custom input
    """
    print(f"\n{'='*60}")
    print(prompt)
    print("-" * 40)
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    if allow_other:
        print(f"  {len(options)+1}. Other (custom input)")
    print("-" * 40)

    while True:
        choice = input("Enter choice (number): ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(options):
                return options[idx - 1]
            elif allow_other and idx == len(options) + 1:
                return input("Enter custom response: ").strip()
        print("Invalid choice. Try again.")


def confirm(prompt: str) -> bool:
    """
    Simple yes/no confirmation.

    Args:
        prompt: Question to display

    Returns:
        True if user confirms, False otherwise
    """
    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")


def get_input(prompt: str, default: str = "") -> str:
    """
    Get free-form input from user.

    Args:
        prompt: Prompt to display
        default: Default value if user presses Enter

    Returns:
        User input or default
    """
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


# ============== TERMINAL OUTPUT FORMATTING ==============

# Emoji mappings for section headers
SECTION_EMOJIS = {
    "orchestrator": "👨‍💼",
    "strategic": "👨‍💼",
    "phase": "🔄",
    "analysis": "🔍",
    "results": "📊",
    "error": "❌",
    "warning": "⚠️",
    "success": "✅",
    "complete": "✅",
    "task": "📋",
    "file": "📁",
    "recovery": "🔧",
    "proposal": "📝",
    "execution": "⚡",
    "outline": "📄",
    "citation": "📚",
    "text": "📝",
    "config": "⚙️",
    "resume": "▶️",
    "checkpoint": "💾",
}


def section_header(title: str, emoji: str = None, width: int = 60) -> str:
    """
    Generate a formatted section header with emoji.

    Args:
        title: Section title text
        emoji: Optional emoji override. If None, auto-detect from title keywords
        width: Width of the separator line (default 60)

    Returns:
        Formatted header string ready for print()
    """
    # Auto-detect emoji from title if not provided
    if emoji is None:
        title_lower = title.lower()
        for keyword, em in SECTION_EMOJIS.items():
            if keyword in title_lower:
                emoji = em
                break
        else:
            emoji = "📌"  # Default emoji

    separator = "=" * width
    return f"\n{separator}\n{emoji} {title.upper()}\n{separator}"


def print_section_header(title: str, emoji: str = None, width: int = 60):
    """Print a formatted section header with emoji."""
    print(section_header(title, emoji, width))


def display_section(title: str, content: str, width: int = 60, emoji: str = None):
    """Display a formatted section with title and content."""
    print(section_header(title, emoji, width))
    print(content)
    print("=" * width)


# ============== ERROR RECOVERY UI ==============

class RecoveryAction(Enum):
    """User choices when an error occurs."""
    RETRY = "retry"
    SKIP = "skip"
    ABORT = "abort"
    RETRY_FAILED = "retry_failed"  # Re-run only failed items
    CONTINUE_PARTIAL = "continue_partial"  # Continue with partial results


def recovery_menu(
    error: Exception,
    context: str,
    options: list[RecoveryAction] = None
) -> RecoveryAction:
    """
    Present recovery options to user after an error.

    Args:
        error: The exception that occurred
        context: What operation was being performed
        options: Available recovery actions (default: RETRY, SKIP, ABORT)

    Returns:
        Selected RecoveryAction
    """
    if options is None:
        options = [RecoveryAction.RETRY, RecoveryAction.SKIP, RecoveryAction.ABORT]

    print_section_header(f"ERROR: {context}", emoji="❌")
    print(f"\n  {error}\n")

    # Check if retryable
    if is_retryable_error(error):
        print("  (This appears to be a temporary error that may succeed on retry)")
    else:
        print("  (This appears to be a permanent error)")
        # Remove RETRY if non-retryable
        if RecoveryAction.RETRY in options:
            options = [o for o in options if o != RecoveryAction.RETRY]

    # Display options
    option_labels = {
        RecoveryAction.RETRY: "Retry the operation",
        RecoveryAction.SKIP: "Skip and continue",
        RecoveryAction.ABORT: "Abort the workflow",
        RecoveryAction.RETRY_FAILED: "Retry only failed items",
        RecoveryAction.CONTINUE_PARTIAL: "Continue with partial results",
    }

    print("\nWhat would you like to do?")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {option_labels.get(opt, opt.value)}")

    while True:
        try:
            choice = input("\nEnter choice [1]: ").strip()
            if not choice:
                return options[0]
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print(f"Please enter a number 1-{len(options)}")
        except ValueError:
            print(f"Please enter a number 1-{len(options)}")


def should_continue_on_error(
    error: Exception,
    context: str,
    auto_recovery: bool = False,
    default_action: RecoveryAction = RecoveryAction.ABORT
) -> bool:
    """
    Determine whether to continue after an error.

    Args:
        error: The exception that occurred
        context: What operation was being performed
        auto_recovery: If True, use default_action without prompting
        default_action: Action to take in auto_recovery mode

    Returns:
        True if workflow should continue, False to abort
    """
    if auto_recovery:
        logger.info(f"Auto-recovery: {default_action.value} for {context}")
        return default_action in (
            RecoveryAction.SKIP,
            RecoveryAction.CONTINUE_PARTIAL,
            RecoveryAction.RETRY_FAILED
        )

    action = recovery_menu(error, context)
    return action != RecoveryAction.ABORT
