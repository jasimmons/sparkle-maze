"""Tiny local server for Pip's Sparkle Maze.

The game itself runs entirely in the browser (web/game.html). This server only
serves it, so it needs nothing beyond the Python standard library.

    python3 server.py            # then open http://localhost:8000
    python3 server.py --port 9000
    python3 server.py --build dist   # write a static site (used for GitHub Pages)
"""
import argparse
import http.server
from pathlib import Path

WEB = Path(__file__).parent / "web"

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


def build(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(full_page(), encoding="utf-8")
    print(f"Wrote {out / 'index.html'}")


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


def main():
    parser = argparse.ArgumentParser(description="Serve Pip's Sparkle Maze")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--build", metavar="DIR", help="write a static index.html into DIR and exit")
    args = parser.parse_args()
    if args.build:
        build(args.build)
        return
    server = http.server.ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Pip's Sparkle Maze is running at http://{args.host}:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
