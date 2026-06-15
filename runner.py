"""
runner.py — ตัวเชื่อมอัตโนมัติ (bridge)
เฝ้าคิว orders ใน state.json -> เรียก Claude Code (headless) ให้ "เลขา" รับงานและมอบหมายทีมจริง
ระหว่างทำงาน agent จะอัปเดตสถานะผ่าน team.py เอง หน้า dashboard จึงขยับตามสด

ต้องมี Claude Code CLI ก่อน (ลงครั้งเดียว):
  npm install -g @anthropic-ai/claude-code
  claude            # login ครั้งแรก
ตรวจ: claude --version

วิธีรัน:
  python runner.py            # โหมดเฝ้าคิวตลอด (poll ทุก 3 วิ)
  python runner.py --once     # เคลียร์คิวที่ค้างรอบเดียวแล้วออก
  python runner.py --dry-run  # ทดสอบ ไม่เรียก claude จริง แค่ปิดงานในคิว
"""
import sys, json, time, shutil, subprocess
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
STATE = ROOT / "state.json"
POLL_SEC = 3

# prompt สั่งตรง ระบุ path ไฟล์ชัด (เลียนแบบรูปแบบที่พิสูจน์แล้วว่า claude ลงมือสร้างไฟล์จริง)
SECRETARY_PROMPT = """สร้างไฟล์ workspace/{slug}/index.html เป็นงานนี้: "{order}"
ทำเป็น static HTML สวยงาม ใช้ inline CSS ธีมมืด responsive ทำให้เสร็จเป็นไฟล์จริงเดี๋ยวนี้
ใช้ Write tool เขียนไฟล์จริง ห้ามถามกลับ ห้ามแค่บรรยาย
ห้ามแก้ web/ หรือไฟล์หลักของโปรเจกต์ เขียนเฉพาะใน workspace/ เท่านั้น (ห้ามใช้ approve.py)
ถ้างานไม่ใช่หน้าเว็บ ให้สร้างไฟล์ที่เหมาะสมใน workspace/{slug}/ แทน"""

RETRY_PROMPT = """ย้ำ: ใช้ Write tool สร้างไฟล์ workspace/{slug}/index.html ขึ้นมาจริงๆ เดี๋ยวนี้
อย่าอธิบาย อย่าถาม — เขียนไฟล์เลย สำหรับงาน: "{order}\""""


def load():
    return json.loads(STATE.read_text(encoding="utf-8"))


def save(d):
    STATE.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now():
    return datetime.now().strftime("%H:%M")


def log(d, who, text):
    d.setdefault("activity", []).insert(0, {"time": now(), "who": who, "text": text})
    d["activity"] = d["activity"][:50]


def next_order(d):
    for o in reversed(d.get("orders", [])):   # เก่าสุดก่อน (FIFO)
        if not o.get("done"):
            return o
    return None


def make_slug(text):
    import re
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s or "task")[:40] + "-" + datetime.now().strftime("%H%M")


def call_claude(prompt):
    claude = shutil.which("claude")
    if not claude:
        return False, "ไม่พบ claude CLI — ลง: npm install -g @anthropic-ai/claude-code แล้ว login"
    try:
        res = subprocess.run(
            [claude, "-p", prompt, "--permission-mode", "acceptEdits"],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", timeout=1800,
        )
        return res.returncode == 0, (res.stdout or res.stderr or "").strip()[-500:]
    except subprocess.TimeoutExpired:
        return False, "หมดเวลา (เกิน 30 นาที)"
    except Exception as e:
        return False, f"error: {e}"


def workspace_files():
    ws = ROOT / "workspace"
    return {p for p in ws.rglob("*") if p.is_file() and p.name != ".gitkeep"}


def process_one(dry_run):
    d = load()
    o = next_order(d)
    if not o:
        return False
    print(f"▶ รับออเดอร์: {o['text']}")
    slug = make_slug(o["text"])
    log(d, "🤖 Runner", f"เริ่มงาน: {o['text']}")
    for a in d["agents"]:                       # runner คุมสถานะเลขาเอง (ชัวร์กว่าพึ่ง claude)
        if a["id"] == "secretary":
            a["status"] = "working"; a["task"] = o["text"]; a["thought"] = "กำลังลงมือทำ"; a["progress"] = 30
    save(d)

    before = workspace_files()
    if dry_run:
        print(f"[dry-run] ข้ามการเรียก claude สำหรับ: {o['text']}")
        ok, info = True, "(dry-run)"
    else:
        # รอบแรก
        ok, info = call_claude(SECRETARY_PROMPT.format(order=o["text"], slug=slug))
        # ตรวจ + retry 1 ครั้งถ้ายังไม่มีไฟล์
        if ok and not (workspace_files() - before):
            print("…ไม่มีไฟล์ ลองย้ำอีกรอบ (retry)")
            ok, info = call_claude(RETRY_PROMPT.format(order=o["text"], slug=slug))

    # ตรวจจริง: ต้องมีไฟล์ใหม่ใน workspace ถึงจะถือว่าทำงานจริง
    new_files = workspace_files() - before
    if ok and not dry_run and not new_files:
        ok = False
        info = "claude จบงานแต่ไม่มีไฟล์ output ใหม่ใน workspace/ (อาจแค่บรรยายงาน ไม่ได้ลงมือ)"
    elif new_files:
        info = f"สร้าง {len(new_files)} ไฟล์: " + ", ".join(sorted(str(p.relative_to(ROOT)) for p in new_files)[:5])

    d = load()  # โหลดใหม่ เผื่อ agent แก้ระหว่างทาง
    for x in d.get("orders", []):
        if x.get("time") == o.get("time") and x.get("text") == o.get("text"):
            x["done"] = True
            x["result"] = "ok" if ok else "failed"
    for a in d["agents"]:                       # อัปเดตเลขาตามผลจริง
        if a["id"] == "secretary":
            a["status"] = "idle"
            a["task"] = ("เสร็จ: " if ok else "ล้มเหลว: ") + o["text"]
            a["thought"] = info or ""
            a["progress"] = 100 if ok else a.get("progress", 0)
    # เด้งข้อความเข้าแชทให้เจ้านายเห็น
    msgs = d.setdefault("messages", [])
    if ok:
        reply = f"เสร็จแล้วครับ ✅ \"{o['text']}\"\n{info}\nเปิดดูได้ที่ workspace/ (ยังไม่แตะเว็บหลัก)"
    else:
        reply = f"งาน \"{o['text']}\" ยังไม่สำเร็จครับ ⚠️\n{info}"
    msgs.append({"role": "secretary", "time": now(), "text": reply})
    d["messages"] = msgs[-50:]
    log(d, "🤖 Runner", ("✓ เสร็จ: " if ok else "✗ ล้มเหลว: ") + o["text"] + (f" — {info}" if info else ""))
    save(d)
    print(("✓ เสร็จ" if ok else "✗ ล้มเหลว") + f": {info}")
    return True


def main():
    args = set(sys.argv[1:])
    dry = "--dry-run" in args
    once = "--once" in args
    print(f"runner เริ่มทำงาน (poll {POLL_SEC}s){' [once]' if once else ''}{' [dry-run]' if dry else ''}")
    while True:
        did = process_one(dry)
        if once and not did:
            print("คิวว่างแล้ว — ออก")
            break
        if not did:
            time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
