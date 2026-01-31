#!/usr/bin/env python3
"""
Web GUI for the Strategic Research System.

Launches a NiceGUI web interface on localhost.
The CLI (run.py) continues to work unchanged.

Usage:
    python gui.py              # Launch on http://localhost:8080
    python gui.py --port 3000  # Custom port
"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from nicegui import app, ui

from gui.bridge import InteractionBridge
from gui.runner import WorkflowRunner
from gui.layout import create_main_page


def main():
    port = 8080
    if '--port' in sys.argv:
        try:
            port_idx = sys.argv.index('--port')
            port = int(sys.argv[port_idx + 1])
        except (ValueError, IndexError):
            print('Error: --port requires a number')
            sys.exit(1)

    # Serve static assets (CSS)
    static_dir = Path(__file__).parent / 'gui' / 'static'
    app.add_static_files('/static', str(static_dir))

    bridge = InteractionBridge()
    runner = WorkflowRunner(bridge)

    @ui.page('/')
    def index():
        ui.add_head_html('<link rel="stylesheet" href="/static/style.css">')
        create_main_page(bridge, runner)

    print(f'Starting Strategic Research System GUI on http://localhost:{port}')
    ui.run(
        title='Strategic Research System',
        port=port,
        dark=True,
        reload=False,
        show=False,
    )


if __name__ == '__main__':
    main()
