"""Tiny local server for Pip's Sparkle Maze.

The game itself runs entirely in the browser (web/game.html). This server only
serves it, so it needs nothing beyond the Python standard library.

    python3 server.py            # then open http://localhost:8000
    python3 server.py --port 9000
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


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            # game.html is a page fragment (that's the form the published Artifact uses),
            # so wrap it in a full HTML document here.
            body = PAGE.format(body=(WEB / "game.html").read_text(encoding="utf-8")).encode("utf-8")
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
    args = parser.parse_args()
    server = http.server.ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Pip's Sparkle Maze is running at http://{args.host}:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
