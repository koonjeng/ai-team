"""
[backend] Hello server — stdlib only (ไม่ต้องลง dependency)
- GET /              -> หน้าเว็บ (frontend)
- GET /api/hello?name=  -> {"message": "สวัสดี <ชื่อ>"}
"""
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# [frontend] โหลดหน้าเว็บบริษัทจากไฟล์ web/index.html
INDEX_HTML = (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")


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
        elif parsed.path == "/api/hello":
            # [backend] validate: ถ้าไม่ใส่ชื่อ ใช้ "เพื่อน" เป็น default
            name = (parse_qs(parsed.query).get("name", [""])[0]).strip() or "เพื่อน"
            self._send(200, json.dumps({"message": f"สวัสดี {name}"}, ensure_ascii=False), "application/json")
        else:
            self._send(404, json.dumps({"error": "not found"}, ensure_ascii=False), "application/json")

    def log_message(self, *args):
        pass  # ปิด log เริ่มต้นให้เงียบ


if __name__ == "__main__":
    port = 8000
    print(f"running on http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
