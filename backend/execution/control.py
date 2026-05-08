from threading import Event


_pause = Event()
_cancel = Event()


def pause_execution() -> dict[str, str]:
    _pause.set()
    return {"status": "paused", "message": "Execution pause requested."}


def resume_execution() -> dict[str, str]:
    _pause.clear()
    return {"status": "running", "message": "Execution resumed."}


def cancel_execution() -> dict[str, str]:
    _cancel.set()
    _pause.clear()
    return {"status": "cancelled", "message": "Execution cancellation requested."}


def reset_execution_control() -> None:
    _pause.clear()
    _cancel.clear()


def execution_control_state() -> dict[str, bool]:
    return {"paused": _pause.is_set(), "cancelled": _cancel.is_set()}


def checkpoint() -> None:
    if _cancel.is_set():
        raise RuntimeError("Execution cancelled by user.")
    while _pause.is_set():
        if _cancel.is_set():
            raise RuntimeError("Execution cancelled by user.")
        _pause.wait(0.25)
