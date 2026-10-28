"""IDRIS company website: serves index.html and the waitlist API (separate from the Idris AI solver backend).

Run on Render as a Web Service: start command `python server.py`. Needs a persistent disk mounted at
IDRIS_DATA_DIR (e.g. /var/data) and IDRIS_ADMIN_TOKEN set; see README.md.
"""
import json
import os
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

import waitlist

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", 8000))


class Handler(BaseHTTPRequestHandler):
    server_version = "IdrisWebsite/1.0"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, code, body, ctype="application/json", extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print("[idris-website]", fmt % args)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        u = urlsplit(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path in ("/", "/index.html"):
                with open(os.path.join(HERE, "index.html"), "rb") as fh:
                    return self._send(200, fh.read(), "text/html; charset=utf-8")
            if u.path == "/health":
                return self._send(200, {"service": "idris-website", "status": "ok", "waitlist": waitlist.status()})
            if u.path == "/waitlist/options":
                return self._send(200, {"success": True, **waitlist.options()})
            if u.path == "/waitlist/stats":
                return self._send(200, {"success": True, **waitlist.stats(q.get("token"))})
            if u.path == "/waitlist/export.csv":
                csv_text = waitlist.export_csv(q.get("token"), q.get("include_test") == "1")
                return self._send(200, csv_text.encode("utf-8"), "text/csv; charset=utf-8",
                                  {"Content-Disposition": 'attachment; filename="idris-waitlist.csv"'})
            return self._send(404, {"success": False, "error": "not found"})
        except waitlist.WaitlistError as e:
            return self._send(e.status, {"success": False, "error": str(e)})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ("/waitlist", "/visit", "/waitlist/delete"):
            return self._send(404, {"success": False, "error": "not found"})
        try:
            n = min(int(self.headers.get("Content-Length", 0)), 20000)
            params = json.loads((self.rfile.read(n) if n else b"{}").decode("utf-8") or "{}")
            if not isinstance(params, dict):
                raise ValueError("body must be a JSON object")
        except Exception as e:
            return self._send(400, {"success": False, "error": f"invalid JSON body: {e}"})
        ip = (self.headers.get("X-Forwarded-For") or self.client_address[0]).split(",")[0].strip()
        try:
            if path == "/waitlist":
                return self._send(*waitlist.signup(params, ip))
            if path == "/visit":
                return self._send(*waitlist.visit(params))
            return self._send(200, waitlist.delete(params.get("token"), params.get("email")))
        except waitlist.WaitlistError as e:
            return self._send(e.status, {"success": False, "error": str(e)})
        except Exception:
            traceback.print_exc()
            return self._send(500, {"success": False, "error": "sign-up failed"})


if __name__ == "__main__":
    print(f"IDRIS website on port {PORT}; waitlist storage: {waitlist.status()}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
