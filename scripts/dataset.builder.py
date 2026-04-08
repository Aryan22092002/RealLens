from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw"
META_FILE = ROOT / "data" / "metadata.jsonl"
TIMEOUT = 20

QUERIES = {
    "genuine": [
        "authentic nike shoes",
        "original samsung phone",
        "genuine apple watch",
        "authentic cosmetics product",
    ],
    "fake": [
        "counterfeit shoes",
        "fake watch",
        "replica bag",
        "counterfeit product",
    ],
}


def slugify(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in text).strip("_")


def get_json(url: str, params: dict) -> dict:
    full_url = f"{url}?{urlencode(params)}"
    req = Request(full_url, headers={"User-Agent": "AuthentiLensDatasetBuilder/1.0"})
    with urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_openverse(query: str, limit: int):
    payload = get_json(
        "https://api.openverse.org/v1/images/",
        {"q": query, "page_size": min(20, limit)},
    )
    for item in payload.get("results", [])[:limit]:
        yield {
            "url": item.get("url"),
            "source": "openverse",
            "title": item.get("title", ""),
            "license": item.get("license", "unknown"),
            "creator": item.get("creator", "unknown"),
        }


def iter_wikimedia(query: str, limit: int):
    payload = get_json(
        "https://commons.wikimedia.org/w/api.php",
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": min(20, limit),
            "prop": "imageinfo",
            "iiprop": "url|user|extmetadata",
        },
    )

    pages = (payload.get("query", {}).get("pages", {}) or {}).values()
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        ext = info.get("extmetadata") or {}
        yield {
            "url": info.get("url"),
            "source": "wikimedia",
            "title": page.get("title", ""),
            "license": ext.get("LicenseShortName", {}).get("value", "unknown"),
            "creator": info.get("user", "unknown"),
        }


def download_image(url: str, destination: Path) -> bool:
    if not url:
        return False
    req = Request(url, headers={"User-Agent": "AuthentiLensDatasetBuilder/1.0"})
    try:
        with urlopen(req, timeout=TIMEOUT) as response:
            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type.lower():
                return False
            destination.write_bytes(response.read())
            return True
    except (HTTPError, URLError, TimeoutError, OSError):
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-query", type=int, default=8)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    META_FILE.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with META_FILE.open("w", encoding="utf-8") as meta:
        for label, queries in QUERIES.items():
            class_dir = OUT_DIR / label
            class_dir.mkdir(parents=True, exist_ok=True)

            for query in queries:
                for provider in (iter_openverse, iter_wikimedia):
                    try:
                        items = list(provider(query, args.per_query))
                    except Exception as exc:
                        print(f"Skipping {provider.__name__} for '{query}': {exc}")
                        continue

                    for item in items:
                        url = item.get("url")
                        if not url:
                            continue

                        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
                        filename = f"{slugify(query)}_{provider.__name__}_{digest}.jpg"
                        path = class_dir / filename

                        if path.exists() or not download_image(url, path):
                            continue

                        record = {
                            "label": label,
                            "query": query,
                            "filename": os.fspath(path.relative_to(ROOT)),
                            **item,
                        }
                        meta.write(json.dumps(record, ensure_ascii=False) + "\n")
                        total += 1

    print(f"Downloaded {total} images")
    print(f"Dataset path: {OUT_DIR}")
    print(f"Metadata: {META_FILE}")


if __name__ == "__main__":
    main()