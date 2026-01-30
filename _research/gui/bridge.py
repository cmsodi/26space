"""
Thread-safe bridge between the orchestrator background thread and the NiceGUI UI thread.

The orchestrator calls blocking UI functions (ask_user, confirm, get_input).
These patched versions put an InteractionRequest on a queue and wait.
The NiceGUI main thread polls the queue, renders a dialog, and responds.
"""

import io
import queue
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class InteractionType(Enum):
    ASK_USER = "ask_user"
    CONFIRM = "confirm"
    GET_INPUT = "get_input"
    RECOVERY_MENU = "recovery_menu"
    # Display-only (auto-responded, non-blocking for orchestrator)
    SECTION_HEADER = "section_header"
    DISPLAY_SECTION = "display_section"


@dataclass
class InteractionRequest:
    """A request from the orchestrator thread to the UI thread."""
    type: InteractionType
    prompt: str
    options: list[str] = field(default_factory=list)
    allow_other: bool = True
    default: str = ""
    error: Optional[Exception] = None
    context: str = ""
    # Response channel
    response: Any = None
    event: threading.Event = field(default_factory=threading.Event)


class InteractionBridge:
    """Thread-safe bridge between orchestrator and NiceGUI."""

    def __init__(self):
        self.request_queue: queue.Queue[InteractionRequest] = queue.Queue()
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.is_running = threading.Event()
        self.is_complete = threading.Event()
        self.error: Optional[Exception] = None
        self.current_step: str = "init"
        self.workflow_result: Optional[str] = None

    def post_request(self, request: InteractionRequest) -> Any:
        """Called from orchestrator thread. Blocks until UI responds."""
        self.request_queue.put(request)
        # Block until NiceGUI sets the response (timeout 5 min)
        responded = request.event.wait(timeout=300)
        if not responded:
            raise RuntimeError("GUI interaction timeout — no response in 300s")
        return request.response

    def post_display(self, request: InteractionRequest):
        """Called from orchestrator thread for display-only events. Non-blocking."""
        request.response = None
        request.event.set()  # Pre-set so it doesn't block
        self.request_queue.put(request)

    def respond(self, request: InteractionRequest, response: Any):
        """Called from NiceGUI UI thread. Unblocks the orchestrator."""
        request.response = response
        request.event.set()

    def post_log(self, text: str):
        """Add a log line (thread-safe)."""
        self.log_queue.put(text)

    def reset(self):
        """Reset bridge state for a new workflow run."""
        # Drain queues
        while not self.request_queue.empty():
            try:
                self.request_queue.get_nowait()
            except queue.Empty:
                break
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except queue.Empty:
                break
        self.is_running.clear()
        self.is_complete.clear()
        self.error = None
        self.current_step = "init"
        self.workflow_result = None


class TeeStdout(io.TextIOBase):
    """
    Replaces sys.stdout during workflow execution.
    Writes to both the original stdout (for debugging) and a queue (for the web log panel).
    Thread-safe.
    """

    def __init__(self, log_queue: queue.Queue, original_stdout):
        self.log_queue = log_queue
        self.original = original_stdout
        self._lock = threading.Lock()

    def write(self, text: str) -> int:
        if text:
            with self._lock:
                self.original.write(text)
                self.log_queue.put(text)
        return len(text) if text else 0

    def flush(self):
        self.original.flush()

    def fileno(self):
        return self.original.fileno()

    @property
    def encoding(self):
        return self.original.encoding

    def isatty(self):
        return False

    def readable(self):
        return False

    def writable(self):
        return True
