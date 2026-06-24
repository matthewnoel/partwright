"""`partwright sketch` — launch the SVG click-to-draw sketch tool.

This module implements the body of `run(args)` for `partwright sketch`. It
starts a tiny standard-library `http.server` that serves the self-contained
`web/sketch.html` drawing page, auto-opens it in the browser, and exposes a
small JSON/SVG API so drawings save into, list from, and load back out of the
`--dest` folder.

The same `sketch.html` also works opened directly via `file://`; the server is
purely an optional convenience layer. Standard library only — no third-party
imports.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import socket
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

__all__ = ["run"]

# Location of the self-contained drawing page. It ships inside the package at
# partwright/web/sketch.html, resolved through importlib.resources so it is found
# whether Partwright runs from a clone or an installed wheel.
_SKETCH_HTML = Path(str(files("partwright") / "web" / "sketch.html"))

# Largest SVG body we will accept on a save request (generous; sketches are
# tiny text files — this is purely a sanity bound against a runaway upload).
_MAX_SAVE_BYTES = 8 * 1024 * 1024


def _safe_svg_name(raw: str) -> str | None:
    """Return a sanitized, single-component ``*.svg`` file name, or ``None``.

    Rejects anything with path separators, parent-directory components, or a
    non-``.svg`` extension so a request can never escape the destination
    folder. The server never trusts a client-supplied name without this.
    """
    if not raw:
        return None
    name = raw.strip()
    # reject path traversal / nested paths outright
    if "/" in name or "\\" in name or name in (".", ".."):
        return None
    candidate = Path(name)
    if candidate.name != name:  # had a directory component
        return None
    if candidate.suffix.lower() != ".svg":
        name = name + ".svg"
        candidate = Path(name)
    # final guard: still a plain name after suffix fixup
    if candidate.name != name or "/" in name or "\\" in name:
        return None
    return name


def _make_handler(html_bytes: bytes, dest: Path):
    """Build the request-handler class, closing over the page and dest folder."""

    class SketchHandler(BaseHTTPRequestHandler):
        # quieter, single-line request logging
        def log_message(self, fmt: str, *fmt_args) -> None:  # noqa: D401
            msg = fmt % fmt_args
            print(f"  [sketch] {self.address_string()} {msg}")

        # -- response helpers ------------------------------------------------
        def _send(
            self,
            status: HTTPStatus,
            body: bytes,
            content_type: str = "text/plain; charset=utf-8",
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with contextlib.suppress(BrokenPipeError, ConnectionResetError):
                self.wfile.write(body)

        def _send_json(self, status: HTTPStatus, payload: dict) -> None:
            self._send(
                status,
                json.dumps(payload).encode("utf-8"),
                "application/json; charset=utf-8",
            )

        # -- routing ---------------------------------------------------------
        def do_GET(self) -> None:  # noqa: N802 (http.server naming)
            parts = urlsplit(self.path)
            route = parts.path
            if route in ("/", "/index.html", "/sketch.html"):
                self._send(HTTPStatus.OK, html_bytes, "text/html; charset=utf-8")
            elif route == "/api/list":
                self._handle_list()
            elif route == "/api/load":
                self._handle_load(parse_qs(parts.query))
            else:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            parts = urlsplit(self.path)
            if parts.path == "/api/save":
                self._handle_save(parse_qs(parts.query))
            else:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        # -- endpoint implementations ---------------------------------------
        def _handle_list(self) -> None:
            try:
                names = sorted(p.name for p in dest.glob("*.svg") if p.is_file())
            except OSError as exc:
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.OK, {"files": names})

        def _handle_load(self, query: dict) -> None:
            raw = (query.get("name") or [""])[0]
            name = _safe_svg_name(raw)
            if name is None:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid file name"})
                return
            target = dest / name
            if not target.is_file():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": f"{name} not found"})
                return
            try:
                body = target.read_bytes()
            except OSError as exc:
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return
            self._send(HTTPStatus.OK, body, "image/svg+xml; charset=utf-8")

        def _handle_save(self, query: dict) -> None:
            raw = (query.get("name") or [""])[0]
            name = _safe_svg_name(raw)
            if name is None:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid file name"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "empty request body"})
                return
            if length > _MAX_SAVE_BYTES:
                self._send_json(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    {"error": "SVG too large"},
                )
                return
            body = self.rfile.read(length)
            target = dest / name
            try:
                dest.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
            except OSError as exc:
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return
            print(f"  [sketch] saved {target}")
            self._send_json(
                HTTPStatus.OK, {"ok": True, "name": name, "path": str(target)}
            )

    return SketchHandler


def _pick_port(host: str, preferred: int = 8765) -> int:
    """Return a usable TCP port: ``preferred`` if free, else an OS-chosen one."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return probe.getsockname()[1]


def run(args: argparse.Namespace) -> int:
    """Entry point for `partwright sketch`.

    Serves the self-contained `web/sketch.html` drawing tool on a local
    `http.server`, opens it in the browser, and keeps running until
    interrupted (Ctrl-C). Drawings save into `args.dest`.

    Returns an integer exit code (0 on success).
    """
    dest = Path(args.dest).expanduser().resolve()
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"partwright sketch: cannot use destination {dest}: {exc}")
        return 1

    if not _SKETCH_HTML.is_file():
        print(f"partwright sketch: drawing page not found at {_SKETCH_HTML}")
        print("  the web/sketch.html asset is missing from the install.")
        return 1

    # Headless / unattended path: the default mode below blocks in
    # serve_forever() until Ctrl-C, so an agent that runs `partwright sketch`
    # hangs its session. --no-serve resolves the dest and the self-contained
    # page, prints them, and returns immediately without serving or opening a
    # browser. The page works opened directly via file://.
    if getattr(args, "no_serve", False):
        print("partwright sketch — headless (--no-serve)")
        print(f"  drawings folder: {dest}")
        print(f"  sketch page:     {_SKETCH_HTML}")
        print(f"  open directly:   file://{_SKETCH_HTML}")
        return 0

    html_bytes = _SKETCH_HTML.read_bytes()

    host = "127.0.0.1"
    port = _pick_port(host)
    handler = _make_handler(html_bytes, dest)

    try:
        httpd = ThreadingHTTPServer((host, port), handler)
    except OSError as exc:
        print(f"partwright sketch: could not start the local server: {exc}")
        return 1

    url = f"http://{host}:{port}/"
    print("partwright sketch — SVG click-to-draw tool")
    print(f"  serving at:  {url}")
    print(f"  saving into: {dest}")
    print("  press Ctrl-C to stop.")

    # Open the browser shortly after the server starts accepting connections.
    def _open_browser() -> None:
        time.sleep(0.4)
        with contextlib.suppress(Exception):
            webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\npartwright sketch: stopping.")
    finally:
        httpd.shutdown()
        httpd.server_close()
    return 0
