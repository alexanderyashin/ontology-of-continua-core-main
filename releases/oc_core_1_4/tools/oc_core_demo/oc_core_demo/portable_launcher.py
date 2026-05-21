from __future__ import annotations

import argparse
import ctypes
import json
import os
import socket
import sys
import time
import urllib.request
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import Popen
from typing import Any
from urllib.parse import parse_qs, urlparse

try:
    from oc_core_demo import v003_engine
except Exception:  # pragma: no cover - streamlit fallback bundles can still start without V010 API.
    v003_engine = None


APP_TITLE = "OC Core 1.4 Demonstrator V010 Ideal RC"
HOST = "127.0.0.1"


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _base_dir() -> Path:
    if _is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


def _app_path() -> Path:
    candidates = [
        _base_dir() / "oc_core_demo" / "app.py",
        Path(__file__).resolve().parent / "app.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("The demonstrator app file is missing from the portable bundle.")


def _web_dist_path() -> Path | None:
    candidates = [
        _base_dir() / "web_dist",
        _base_dir() / "web" / "dist",
        Path(__file__).resolve().parents[1] / "web" / "dist",
    ]
    for candidate in candidates:
        if (candidate / "index.html").exists():
            return candidate
    return None


def _find_port(preferred: int | None = None) -> int:
    if preferred:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((HOST, preferred))
                return preferred
            except OSError:
                pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return int(sock.getsockname()[1])


def _url_ok(url: str, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def _child_command(port: int, status_json: str | None = None) -> list[str]:
    if _is_frozen():
        command = [str(Path(sys.executable).resolve()), "--serve", "--port", str(port)]
    else:
        command = [sys.executable, str(Path(__file__).resolve()), "--serve", "--port", str(port)]
    if status_json:
        command.extend(["--serve-status-json", status_json])
    return command


def _portable_env() -> dict[str, str]:
    env = dict(os.environ)
    package_root = _base_dir()
    env["PYTHONPATH"] = str(package_root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    return env


def _write_status(path: str | None, payload: dict[str, Any]) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _api_enabled() -> bool:
    return os.environ.get("OC_CORE_DEMO_PUBLIC_ONLY", "").strip().lower() not in {"1", "true", "yes"}


def _parse_query(path: str) -> dict[str, str]:
    query: dict[str, str] = {}
    parsed = urlparse(path)
    for key, values in parse_qs(parsed.query, keep_blank_values=True).items():
        if not values:
            query[key] = ""
        else:
            query[key] = values[0]
    return query


def _make_handler(web_dist: Path) -> type[SimpleHTTPRequestHandler]:
    class OCRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(web_dist), **kwargs)

        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_bytes(self, body: bytes, *, filename: str, content_type: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0:
                return {}
            if length > 512_000:
                raise ValueError("request body too large")
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def _atlas(self) -> dict[str, Any]:
            if v003_engine is None:
                raise RuntimeError("V010 engine unavailable")
            return v003_engine.load_universe(_base_dir())

        def _handle_api_get(self) -> bool:
            if not self.path.startswith("/api/"):
                return False
            if not _api_enabled():
                self._send_json({"status": "FAIL_CLOSED", "message": "private API disabled for public-only mode"}, 403)
                return True
            if v003_engine is None:
                self._send_json({"status": "FAIL_CLOSED", "message": "V010 engine unavailable"}, 500)
                return True
            try:
                parsed = urlparse(self.path)
                atlas = self._atlas()
                edition = str(atlas.get("edition", "unknown"))
                query = _parse_query(self.path)
                if parsed.path == "/api/atlas":
                    self._send_json(v003_engine.envelope("atlas", edition, atlas))
                    return True
                if parsed.path == "/api/export-bundle":
                    data_dir = v003_engine.find_data_dir(_base_dir())
                    self._send_bytes(v003_engine.export_bundle(atlas, data_dir), filename="oc_core_v010_evidence_bundle.zip", content_type="application/zip")
                    return True
                if parsed.path == "/api/science-graph":
                    self._send_json(v003_engine.envelope("science-graph", edition, v003_engine.science_graph(atlas)))
                    return True
                if parsed.path == "/api/surface-graph":
                    self._send_json(v003_engine.envelope("surface-graph", edition, v003_engine.surface_graph(atlas)))
                    return True
                if parsed.path == "/api/m-space":
                    rows = v003_engine.resource_rows(atlas, "m_spaces", fallback_file="m_spaces.json", fallback_key="m_spaces")
                    m_space_id = query.get("m_space_id") or query.get("id", "")
                    if m_space_id:
                        row = v003_engine.find_by_id(rows, m_space_id, id_fields=("m_space_id", "id"))
                        if row is None:
                            self._send_json(
                                v003_engine.envelope(
                                    "m-space",
                                    edition,
                                    {"status": "FAIL", "message": f"unknown m_space_id: {m_space_id}"},
                                    status="FAIL_CLOSED",
                                ),
                                404,
                            )
                            return True
                        self._send_json(v003_engine.envelope("m-space", edition, {"m_space_id": m_space_id, "m_space": row}))
                        return True
                    self._send_json(v003_engine.envelope("m-space", edition, {"m_spaces": rows, "count": len(rows)}))
                    return True
                if parsed.path == "/api/system-templates":
                    rows = v003_engine.resource_rows(atlas, "system_templates", fallback_file="system_templates.json", fallback_key="system_templates")
                    template_id = query.get("template_id") or query.get("id", "")
                    if template_id:
                        row = v003_engine.find_by_id(rows, template_id, id_fields=("template_id", "system_id", "id"))
                        if row is None:
                            self._send_json(
                                v003_engine.envelope(
                                    "system-template",
                                    edition,
                                    {"status": "FAIL", "message": f"unknown template_id: {template_id}"},
                                    status="FAIL_CLOSED",
                                ),
                                404,
                            )
                            return True
                        self._send_json(v003_engine.envelope("system-template", edition, {"template_id": template_id, "template": row}))
                        return True
                    self._send_json(v003_engine.envelope("system-template-list", edition, {"templates": rows, "count": len(rows)}))
                    return True
                if parsed.path == "/api/didactic-route":
                    rows = v003_engine.resource_rows(atlas, "didactic_routes", fallback_file="didactic_routes.json", fallback_key="didactic_routes")
                    if not rows:
                        rows = v003_engine.resource_rows(atlas, "journeys", fallback_file="didactic_routes.json", fallback_key="journeys")
                    route_id = query.get("route_id") or query.get("id", "")
                    if route_id:
                        row = v003_engine.find_by_id(rows, route_id, id_fields=("route_id", "name", "id"))
                        if row is None:
                            self._send_json(
                                v003_engine.envelope(
                                    "didactic-route",
                                    edition,
                                    {"status": "FAIL", "message": f"unknown route_id: {route_id}"},
                                    status="FAIL_CLOSED",
                                ),
                                404,
                            )
                            return True
                        self._send_json(v003_engine.envelope("didactic-route", edition, {"route_id": route_id, "route": row}))
                        return True
                    self._send_json(v003_engine.envelope("didactic-route-list", edition, {"routes": rows, "count": len(rows)}))
                    return True
                if parsed.path == "/api/reviewer-objections":
                    rows = v003_engine.resource_rows(atlas, "reviewer_objection_routes", fallback_file="reviewer_objection_routes.json", fallback_key="reviewer_objection_routes")
                    route_id = query.get("route_id") or query.get("id", "")
                    if route_id:
                        row = v003_engine.find_by_id(rows, route_id, id_fields=("id", "route_id", "objection_id"))
                        if row is None:
                            self._send_json(v003_engine.envelope("reviewer-objection", edition, {"status": "FAIL", "message": f"unknown route_id: {route_id}"}, status="FAIL_CLOSED"), 404)
                            return True
                        self._send_json(v003_engine.envelope("reviewer-objection", edition, {"route_id": route_id, "route": row}))
                        return True
                    self._send_json(v003_engine.envelope("reviewer-objection-list", edition, {"routes": rows, "count": len(rows)}))
                    return True
                if parsed.path == "/api/model-comparison":
                    rows = v003_engine.resource_rows(atlas, "model_comparison_matrix", fallback_file="model_comparison_matrix.json", fallback_key="model_comparison_matrix")
                    comparison_id = query.get("comparison_id") or query.get("id", "")
                    if comparison_id:
                        row = v003_engine.find_by_id(rows, comparison_id, id_fields=("comparison_id", "id", "model_id"))
                        if row is None:
                            self._send_json(v003_engine.envelope("model-comparison", edition, {"status": "FAIL", "message": f"unknown comparison_id: {comparison_id}"}, status="FAIL_CLOSED"), 404)
                            return True
                        self._send_json(v003_engine.envelope("model-comparison", edition, {"comparison_id": comparison_id, "comparison": row}))
                        return True
                    self._send_json(v003_engine.envelope("model-comparison-list", edition, {"rows": rows, "count": len(rows)}))
                    return True
                if parsed.path == "/api/architect-missions":
                    rows = v003_engine.resource_rows(atlas, "system_architect_missions", fallback_file="system_architect_missions.json", fallback_key="system_architect_missions")
                    mission_id = query.get("mission_id") or query.get("id", "")
                    if mission_id:
                        row = v003_engine.find_by_id(rows, mission_id, id_fields=("id", "mission_id", "template_id"))
                        if row is None:
                            self._send_json(v003_engine.envelope("architect-mission", edition, {"status": "FAIL", "message": f"unknown mission_id: {mission_id}"}, status="FAIL_CLOSED"), 404)
                            return True
                        self._send_json(v003_engine.envelope("architect-mission", edition, {"mission_id": mission_id, "mission": row}))
                        return True
                    self._send_json(v003_engine.envelope("architect-mission-list", edition, {"missions": rows, "count": len(rows)}))
                    return True
                if parsed.path == "/api/trust-ladder":
                    rows = v003_engine.resource_rows(atlas, "trust_ladder", fallback_file="trust_ladder.json", fallback_key="trust_ladder")
                    rung_id = query.get("rung_id") or query.get("id", "")
                    if rung_id:
                        row = v003_engine.find_by_id(rows, rung_id, id_fields=("rung_id", "id"))
                        if row is None:
                            self._send_json(v003_engine.envelope("trust-ladder", edition, {"status": "FAIL", "message": f"unknown rung_id: {rung_id}"}, status="FAIL_CLOSED"), 404)
                            return True
                        self._send_json(v003_engine.envelope("trust-ladder", edition, {"rung_id": rung_id, "rung": row}))
                        return True
                    self._send_json(v003_engine.envelope("trust-ladder-list", edition, {"rungs": rows, "count": len(rows)}))
                    return True
                if parsed.path == "/api/closure-ledger":
                    self._send_json(v003_engine.envelope("closure-ledger", edition, v003_engine.closure_ledger_summary(atlas)))
                    return True
                if parsed.path == "/api/corpus":
                    query = _parse_query(self.path).get("query", "")
                    self._send_json(v003_engine.envelope("corpus", edition, v003_engine.corpus_search(atlas, query)))
                    return True
                if parsed.path == "/api/formula":
                    query = _parse_query(self.path).get("query", "")
                    self._send_json(v003_engine.envelope("formula", edition, v003_engine.formula_search(atlas, query)))
                    return True
                if parsed.path == "/api/node-detail":
                    node_id = _parse_query(self.path).get("node_id", "")
                    self._send_json(v003_engine.envelope("node-detail", edition, v003_engine.node_detail(atlas, node_id)))
                    return True
                if parsed.path == "/api/cerberus":
                    data_dir = v003_engine.find_data_dir(_base_dir())
                    body = v003_engine.cerberus_summary(atlas, data_dir, requested_version=query.get("version", "V010"))
                    status = "PASS" if body.get("status") == "PASS" else "FAIL_CLOSED"
                    self._send_json(v003_engine.envelope("cerberus", edition, body, status=status))
                    return True
                self._send_json(v003_engine.envelope("api", edition, {}, status="FAIL_CLOSED", message=f"unknown endpoint: {parsed.path}"), 404)
                return True
            except Exception as exc:
                self._send_json({"schema_version": "oc-core-demo-api.v010", "status": "FAIL_CLOSED", "message": str(exc)}, 500)
                return True

        def _handle_api_post(self) -> bool:
            if not self.path.startswith("/api/"):
                return False
            if not _api_enabled():
                self._send_json({"status": "FAIL_CLOSED", "message": "private API disabled for public-only mode"}, 403)
                return True
            if v003_engine is None:
                self._send_json({"status": "FAIL_CLOSED", "message": "V010 engine unavailable"}, 500)
                return True
            try:
                parsed = urlparse(self.path)
                body = self._read_body()
                atlas = self._atlas()
                edition = str(atlas.get("edition", "unknown"))
                if parsed.path == "/api/sim/run":
                    simulation_id = str(body.get("simulation_id") or "")
                    result = v003_engine.run_simulation(simulation_id, body.get("params") if isinstance(body.get("params"), dict) else {}, atlas=atlas)
                    self._send_json(v003_engine.envelope("simulation", edition, result))
                    return True
                if parsed.path == "/api/kill":
                    result = v003_engine.kill_cascade(body, atlas)
                    self._send_json(v003_engine.envelope("kill-cascade", edition, result))
                    return True
                if parsed.path == "/api/research-gap":
                    result = v003_engine.make_research_gap(body, atlas)
                    self._send_json(v003_engine.envelope("research-gap", edition, result))
                    return True
                if parsed.path == "/api/predict":
                    result = v003_engine.predict(body, atlas)
                    self._send_json(v003_engine.envelope("predict", edition, result))
                    return True
                if parsed.path == "/api/simulate-system":
                    system_id = str(body.get("system_id") or body.get("template_id") or "")
                    if not system_id:
                        self._send_json(v003_engine.envelope("simulate-system", edition, {"status": "FAIL", "message": "system_id is required"}, status="FAIL_CLOSED"), 400)
                        return True
                    params = dict(body) if isinstance(body, dict) else {}
                    params.setdefault("system_id", system_id)
                    params.setdefault("mode", "selected")
                    params.setdefault("shock", 0.82)
                    templates = v003_engine.resource_rows(atlas, "system_templates", fallback_file="system_templates.json", fallback_key="system_templates")
                    systems = v003_engine.resource_rows(atlas, "system_zoo", fallback_file="system_zoo.json", fallback_key="systems")
                    selected = v003_engine.find_by_id(templates, system_id, id_fields=("template_id", "system_id"))
                    if selected is None:
                        selected = v003_engine.find_by_id(systems, system_id, id_fields=("id", "system_id"))
                    if selected is None:
                        self._send_json(v003_engine.envelope("simulate-system", edition, {"status": "FAIL", "message": f"unknown system/template id: {system_id}"}, status="FAIL_CLOSED"), 404)
                        return True
                    result = v003_engine.kill_cascade(params, atlas)
                    self._send_json(v003_engine.envelope("simulate-system", edition, {"system_id": system_id, "template": selected, "simulation": result}))
                    return True
                self._send_json(v003_engine.envelope("api", edition, {}, status="FAIL_CLOSED", message=f"unknown endpoint: {parsed.path}"), 404)
                return True
            except Exception as exc:
                self._send_json({"schema_version": "oc-core-demo-api.v010", "status": "FAIL_CLOSED", "message": str(exc)}, 500)
                return True

        def do_GET(self) -> None:  # noqa: N802
            if self._handle_api_get():
                return
            super().do_GET()

        def do_POST(self) -> None:  # noqa: N802
            if self._handle_api_post():
                return
            self._send_json({"status": "FAIL_CLOSED", "message": "POST is only supported under /api"}, 405)

    return OCRequestHandler


def _show_error(message: str) -> None:
    if os.name == "nt":
        try:
            ctypes.windll.user32.MessageBoxW(None, message, APP_TITLE, 0x10)
            return
        except Exception:
            pass
    print(f"{APP_TITLE}: {message}", file=sys.stderr)


def _serve(port: int, status_json: str | None = None) -> int:
    web_dist = _web_dist_path()
    if web_dist:
        _write_status(status_json, {"app": APP_TITLE, "status": "STATIC_WEB_SERVE_READY", "web_dist": str(web_dist), "port": port})
        handler = _make_handler(web_dist)
        server = ThreadingHTTPServer((HOST, port), handler)
        try:
            server.serve_forever()
        finally:
            server.server_close()
        return 0

    from streamlit.web import bootstrap

    app_path = _app_path()
    _write_status(status_json, {"app": APP_TITLE, "status": "SERVE_STARTING", "app_path": str(app_path), "port": port})
    flag_options = {
        "server_address": HOST,
        "server_port": port,
        "server_headless": True,
        "browser_gatherUsageStats": False,
        "global_developmentMode": False,
    }
    _write_status(status_json, {"app": APP_TITLE, "status": "SERVE_BOOTSTRAP_READY", "app_path": str(app_path), "port": port})
    bootstrap.load_config_options(flag_options)
    bootstrap.run(str(app_path), False, [], flag_options)
    return 0


def _launch(args: argparse.Namespace) -> int:
    port = _find_port(args.port)
    url = f"http://{HOST}:{port}"
    child_status = str(Path(args.status_json).resolve().with_suffix(".serve.json")) if args.status_json else ""
    proc = Popen(_child_command(port, child_status), cwd=str(Path(sys.executable).resolve().parent if _is_frozen() else Path(__file__).resolve().parent), env=_portable_env())
    ok = False
    deadline = time.time() + float(args.timeout)
    while time.time() < deadline:
        if _url_ok(url):
            ok = True
            break
        if proc.poll() is not None:
            break
        time.sleep(0.35)

    payload = {
        "app": APP_TITLE,
        "status": "PASS" if ok else "FAIL_CLOSED",
        "url": url,
        "pid": proc.pid,
        "smoke": bool(args.smoke),
        "child_status_json": child_status,
    }
    _write_status(args.status_json, payload)

    if not ok:
        try:
            proc.terminate()
        except Exception:
            pass
        _show_error("The demonstrator could not start. Please rebuild the portable bundle and retry.")
        return 2

    if args.smoke:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except Exception:
            proc.kill()
        return 0

    if not args.no_browser:
        webbrowser.open(url)
    try:
        return int(proc.wait())
    except KeyboardInterrupt:
        proc.terminate()
        return 130


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch the OC Core 1.4 scientific demonstrator.")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--status-json", default="")
    parser.add_argument("--serve-status-json", default="")
    args = parser.parse_args(argv)
    try:
        if args.serve:
            return _serve(_find_port(args.port), args.serve_status_json)
        return _launch(args)
    except Exception as exc:
        payload = {"app": APP_TITLE, "status": "FAIL_CLOSED", "message": str(exc), "smoke": bool(args.smoke)}
        _write_status(args.status_json, payload)
        _show_error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

