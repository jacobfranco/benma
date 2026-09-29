"""Bounded public metadata/audio acquisition for the pronunciation V2 data gate.

No production imports, model dependencies, credentials, or training. See acquisition.md.
"""

from __future__ import annotations

import argparse
import email.utils
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "BenmaPronunciationResearch/0.1 (bounded public corpus feasibility audit)"
CATEGORIES = [
    "Chinese pronunciation",
    "Mandarin pronunciation",
    "Lingua Libre pronunciation-cmn",
    "Lingua Libre pronunciation-zho",
    "Audio files from Shtooka Project (Mandarin)",
    "Tones of Standard Chinese",
]


def retry_seconds(value, default=60):
    """Honor numeric or HTTP-date Retry-After without capping the server delay."""
    if value and value.isdigit():
        return max(default, int(value))
    if value:
        try:
            return max(
                default, int(email.utils.parsedate_to_datetime(value).timestamp() - time.time()) + 1
            )
        except (TypeError, ValueError, OverflowError):
            pass
    return default


def pause(seconds):
    while seconds > 0:
        interval = min(30, seconds)
        time.sleep(interval)
        seconds -= interval


class Client:
    def __init__(self, cache: Path, offline: bool = False):
        self.cache = cache
        self.cache.mkdir(parents=True, exist_ok=True)
        self.offline = offline

    def get(self, url: str) -> bytes:
        path = self.cache / (hashlib.sha256(url.encode()).hexdigest() + ".json")
        if path.exists():
            return path.read_bytes()
        if self.offline:
            raise RuntimeError(f"Uncached URL in offline mode: {url}")
        for attempt in range(3):
            time.sleep(0.35)
            try:
                request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = response.read(16 * 1024 * 1024 + 1)
                if len(data) > 16 * 1024 * 1024:
                    raise ValueError("Metadata response exceeds 16 MiB")
                # Cache only successful JSON, not error/challenge HTML.
                parsed = json.loads(data)
                if "error" in parsed:
                    raise ValueError(parsed["error"])
                path.write_bytes(data)
                path.with_suffix(".url").write_text(url + "\n")
                return data
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 503) or attempt == 2:
                    raise
                pause(retry_seconds(exc.headers.get("Retry-After")))
        raise RuntimeError("Retries exhausted")

    def query(self, **params):
        params = {"action": "query", "format": "json", "maxlag": 5, **params}
        url = API + "?" + urllib.parse.urlencode(sorted(params.items()))
        return json.loads(self.get(url))


def inventory(client: Client, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    memberships = {}
    categories = {}
    for category in CATEGORIES:
        title = "Category:" + category
        info = client.query(prop="categoryinfo", titles=title)
        categories[category] = info
        continuation = {}
        count = 0
        while True:
            result = client.query(
                list="categorymembers", cmtitle=title, cmtype="file", cmlimit=500, **continuation
            )
            for item in result["query"]["categorymembers"]:
                memberships.setdefault(
                    str(item["pageid"]), {"title": item["title"], "categories": []}
                )["categories"].append(category)
                count += 1
            if len(memberships) > 20000:
                raise ValueError("Metadata inventory exceeds 20,000-file bound")
            if "continue" not in result:
                break
            continuation = result["continue"]
        print(f"{category}: {count} direct file members", flush=True)
    (output / "categories.json").write_text(json.dumps(categories, indent=2) + "\n")
    ids = sorted(memberships, key=int)
    pages = []
    for start in range(0, len(ids), 50):
        result = client.query(
            prop="imageinfo",
            pageids="|".join(ids[start : start + 50]),
            iiprop="url|user|size|sha1|extmetadata",
            iilimit=1,
        )
        for page in result["query"]["pages"].values():
            page["inventory_categories"] = memberships[str(page["pageid"])]["categories"]
            pages.append(page)
        if start % 500 == 0:
            print(f"Inspected metadata: {min(start + 50, len(ids))}/{len(ids)}", flush=True)
    pages.sort(key=lambda p: p["pageid"])
    with (output / "commons-metadata.jsonl").open("w") as handle:
        for page in pages:
            handle.write(json.dumps(page, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Unique file pages: {len(pages)}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inventory"])
    parser.add_argument("--cache", type=Path, default=Path("/tmp/benma-pronunciation-v2-pilot"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    inventory(Client(args.cache / "api", args.offline), args.cache)


if __name__ == "__main__":
    main()
