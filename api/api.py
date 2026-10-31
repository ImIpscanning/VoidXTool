"""Small local status API compatible with the original application hook."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _StatusHandler(BaseHTTPRequestHandler):
    server_version = "VoidXToolLocal/1.0"

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/health":
            self.send_error(404)
            return
        payload = json.dumps({"status": "ok", "service": "voidxtool-local"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _format: str, *_args: object) -> None:
        return


class VoidXToolInternalAPI:
    """Bind the optional API to loopback only."""

    def __init__(self, authentication: object, port: int = 8765) -> None:
        self.authentication = authentication
        self.port = port

    def run(self) -> None:
        ThreadingHTTPServer(("127.0.0.1", self.port), _StatusHandler).serve_forever()
