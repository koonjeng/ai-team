"""
[backend] Home Office — แดชบอร์ดดูภาพรวมทีม AI (stdlib only)
- GET /              -> หน้าแดชบอร์ด (frontend)
- GET /api/state     -> สถานะ agent + ฟีดกิจกรรม (อ่านจาก state.json)
- GET /api/hello?name= -> demo เดิม
"""
import json
from datetime import datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).parent
STATE = ROOT / "state.json"


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type):
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            # โหลด HTML สดทุกครั้ง แก้หน้าแล้วรีเฟรชเห็นเลย
            self._send(200, (ROOT / "web" / "index.html").read_text(encoding="utf-8"), "text/html")
        elif parsed.path == "/api/state":
            self._send(200, STATE.read_text(encoding="utf-8"), "application/json")
        elif parsed.path == "/api/hello":
            name = (parse_qs(parsed.query).get("name", [""])[0]).strip() or "เพื่อน"
            self._send(200, json.dumps({"message": f"สวัสดี {name}"}, ensure_ascii=False), "application/json")
        else:
            self._send(404, json.dumps({"error": "not found"}, ensure_ascii=False), "application/json")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/api/order", "/api/chat"):
            # รับข้อความจากแชท -> เก็บประวัติแชท + เข้าคิวงาน + ให้เลขาตอบรับทันที
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            text = (body.get("text") or "").strip()
            if not text:
                self._send(400, json.dumps({"error": "empty"}, ensure_ascii=False), "application/json")
                return
            data = json.loads(STATE.read_text(encoding="utf-8"))
            now = datetime.now().strftime("%H:%M")
            msgs = data.setdefault("messages", [])
            msgs.append({"role": "user", "time": now, "text": text})
            msgs.append({"role": "secretary", "time": now,
                         "text": f"รับทราบครับ 👔 กำลังให้ทีมลงมือ \"{text}\" — เดี๋ยวเสร็จจะรายงานในแชทนี้"})
            data["messages"] = msgs[-50:]
            data.setdefault("orders", []).insert(0, {"time": now, "text": text, "done": False})
            data["orders"] = data["orders"][:30]
            data.setdefault("activity", []).insert(0, {"time": now, "who": "🧑 เจ้านาย", "text": "สั่งงาน: " + text})
            data["activity"] = data["activity"][:50]
            for a in data["agents"]:
                if a["id"] == "secretary":
                    a["status"] = "working"
                    a["task"] = "รับโจทย์ใหม่: " + text
                    a["thought"] = "กำลังแตกงานและมอบหมายให้ทีม"
            STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self._send(200, json.dumps({"ok": True}, ensure_ascii=False), "application/json")
        else:
            self._send(404, json.dumps({"error": "not found"}, ensure_ascii=False), "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = 8000
    print(f"running on http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
