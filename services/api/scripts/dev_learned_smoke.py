"""Two normal API attempts; live ASR/Azure charges apply. No research comparison.

Run against an explicitly enabled dev server. Writes only a new output file;
source recordings are read-only. Microphone stop and render timing require the app.
"""

import argparse
import json
import time
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("audio", type=Path, nargs=2)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to replace existing smoke evidence")
    records = []
    with httpx.Client(base_url=args.url, timeout=120) as client:
        auth = client.post("/v1/dev/auth", json={"phone_number": "+12025550123"})
        auth.raise_for_status()
        client.headers["Authorization"] = "Bearer " + auth.json()["token"]
        target = client.post(
            "/v1/pronunciation-targets", json={"text": "我想买这个", "target_source": "manual"}
        )
        target.raise_for_status()
        for path in args.audio:
            stages = {}

            def post(name, route, timings=stages, **kwargs):
                started = time.perf_counter()
                response = client.post(route, **kwargs)
                timings[name] = (time.perf_counter() - started) * 1000
                response.raise_for_status()
                return response.json()

            started = time.perf_counter()
            upload = post(
                "upload_http_ms",
                "/v1/utterances",
                files={"file": ("attempt.wav", path.read_bytes(), "audio/wav")},
            )
            perceived = post("asr_http_ms", f"/v1/utterances/{upload['id']}/perceptions", json={})
            assert perceived["status"] == "succeeded", perceived.get("error_code")
            post(
                "attempt_record_http_ms",
                "/v1/pronunciation-attempts",
                json={"utterance_id": upload["id"], "target_id": target.json()["id"]},
            )
            analysis = post(
                "analysis_http_ms",
                f"/v1/perceptions/{perceived['id']}/speech-analysis",
                json={"dev_learned_target_id": target.json()["id"]},
            )
            stages["upload_to_result_ms"] = (time.perf_counter() - started) * 1000
            learned = analysis["data"]["dev_learned_tone"]
            assert learned and any(u["realization"]["status"] == "ok" for u in learned["units"]), (
                "No learned realization"
            )
            assert learned["runtime"]["load_count"] == 1
            records.append({"source": str(path), "stages_ms": stages, "analysis": analysis})
            print(
                json.dumps(
                    {
                        "stages_ms": stages,
                        "runtime": learned["runtime"],
                        "backend_ms": learned["timings_ms"],
                    }
                ),
                flush=True,
            )
    assert records[1]["analysis"]["data"]["dev_learned_tone"]["runtime"]["cold_start"] is False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(
            {
                "kind": "normal_api_saved_audio_smoke_not_new_physical_recording",
                "attempts": records,
            },
            stream,
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    main()
