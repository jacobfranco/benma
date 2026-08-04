# ruff: noqa: E501
"""Local, tokenized browser workbench for two-stage human annotation."""

from __future__ import annotations

import hashlib
import json
import secrets
import zipfile
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from benchmark.annotations import commit_blind, commit_revealed, verify_blind
from benchmark.models import (
    BlindAnnotationCommit,
    BlindListenerResponse,
    CorpusManifest,
    RaterProfile,
    RevealedAnnotationCommit,
    RevealedTargetResponse,
    SpeakerCategory,
)
from benchmark.storage import load_model, write_model


@dataclass(frozen=True, slots=True)
class PendingItem:
    sample_id: str
    listener_id: str
    randomized_order: int


class AnnotationWorkbench:
    def __init__(self, manifest: CorpusManifest, annotations_dir: Path, *, seed: str) -> None:
        self.manifest = manifest
        self.annotations_dir = annotations_dir
        self.seed = seed
        self._items: dict[str, PendingItem] = {}
        self._reveals: dict[str, str] = {}

    def _ordered_samples(self, listener_id: str):  # type: ignore[no-untyped-def]
        samples = [
            sample
            for sample in self.manifest.samples
            if sample.audio is not None
            and sample.speaker_category != SpeakerCategory.SYNTHETIC_REFERENCE
        ]
        return sorted(
            samples,
            key=lambda sample: hashlib.sha256(
                f"{self.seed}:{listener_id}:{sample.sample_id}".encode()
            ).hexdigest(),
        )

    def _completed_sample_ids(self, listener_id: str) -> set[str]:
        completed: set[str] = set()
        for path in (self.annotations_dir / "blind").glob("*.json"):
            commit = load_model(path, BlindAnnotationCommit)
            if commit.listener_id == listener_id:
                completed.add(commit.sample_id)
        return completed

    def next_blind_item(self, listener_id: str) -> dict[str, Any] | None:
        completed = self._completed_sample_ids(listener_id)
        ordered = self._ordered_samples(listener_id)
        for order, sample in enumerate(ordered):
            if sample.sample_id in completed:
                continue
            token = secrets.token_urlsafe(24)
            self._items[token] = PendingItem(sample.sample_id, listener_id, order)
            return {
                "item_token": token,
                "audio_url": f"/audio/{token}",
                "randomized_order": order,
                "completed": len(completed),
                "total": len(ordered),
                "stage": "blind",
                "blindness_notice": "Target, intended error, and provider output are hidden.",
            }
        return None

    def audio_path(self, token: str, listener_id: str) -> Path:
        item = self._items.get(token)
        if item is None or item.listener_id != listener_id:
            raise PermissionError("unknown or expired blind item")
        sample = next(
            sample for sample in self.manifest.samples if sample.sample_id == item.sample_id
        )
        if sample.audio is None:
            raise FileNotFoundError("sample audio is unavailable")
        return sample.audio.asset_path

    def commit_blind_stage(
        self,
        token: str,
        *,
        listener_id: str,
        profile: RaterProfile,
        response: BlindListenerResponse,
    ) -> dict[str, Any]:
        item = self._items.get(token)
        if item is None or item.listener_id != listener_id:
            raise PermissionError("unknown or expired blind item")
        annotation_id = hashlib.sha256(
            f"{self.manifest.corpus_version}:{item.sample_id}:{listener_id}".encode()
        ).hexdigest()[:24]
        blind_path = self.annotations_dir / "blind" / f"{annotation_id}.json"
        commit_blind(
            blind_path,
            annotation_id=annotation_id,
            sample_id=item.sample_id,
            listener_id=listener_id,
            randomized_order=item.randomized_order,
            response=response,
            rater_profile=profile,
        )
        del self._items[token]
        reveal_token = secrets.token_urlsafe(24)
        self._reveals[reveal_token] = annotation_id
        sample = next(
            sample for sample in self.manifest.samples if sample.sample_id == item.sample_id
        )
        return {
            "stage": "revealed",
            "reveal_token": reveal_token,
            "target": sample.intended_text,
            "pinyin": sample.intended_pinyin,
            "lexical_tones": sample.lexical_tones,
            "expected_surface_tones": sample.expected_surface_tones,
            "blind_commit_sha256": load_model(blind_path, BlindAnnotationCommit).commit_sha256,
        }

    def commit_revealed_stage(
        self,
        reveal_token: str,
        *,
        listener_id: str,
        response: RevealedTargetResponse,
    ) -> None:
        annotation_id = self._reveals.get(reveal_token)
        if annotation_id is None:
            raise PermissionError("unknown or expired reveal token")
        blind_path = self.annotations_dir / "blind" / f"{annotation_id}.json"
        blind = load_model(blind_path, BlindAnnotationCommit)
        if blind.listener_id != listener_id:
            raise PermissionError("reveal token belongs to another listener")
        sample = next(
            sample for sample in self.manifest.samples if sample.sample_id == blind.sample_id
        )
        if any(index >= len(sample.intended_pinyin) for index in response.affected_syllable_indices):
            raise ValueError("affected syllable index is outside the target")
        commit_revealed(
            blind_path,
            self.annotations_dir / "revealed" / f"{annotation_id}.json",
            response=response,
        )
        del self._reveals[reveal_token]

    def export_bundle(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        blind_paths = sorted((self.annotations_dir / "blind").glob("*.json"))
        revealed_paths = sorted((self.annotations_dir / "revealed").glob("*.json"))
        index = {
            "format": "benma-annotation-bundle-v1",
            "corpus_id": self.manifest.corpus_id,
            "corpus_version": self.manifest.corpus_version,
            "blind_commits": [path.name for path in blind_paths],
            "revealed_commits": [path.name for path in revealed_paths],
            "contains_audio": False,
        }
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("index.json", json.dumps(index, ensure_ascii=False, indent=2))
            for path in [*blind_paths, *revealed_paths]:
                bundle.write(path, f"{path.parent.name}/{path.name}")

    def import_bundle(self, source: Path) -> tuple[int, int]:
        with zipfile.ZipFile(source) as bundle:
            index = json.loads(bundle.read("index.json"))
            if index.get("format") != "benma-annotation-bundle-v1":
                raise ValueError("unsupported annotation bundle format")
            if index.get("corpus_id") != self.manifest.corpus_id:
                raise ValueError("annotation bundle belongs to another corpus")
            blind: dict[str, BlindAnnotationCommit] = {}
            revealed: dict[str, RevealedAnnotationCommit] = {}
            for name in index.get("blind_commits", []):
                blind_commit = BlindAnnotationCommit.model_validate_json(
                    bundle.read(f"blind/{Path(name).name}")
                )
                if not verify_blind(blind_commit):
                    raise ValueError(f"blind commit hash is invalid: {name}")
                blind[Path(name).name] = blind_commit
            for name in index.get("revealed_commits", []):
                revealed_commit = RevealedAnnotationCommit.model_validate_json(
                    bundle.read(f"revealed/{Path(name).name}")
                )
                matching_blind = blind.get(Path(name).name)
                if (
                    matching_blind is None
                    or revealed_commit.blind_commit_sha256 != matching_blind.commit_sha256
                ):
                    raise ValueError(f"revealed commit does not match blind commit: {name}")
                revealed[Path(name).name] = revealed_commit
        for kind, items in (("blind", blind), ("revealed", revealed)):
            for name in items:
                destination = self.annotations_dir / kind / name
                if destination.exists():
                    raise FileExistsError(f"annotation import is create-only: {destination}")
        for name, blind_commit in blind.items():
            write_model(self.annotations_dir / "blind" / name, blind_commit)
        for name, revealed_commit in revealed.items():
            write_model(self.annotations_dir / "revealed" / name, revealed_commit)
        return len(blind), len(revealed)


WORKBENCH_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Benma annotation workbench</title><style>
body{font:16px system-ui;max-width:760px;margin:2rem auto;padding:0 1rem;background:#f6f5f1;color:#17202a}
fieldset{border:1px solid #bbb;border-radius:10px;margin:1rem 0;padding:1rem}label{display:block;margin:.7rem 0}
input[type=text],textarea,select{box-sizing:border-box;width:100%;padding:.6rem}button{padding:.7rem 1rem;margin:.4rem .4rem .4rem 0}
.hidden{display:none}.target{font-size:2rem}small{color:#52606d}</style></head><body>
<h1>Mandarin listener annotation</h1><p id="status">Stage A is audio-only. Do not infer a target from file names or session notes.</p>
<fieldset id="profile"><legend>Rater profile</legend><label>Pseudonym <input id="listener" type="text"></label>
<label><input id="native" type="checkbox"> I self-report as a native Mandarin listener</label>
<label>Role <select id="role"><option>ordinary_native_listener</option><option>linguistically_trained_listener</option></select></label>
<label>Region/accent note (optional)<input id="region" type="text"></label><button id="begin">Begin / resume</button></fieldset>
<fieldset id="blind" class="hidden"><legend>Stage A — blind listening</legend><audio id="audio" controls></audio>
<label>What did you hear?<textarea id="heard"></textarea></label><label>Perceived pinyin, space separated<input id="heardPinyin"></label>
<label><input id="understood" type="checkbox"> Understood on first pass</label><label><input id="repeat" type="checkbox"> Would request repetition</label>
<label>Confidence <input id="confidence" type="range" min="0" max="1" step=".05" value=".5"><output id="confidenceOut">0.5</output></label>
<label>Notes<textarea id="blindNotes"></textarea></label><button id="commitBlind">Commit blind response and reveal target</button></fieldset>
<fieldset id="revealed" class="hidden"><legend>Stage B — target revealed</legend><div id="target" class="target"></div><div id="pinyin"></div>
<label><input id="tone" type="checkbox"> Tone problem</label><label>Affected syllable indices, 0-based<input id="indices"></label>
<label><input id="initial" type="checkbox"> Initial problem</label><label><input id="final" type="checkbox"> Final problem</label>
<label><input id="prosody" type="checkbox"> Rhythm/prosody issue</label><label><input id="still" type="checkbox"> Still understandable</label>
<label>Technical severity<select id="severity"><option>none</option><option>minor</option><option>moderate</option><option>severe</option></select></label>
<label>Semantic severity<select id="semantic"><option value="">not supplied</option><option>technical_only</option><option>noticeable_but_understood</option><option>confusing</option><option>requires_repetition</option><option>wrong_word_perceived</option></select></label>
<label>Perceived tones, space separated<input id="tones"></label><label><input id="invalid" type="checkbox"> Invalid/unusable sample</label>
<label>Notes<textarea id="revealNotes"></textarea></label><button id="commitReveal">Commit Stage B</button></fieldset>
<script>
const q=new URLSearchParams(location.search), access=q.get('access')||'', $=id=>document.getElementById(id);
let item=null,reveal=null; const draftKey=()=>`benma-annotation-${$('listener').value}`;
function saveDraft(){const values={};document.querySelectorAll('input,textarea,select').forEach(e=>values[e.id]=e.type==='checkbox'?e.checked:e.value);localStorage.setItem(draftKey(),JSON.stringify(values));}
function restore(){try{const v=JSON.parse(localStorage.getItem(draftKey())||'{}');Object.entries(v).forEach(([id,x])=>{const e=$(id);if(e)e.type==='checkbox'?e.checked=x:e.value=x;});}catch{}}
document.addEventListener('input',saveDraft);$('confidence').oninput=()=>{$('confidenceOut').value=$('confidence').value};
async function request(path,options={}){const response=await fetch(path,{...options,headers:{'content-type':'application/json',...(options.headers||{})}});const body=await response.json();if(!response.ok)throw Error(body.error||response.statusText);return body;}
$('begin').onclick=async()=>{restore();const listener=$('listener').value.trim();if(!listener)return alert('Choose a pseudonym');item=await request(`/api/next?access=${encodeURIComponent(access)}&listener_id=${encodeURIComponent(listener)}`);if(!item){$('status').textContent='All available samples are complete.';return}$('profile').classList.add('hidden');$('blind').classList.remove('hidden');$('audio').src=`${item.audio_url}?access=${encodeURIComponent(access)}&listener_id=${encodeURIComponent(listener)}`;$('status').textContent=`Blind item ${item.completed+1} of ${item.total}`;};
$('commitBlind').onclick=async()=>{try{reveal=await request('/api/blind',{method:'POST',body:JSON.stringify({access,item_token:item.item_token,listener_id:$('listener').value,rater_profile:{rater_id:$('listener').value,native_mandarin_self_report:$('native').checked,role:$('role').value,region_or_accent_note:$('region').value||null},response:{perceived_text:$('heard').value,perceived_pinyin:$('heardPinyin').value.trim().split(/\s+/).filter(Boolean),understood_first_pass:$('understood').checked,would_request_repetition:$('repeat').checked,confidence:Number($('confidence').value),notes:$('blindNotes').value||null}})});$('blind').classList.add('hidden');$('revealed').classList.remove('hidden');$('target').textContent=reveal.target||'[control has no target]';$('pinyin').textContent=(reveal.pinyin||[]).join(' ');$('status').textContent='Blind response is immutable. Complete target-aware review.';}catch(e){alert(e.message)}};
$('commitReveal').onclick=async()=>{try{await request('/api/revealed',{method:'POST',body:JSON.stringify({access,reveal_token:reveal.reveal_token,listener_id:$('listener').value,response:{tone_problem:$('tone').checked,affected_syllable_indices:$('indices').value.trim().split(/\s+/).filter(Boolean).map(Number),initial_problem:$('initial').checked,final_problem:$('final').checked,rhythm_or_prosody_issue:$('prosody').checked,still_understandable:$('still').checked,severity:$('severity').value,semantic_severity:$('semantic').value||null,perceived_produced_tones:$('tones').value.trim().split(/\s+/).filter(Boolean),invalid_sample:$('invalid').checked,notes:$('revealNotes').value||null}})});localStorage.removeItem(draftKey());location.reload();}catch(e){alert(e.message)}};
</script></body></html>"""


class WorkbenchServer(ThreadingHTTPServer):
    workbench: AnnotationWorkbench
    access_token: str


class WorkbenchHandler(BaseHTTPRequestHandler):
    server: WorkbenchServer

    def _json(self, status: HTTPStatus, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self, value: str | None) -> bool:
        return value is not None and secrets.compare_digest(value, self.server.access_token)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        access = query.get("access", [None])[0]
        if parsed.path == "/":
            body = WORKBENCH_HTML.encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if not self._authorized(access):
            self._json(HTTPStatus.FORBIDDEN, {"error": "invalid access token"})
            return
        listener_id = query.get("listener_id", [""])[0]
        try:
            if parsed.path == "/api/next":
                self._json(
                    HTTPStatus.OK,
                    self.server.workbench.next_blind_item(listener_id),
                )
                return
            if parsed.path.startswith("/audio/"):
                path = self.server.workbench.audio_path(
                    parsed.path.removeprefix("/audio/"), listener_id
                )
                body = path.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("content-type", "audio/wav")
                self.send_header("content-length", str(len(body)))
                self.send_header("cache-control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
        except (FileNotFoundError, PermissionError, StopIteration) as exc:
            self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        try:
            body = self._body()
            if not self._authorized(str(body.get("access", ""))):
                self._json(HTTPStatus.FORBIDDEN, {"error": "invalid access token"})
                return
            if self.path == "/api/blind":
                result = self.server.workbench.commit_blind_stage(
                    str(body["item_token"]),
                    listener_id=str(body["listener_id"]),
                    profile=RaterProfile.model_validate(body["rater_profile"]),
                    response=BlindListenerResponse.model_validate(body["response"]),
                )
                self._json(HTTPStatus.CREATED, result)
                return
            if self.path == "/api/revealed":
                self.server.workbench.commit_revealed_stage(
                    str(body["reveal_token"]),
                    listener_id=str(body["listener_id"]),
                    response=RevealedTargetResponse.model_validate(body["response"]),
                )
                self._json(HTTPStatus.CREATED, {"committed": True})
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        except (FileExistsError, KeyError, PermissionError, ValueError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def serve_workbench(
    workbench: AnnotationWorkbench, *, bind: str, port: int, access_token: str
) -> None:
    server = WorkbenchServer((bind, port), WorkbenchHandler)
    server.workbench = workbench
    server.access_token = access_token
    print(f"annotation workbench: http://{bind}:{server.server_port}/?access={access_token}")
    server.serve_forever()
