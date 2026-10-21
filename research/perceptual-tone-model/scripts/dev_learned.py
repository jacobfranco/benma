"""Explicitly gated, loopback-only learned-tone physical testing. No production imports."""

import argparse
import json
import secrets
import sys
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.common import PACKAGE, read_json, write_json
from perceptual_tone.dev_inference import require_dev, verify_frozen
from perceptual_tone.dev_runtime import DEFAULT_RUNS, DevRuntime

ASSETS = PACKAGE / "scripts"


def handler(runtime, token, capture_source="physical_microphone"):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, data, mime="application/json"):
            body = (
                data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
            )
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def local_request(self):
            host = self.headers.get("Host", "")
            allowed = {
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
            }
            origin = self.headers.get("Origin")
            return host in allowed and (not origin or origin == "http://" + host)

        def do_GET(self):
            if not self.local_request():
                return self.send(403, {"error": "loopback_origin_required"})
            path = urlparse(self.path).path
            if path in ("/", "/dev_learned.js"):
                name = "dev_learned.html" if path == "/" else "dev_learned.js"
                mime = "text/html; charset=utf-8" if path == "/" else "text/javascript"
                return self.send(200, (ASSETS / name).read_bytes(), mime)
            if path == "/config":
                return self.send(
                    200,
                    {
                        "token": token,
                        "asr_requested": runtime.asr,
                        "verification": runtime.recognizer.verification,
                    },
                )
            if path == "/takes":
                reports = sorted(
                    runtime.folder.glob("*/report.json"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                return self.send(
                    200,
                    [
                        {k: read_json(p)[k] for k in ("take_id", "intended_phrase", "source_kind")}
                        for p in reports
                    ],
                )
            parts = path.strip("/").split("/")
            if len(parts) == 3 and parts[0] == "takes":
                try:
                    if uuid.UUID(parts[1]).hex != parts[1]:
                        raise ValueError("bad_take_id")
                    name = parts[2]
                    if (
                        name != "report.json"
                        and name != "canonical.wav"
                        and not (
                            name.startswith("unit-")
                            and name.endswith(".wav")
                            and all(c.isalnum() or c in "-." for c in name)
                        )
                    ):
                        raise ValueError("bad_artifact")
                    target = runtime.folder / parts[1] / name
                    return self.send(
                        200,
                        target.read_bytes(),
                        "audio/wav" if name.endswith(".wav") else "application/json",
                    )
                except (ValueError, OSError):
                    pass
            self.send(404, {"error": "not_found"})

        def do_POST(self):
            if not self.local_request() or self.headers.get("X-Benma-Dev") != token:
                return self.send(403, {"error": "explicit_local_dev_session_required"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 15 * 1024 * 1024:
                    return self.send(413, {"error": "empty_or_oversize_upload"})
                body = self.rfile.read(length)
                if self.path == "/take":
                    phrase = self.headers.get("X-Phrase", "")
                    from urllib.parse import unquote

                    result = runtime.take(
                        body, unquote(phrase) or "我想买这个", source_kind=capture_source
                    )
                    return self.send(200, result)
                if self.path == "/observation":
                    value = json.loads(body)
                    ident = uuid.UUID(value["take_id"]).hex
                    if not (runtime.folder / ident / "report.json").exists():
                        raise ValueError("unknown_take")
                    if value["category"] not in (
                        "plausible correction",
                        "suspicious model behavior",
                        "alignment failure",
                        "insufficient evidence",
                    ):
                        raise ValueError("unknown_category")
                    observation = {
                        "take_id": ident,
                        "category": value["category"],
                        "notes": str(value.get("notes", ""))[:5000],
                        "is_ground_truth": False,
                    }
                    write_json(
                        runtime.folder / ident / f"observation-{uuid.uuid4().hex}.json", observation
                    )
                    return self.send(200, {"saved": True})
                self.send(404, {"error": "not_found"})
            except Exception as error:
                # Full traceback stays in the local terminal, never expose credentials.
                import traceback

                traceback.print_exc()
                self.send(
                    422,
                    {
                        "error": type(error).__name__,
                        "message": "Take could not be processed; inspect local log. "
                        "No correction issued.",
                    },
                )

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable-learned-dev", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument(
        "--asr", action="store_true", help="Use configured live Benma ASR, if available"
    )
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--output", type=Path, default=DEFAULT_RUNS)
    parser.add_argument(
        "--audio", type=Path, help="Analyze one existing recording instead of serving"
    )
    parser.add_argument("--phrase", default="我想买这个")
    parser.add_argument(
        "--capture-source",
        default="physical_microphone",
        choices=("physical_microphone", "automated_browser_replay"),
    )
    args = parser.parse_args()
    require_dev(args.enable_learned_dev)
    if args.verify_only:
        print(json.dumps(verify_frozen(), indent=2))
        return
    runtime = DevRuntime(args.output, enabled=True, asr=args.asr)
    if args.audio:
        result = runtime.take(
            args.audio.read_bytes(), args.phrase, source_kind="saved_recording_replay"
        )
        print(
            json.dumps(
                {"take_id": result["take_id"], "performance": result["performance"]}, indent=2
            )
        )
        return
    server = HTTPServer(
        ("127.0.0.1", args.port), handler(runtime, secrets.token_urlsafe(32), args.capture_source)
    )
    print(f"DEV/RESEARCH ONLY: http://127.0.0.1:{args.port} — Ctrl-C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
