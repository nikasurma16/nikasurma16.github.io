# -*- coding: utf-8 -*-
"""
Local preview server that never serves a stale page.

    python tools/serve.py [port]

Assets carry a content hash in their URL, so they are safe to cache — but
the HTML that points at them does not, and a cached page keeps asking for
yesterday's video. This sends no-store for documents and leaves the rest
alone.
"""
import functools
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8899


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        path = self.path.split("?")[0]
        if path.endswith("/") or path.endswith(".html") or "." not in path.rsplit("/", 1)[-1]:
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    handler = functools.partial(Handler, directory=ROOT)
    print("preview on http://127.0.0.1:%d  (documents are never cached)" % PORT)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler).serve_forever()
