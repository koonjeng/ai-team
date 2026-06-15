"""
[backend] Home Office — แดชบอร์ดดูภาพรวมทีม AI (stdlib only)
- GET /              -> หน้าแดชบอร์ด (frontend)
- GET /api/state     -> สถานะ agent + ฟีดกิจกรรม (อ่านจาก state.json)
- GET /api/hello?name= -> demo เดิม
"""
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).parent
INDEX_HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type):
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(200, INDEX_HTML, "text/html")
        elif parsed.path == "/api/state":
            # อ่านสดทุกครั้ง เพื่อให้แก้ state.json แล้วเห็นผลทันทีโดยไม่ต้องรีสตาร์ท
            data = (ROOT / "state.json").read_text(encoding="utf-8")
            self._send(200, data, "application/json")
        elif parsed.path == "/api/hello":
            name = (parse_qs(parsed.query).get("name", [""])[0]).strip() or "เพื่อน"
            self._send(200, json.dumps({"message": f"สวัสดี {name}"}, ensure_ascii=False), "application/json")
        else:
            self._send(404, json.dumps({"error": "not found"}, ensure_ascii=False), "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = 8000
    print(f"running on http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
