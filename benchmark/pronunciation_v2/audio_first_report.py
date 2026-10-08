"""Build a local, offline six-take product mock. No analysis or provider execution."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "services/api/var/audio-first-feedback"
SOURCE = ROOT / "services/api/var/relative-pitch-gesture/saved-analyses.json"
BENCH = ROOT / "benchmark/pronunciation_v2"
REPORT = ROOT / "docs/research/pronunciation-v2/2026-10-08-audio-first-feedback"


def build():
    rows = []
    captures = json.loads(SOURCE.read_text())
    assert [r["id"][:8] for r in captures] == [
        "40357072",
        "8d252264",
        "d47274bc",
        "4b9dbd2b",
        "8faf1a90",
        "a5acd04c",
    ]
    for saved in captures:
        analysis = saved["analyses"][-1]
        data = analysis["result"]
        matches = list((ROOT / "services/api/var/audio").glob(f"*/canonical/{saved['id']}.wav"))
        assert len(matches) == 1, "Canonical recording missing or ambiguous"
        audio = matches[0].read_bytes()
        assert hashlib.sha256(audio).hexdigest() == saved["sha256"]
        with wave.open(str(matches[0])) as wav:
            duration = wav.getnframes() / wav.getframerate()
            assert wav.getframerate() == 16000 and wav.getnchannels() == 1
            assert abs(duration - data["duration_seconds"]) < 1 / 16000
        # This persisted alignment reference is the perceived transcript, not a target.
        text = data["timing_evidence"]["reference_text"]
        assert all(
            text[s["character_start"] : s["character_end"]] == s["characters"]
            for s in data["syllables"]
        )
        rows.append(
            dict(
                id=saved["id"],
                analysis_id=analysis["id"],
                created_at=analysis["created_at"],
                perceived_text=text,
                duration_seconds=duration,
                audio_sha256=saved["sha256"],
                audio_path=str(matches[0].relative_to(ROOT)),
                audio_base64=base64.b64encode(audio).decode(),
                data=data,
            )
        )
    return dict(
        recordings=rows, saved_analysis_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = build()
    (OUT / "viewer-data.json").write_text(json.dumps(evidence, ensure_ascii=False, allow_nan=False))
    payload = json.dumps(evidence, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    html = (BENCH / "audio_first_viewer.html").read_text()
    html = html.replace("/* MODEL */", (BENCH / "audio_first_model.cjs").read_text())
    html = html.replace("/* EVIDENCE */", f"const evidence={payload};")
    (OUT / "viewer.html").write_text(html)
    # Execute the exact browser card model for a small review artifact, not a
    # second implementation of timing, eligibility or gesture presentation.
    review = subprocess.check_output(
        [
            "node",
            "-e",
            """
const fs=require('node:fs'),m=require(process.argv[1]);
const evidence=JSON.parse(fs.readFileSync(0,'utf8'));
const recordings=evidence.recordings.map(r=>{
  const cards=m.cards(r.data);
  return {id:r.id.slice(0,8),perceived_text:r.perceived_text,analysis_id:r.analysis_id,
    audio_sha256:r.audio_sha256,duration:r.duration_seconds,cards,
    detail:{points:r.data.tone_graph.filtered.segments.flat().length,
      segments:r.data.tone_graph.filtered.segments.length,
      baseline_hz:r.data.tone_graph.filtered.baseline_hz},
    padding:[0,40,80].map(ms=>({ms,units_with_neighbor_context:cards.filter((c,i)=>{
      const b=m.playbackBounds(c.start_seconds,c.end_seconds,r.duration_seconds,ms);
      return cards.some((n,j)=>i!==j&&b.start_seconds<n.end_seconds&&n.start_seconds<b.end_seconds);
    }).length}))};
});
process.stdout.write(JSON.stringify({saved_analysis_sha256:evidence.saved_analysis_sha256,recordings},null,2)+'\\n');
""",
            str(BENCH / "audio_first_model.cjs"),
        ],
        input=json.dumps(evidence),
        text=True,
    )
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "replay.json").write_text(review)
    (OUT / "review.json").write_text(review)
    print(
        f"Built {OUT / 'viewer.html'}; "
        "six original canonical files verified; no audio files created."
    )


if __name__ == "__main__":
    main()
