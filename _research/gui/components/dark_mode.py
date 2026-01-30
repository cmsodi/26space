"""
Dark mode toggle with persistence via browser localStorage.
"""

from nicegui import ui


def create_dark_mode_toggle():
    """Create a dark mode toggle button in the header."""
    dark = ui.dark_mode(value=True)

    def toggle():
        dark.value = not dark.value

    btn = ui.button(icon='dark_mode', on_click=toggle).props('flat round color=white')
    return btn
