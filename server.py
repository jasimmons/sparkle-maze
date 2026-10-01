"""Tiny local server for Pip's Sparkle Maze.

The game itself runs entirely in the browser (web/game.html). This server only
serves it, so it needs nothing beyond the Python standard library.

    python3 server.py            # then open http://localhost:8000
    python3 server.py --port 9000
    python3 server.py --build dist   # write a static site (used for GitHub Pages)
    python3 server.py --artifact out.html   # one self-contained file with the levels inlined

The hand-made levels are JSON files in web/levels/, listed in order in
web/levels/index.json. The game fetches them when it starts.
"""
import argparse
import http.server
import json
import re
import shutil
from pathlib import Path

WEB = Path(__file__).parent / "web"
LEVELS = WEB / "levels"

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
</head>
<body>
{body}
</body>
</html>
"""


def full_page():
    # game.html is a page fragment (that's the form the published Artifact uses),
    # so wrap it in a full HTML document.
    return PAGE.format(body=(WEB / "game.html").read_text(encoding="utf-8"))


def load_levels():
    index = json.loads((LEVELS / "index.json").read_text(encoding="utf-8"))
    return [json.loads((LEVELS / f).read_text(encoding="utf-8")) for f in index["levels"]]


def inline_levels(html):
    # The published Artifact is a single file and can't fetch levels/*.json, so put
    # the levels straight into the page where the game looks for them.
    levels = json.dumps(load_levels(), ensure_ascii=False).replace("</", "<\\/")
    new, n = re.subn(r"const INLINE_LEVELS = null;", lambda _: f"const INLINE_LEVELS = {levels};", html)
    if n != 1:
        raise SystemExit("Couldn't find 'const INLINE_LEVELS = null;' in web/game.html")
    return new


def build(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(full_page(), encoding="utf-8")
    shutil.copytree(LEVELS, out / "levels", dirs_exist_ok=True)
    print(f"Wrote {out / 'index.html'} and {out / 'levels'}/")


def build_artifact(out):
    out = Path(out)
    out.write_text(inline_levels((WEB / "game.html").read_text(encoding="utf-8")), encoding="utf-8")
    print(f"Wrote {out} (levels inlined)")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = full_page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def end_headers(self):
        # Always serve fresh level files so edits show up on refresh.
        if self.path.startswith("/levels/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description="Serve Pip's Sparkle Maze")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--build", metavar="DIR", help="write a static site (index.html + levels/) into DIR and exit")
    parser.add_argument("--artifact", metavar="FILE", help="write game.html with the levels inlined into FILE and exit")
    args = parser.parse_args()
    if args.build or args.artifact:
        if args.build:
            build(args.build)
        if args.artifact:
            build_artifact(args.artifact)
        return
    server = http.server.ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Pip's Sparkle Maze is running at http://{args.host}:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
