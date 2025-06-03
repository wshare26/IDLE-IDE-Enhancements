
import builtins
import inspect
import threading
from queue import Queue

# A thread‑safe queue for holding “debug‐print” messages
_message_queue = Queue()

# A thread‑safe set of applied line‑numbers
_debug_lock     = threading.Lock()
_debug_line_set = set()

def set_debug_lines(lines):
    """
    Replace the set of “applied” debug lines with the given iterable of ints.
    """
    global _debug_line_set
    with _debug_lock:
        _debug_line_set = set(lines)

def get_debug_lines():
    """
    Return a copy of the currently applied debug lines (as a set).
    """
    with _debug_lock:
        return set(_debug_line_set)

def _find_caller_lineno():
    """
    Inspect the call stack and return the lineno of whoever called print(...).
    We skip two frames so that we land on the user’s code frame, not inside this helper.
    """
    frm = inspect.currentframe()
    caller = frm.f_back.f_back
    return caller.f_lineno

def _debug_print(*args, sep=" ", end="\n", file=None, flush=False):
    """
    Replacement for builtins.print.  If the calling line number is in _debug_line_set,
    enqueue the text. Otherwise, swallow it (so it never appears).
    """
    lineno = _find_caller_lineno()
    with _debug_lock:
        if lineno in _debug_line_set:
            text = sep.join(str(a) for a in args) + end
            enqueue_message(f"Line {lineno}: {text}")
        # If lineno not in set, do nothing: print is “invisible.”

def install_debug_print():
    """
    Call this before exec(user_code) in IDLE’s subprocess.  It will override
    builtins.print so that subsequent print(...) calls go through _debug_print.
    """
    builtins.print = _debug_print

def enqueue_message(msg):
    """
    Put a new debug message (string) into the queue, for the UI to pull later.
    """
    _message_queue.put(msg)

def poll_messages():
    """
    Drain all queued messages and return them as a list of strings.
    Once returned, the queue is cleared of those messages.
    """
    msgs = []
    while not _message_queue.empty():
        msgs.append(_message_queue.get())
    return msgs

def rpc_set_debug_lines(lines):
    """
    This function is intended to be called *inside* the subprocess
    (via IDLE’s RPC mechanism).  It simply forwards to set_debug_lines.
    """
    set_debug_lines(lines)
    return f"_debug_line_set now = {lines}"
# ──────────────────────────────────────────────────────────────────────────────
