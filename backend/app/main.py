import logging
import atexit
import signal

from flask import Flask, jsonify
from flask_cors import CORS

from api.routes import router, shutdown_runtime
from app.config import settings


app = Flask(__name__)
CORS(
    app,
    origins=["http://127.0.0.1:5173", "http://localhost:5173"],
)

app.register_blueprint(router)

startup_warnings: list[str] = []


def start_optional_runtime() -> None:
    try:
        from scheduler.task_scheduler import scheduler

        scheduler.start()
    except Exception as error:
        message = f"Scheduler startup skipped: {error}"
        startup_warnings.append(message)
        logging.getLogger(__name__).warning(message)

    try:
        from voice.voice_runtime import voice_runtime

        voice_runtime.start()
    except Exception as error:
        message = f"Voice runtime startup skipped: {error}"
        startup_warnings.append(message)
        logging.getLogger(__name__).warning(message)


start_optional_runtime()

_cleanup_done = False


def cleanup_runtime() -> None:
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True
    try:
        shutdown_runtime()
    except Exception as error:
        logging.getLogger(__name__).warning("Runtime cleanup failed: %s", error)


def handle_exit_signal(_signum, _frame) -> None:
    cleanup_runtime()
    raise SystemExit(0)


atexit.register(cleanup_runtime)
for _signal_name in ("SIGINT", "SIGTERM"):
    if hasattr(signal, _signal_name):
        signal.signal(getattr(signal, _signal_name), handle_exit_signal)


@app.get("/")
def root():
    return jsonify(name="JX JARVIS", status="online", warnings=startup_warnings)


if __name__ == "__main__":
    from waitress import serve

    logging.getLogger("waitress.queue").setLevel(logging.ERROR)
    serve(app, host="127.0.0.1", port=settings.backend_port, threads=16)
