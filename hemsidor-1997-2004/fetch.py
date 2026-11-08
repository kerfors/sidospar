"""Hämta mina gamla hemsidor ur Internet Archive (Wayback Machine).

Download Kerstin's home pages 1997–2004 from the Wayback Machine.

For each source, all captures are listed with the CDX API. For every archived
URL the latest capture with status 200 is downloaded raw (the "id_" form,
without the Wayback toolbar) to data/<folder>/<path>.

The folder names (netg, viktoria) replace the user directories (~kerfor,
~kerstinf): Jekyll skips names that begin with "~".

data/manifest.json records every capture found, also the ones not downloaded,
so other versions can be fetched later.

Resumable: a file that already exists in data/ is not downloaded again.
Python 3 standard library only. Run from any directory:

    python3 fetch.py
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Source prefix (host without www. and port, then path) -> local folder.
SOURCES = {
    "netg.se/~kerfor/": "netg",
    "viktoria.informatik.gu.se/~kerstinf/": "viktoria",
}
DATA_DIR = Path(__file__).parent / "data"
CDX = "https://web.archive.org/cdx/search/cdx"
WAYBACK = "https://web.archive.org/web"
USER_AGENT = "sidospar-hemsidor/1.0 (personal archive recovery)"
PAUSE_SECONDS = 1.5
RETRY_CODES = (429, 502, 503, 504)


def get(url):
    """GET with a few slow retries: the Wayback Machine often answers 429/503."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as err:
            if err.code not in RETRY_CODES or attempt == 3:
                raise
        except urllib.error.URLError:
            if attempt == 3:
                raise
        wait = 15 * (attempt + 1)
        print(f"    retry in {wait} s")
        time.sleep(wait)


def list_captures(prefix):
    query = urllib.parse.urlencode({
        "url": prefix,
        "matchType": "prefix",
        "output": "json",
        "fl": "timestamp,original,statuscode,mimetype,digest,length",
    })
    rows = json.loads(get(f"{CDX}?{query}"))
    header, body = rows[0], rows[1:]
    return [dict(zip(header, row)) for row in body]


def local_path(url):
    """Local path (folder/path) for a URL under one of the SOURCES, else None.

    Host is lower-cased, www. and port dropped, %-escapes decoded; a directory
    URL becomes index.html. Matching against the prefix ignores case.
    """
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return None
    host = parts.hostname.lower()
    if host.startswith("www."):
        host = host[4:]
    full = host + urllib.parse.unquote(parts.path)
    for prefix, folder in SOURCES.items():
        if full.lower() == prefix.lower().rstrip("/"):
            rest = ""
        elif full.lower().startswith(prefix.lower()):
            rest = full[len(prefix):]
        else:
            continue
        if rest == "" or rest.endswith("/"):
            rest += "index.html"
        relative = Path(folder) / rest
        if ".." in relative.parts:
            raise ValueError(f"Path escapes data folder: {url}")
        return relative
    return None


def main():
    manifest = {"sources": {}}
    for prefix, folder in SOURCES.items():
        print(f"Listing captures under {prefix}")
        captures = list_captures(prefix)
        time.sleep(PAUSE_SECONDS)

        # All 200 captures per local file, newest first. Keyed case-insensitively, since
        # macOS file names are (~Kerfor and ~kerfor would collide).
        # URLs with a query string are skipped: they are Apache directory
        # listings sorted another way (?D=A, ?N=D ...), the same listing as the
        # directory URL itself. They are kept in the manifest as skipped_query.
        candidates = {}
        skipped_query = []
        for capture in captures:
            if capture["statuscode"] != "200":
                continue
            if urllib.parse.urlsplit(capture["original"]).query:
                skipped_query.append(capture["original"])
                continue
            path = local_path(capture["original"])
            if path is None:
                raise ValueError(f"Capture outside {prefix}: {capture['original']}")
            key = str(path).lower()
            candidates.setdefault(key, []).append(dict(capture, path=str(path)))

        print(f"  {len(captures)} captures, {len(candidates)} files with content, "
              f"{len(set(skipped_query))} URLs with query string skipped")
        # The CDX index sometimes lists a 200 capture that the archive then
        # answers 404 for. Then older captures of the same URL are tried; if all
        # fail, the file is listed as missing in the manifest.
        chosen = []
        missing = []
        for key in sorted(candidates):
            versions = sorted(candidates[key], key=lambda c: c["timestamp"], reverse=True)
            target = DATA_DIR / versions[0]["path"]
            for item in versions:
                if target.exists():
                    break
                print(f"  {item['timestamp'][:8]}  {item['path']}")
                try:
                    content = get(f"{WAYBACK}/{item['timestamp']}id_/{item['original']}")
                except urllib.error.HTTPError as err:
                    if err.code != 404:
                        raise
                    print("    404 in the archive, trying an older capture")
                    time.sleep(PAUSE_SECONDS)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                time.sleep(PAUSE_SECONDS)
                break
            if target.exists():
                chosen.append(item)
            else:
                missing.append(versions[0]["path"])

        manifest["sources"][prefix] = {
            "folder": folder,
            "files": chosen,
            "missing": missing,
            "skipped_query": sorted(set(skipped_query)),
            "all_captures": captures,
        }

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    total = sum(len(s["files"]) for s in manifest["sources"].values())
    print(f"Done: {total} files in {DATA_DIR}")


if __name__ == "__main__":
    main()
