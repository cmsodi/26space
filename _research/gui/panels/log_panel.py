"""
Log panel — real-time display of captured stdout from the orchestrator thread.

Polls the bridge's log_queue and appends text to a scrollable log element.
"""

import queue
from nicegui import ui

from gui.bridge import InteractionBridge


MAX_LOG_LINES = 3000


def create_log_panel(bridge: InteractionBridge) -> ui.log:
    """Create the log panel that displays captured stdout."""

    log_element = ui.log(max_lines=MAX_LOG_LINES).classes(
        'w-full'
    ).style('height: 400px; font-family: monospace; font-size: 13px;')

    async def poll_logs():
        """Drain log queue and append to display (called every 100ms)."""
        lines_batch = []
        try:
            while True:
                text = bridge.log_queue.get_nowait()
                lines_batch.append(text)
        except queue.Empty:
            pass

        if lines_batch:
            combined = ''.join(lines_batch)
            # Split into lines but keep structure
            for line in combined.splitlines():
                if line.strip():
                    log_element.push(line)

    ui.timer(0.1, poll_logs)

    return log_element
