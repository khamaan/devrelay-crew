"""Local-only web interface for the CrewAI showcase."""
from __future__ import annotations

import argparse
import json
import os
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .crew import DEFAULT_MODEL, MODEL_CHOICES, run_crew

STATIC = Path(__file__).with_name("static")
RUNS: dict[str, dict[str, Any]] = {}
LOCK = threading.Lock()
ONE_RUN = threading.Semaphore(1)


def _run_job(run_id: str, idea: str, api_key: str, model: str) -> None:
    def emit(event: dict[str, Any]) -> None:
        with LOCK:
            RUNS[run_id]["events"].append(event)

    try:
        result = run_crew(idea, api_key, model, emit)
        with LOCK:
            RUNS[run_id].update(status="complete", result=result)
    except Exception as exc:
        # Provider exceptions can include prompt content; never send their raw text to the UI.
        with LOCK:
            RUNS[run_id].update(status="error", error=(
                f"Crew run failed ({type(exc).__name__}). Check the API key, model access, "
                "and quota, then try again."))
    finally:
        api_key = ""
        ONE_RUN.release()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _json(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _file(self, name: str, content_type: str) -> None:
        data = (STATIC / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        files = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/app.css": ("app.css", "text/css; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8")}
        if self.path in files:
            self._file(*files[self.path])
        elif self.path == "/api/config":
            self._json(200, {"model": DEFAULT_MODEL, "models": sorted(MODEL_CHOICES),
                             "key_configured": bool(os.getenv("GEMINI_API_KEY"))})
        elif self.path.startswith("/api/runs/"):
            run_id = self.path.removeprefix("/api/runs/")
            with LOCK:
                run = RUNS.get(run_id)
                snapshot = json.loads(json.dumps(run)) if run else None
            self._json(200, snapshot) if snapshot else self._json(404, {"error": "Run not found"})
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/api/runs":
            self._json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4000:
                raise ValueError("Request is too large")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Expected a JSON object")
            idea = body.get("idea")
            if not isinstance(idea, str) or not 12 <= len(idea.strip()) <= 500:
                raise ValueError("Describe the utility in 12–500 characters")
            model = body.get("model", DEFAULT_MODEL)
            if model not in MODEL_CHOICES:
                raise ValueError("Choose one of the listed Gemini models")
            api_key = body.get("api_key") or os.getenv("GEMINI_API_KEY")
            if not isinstance(api_key, str) or not 10 <= len(api_key) <= 512:
                raise ValueError("Enter your Gemini API key")
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
            return
        if not ONE_RUN.acquire(blocking=False):
            self._json(429, {"error": "A crew is already running. Wait for it to finish."})
            return
        run_id = uuid.uuid4().hex
        with LOCK:
            RUNS[run_id] = {"id": run_id, "status": "running", "model": model,
                            "events": [], "result": None, "error": None}
            if len(RUNS) > 12:
                for old in list(RUNS):
                    if old != run_id and RUNS[old]["status"] != "running":
                        del RUNS[old]
                        break
        threading.Thread(target=_run_job, args=(run_id, idea.strip(), api_key, model), daemon=True).start()
        self._json(202, {"id": run_id})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DevRelay Crew in a local browser")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"DevRelay Crew is running at {url} | close this window to stop it", flush=True)
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
