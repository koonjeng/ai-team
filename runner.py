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

# prompt ที่ส่งให้ Claude Code สวมบทเลขา รับ 1 ออเดอร์
SECRETARY_PROMPT = """คุณคือ "เลขา" หัวหน้าทีม AI ในโปรเจกต์นี้ (ดู .claude/agents/)
เจ้านายสั่งงานนี้มา ให้คุณแตกงานเป็น task ย่อย แล้วมอบหมายให้ทีม
(frontend/backend/trainer/reviewer ตามความเหมาะสม) ทำจนเสร็จ

⚠️ กฎสำคัญเรื่องไฟล์:
- ให้สร้าง/แก้ผลงานทั้งหมดไว้ในโฟลเดอร์ workspace/ เท่านั้น (แยกชื่อโฟลเดอร์ย่อยตามงาน)
- ห้ามแก้ไฟล์หลักของเว็บหลัก/Home Office: app.py, web/, state.json, team.py, runner.py, .claude/
  (มี guard กั้นอยู่ ถ้าจำเป็นต้องแก้จริง ต้องให้เจ้านายอนุญาตและรัน `python approve.py on` ก่อน)
- การอัปเดตสถานะ dashboard ทำได้ปกติผ่านคำสั่ง team.py (ไม่นับเป็นการแก้ไฟล์หลัก)

ระหว่างทำงาน ให้แต่ละ agent อัปเดตสถานะลง dashboard ด้วยคำสั่ง:
  python team.py status <id> --status working --task "..." --thought "..." --progress N
และก่อน deploy ต้องให้ reviewer ตรวจ แล้วสรุปขอเจ้านาย Accept

=== คำสั่งจากเจ้านาย ===
{order}
"""


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


def run_order(order_text, dry_run):
    """เรียก Claude Code แบบ headless ให้เลขาจัดการ 1 ออเดอร์"""
    if dry_run:
        print(f"[dry-run] ข้ามการเรียก claude สำหรับ: {order_text}")
        return True, "(dry-run)"
    claude = shutil.which("claude")
    if not claude:
        return False, "ไม่พบ claude CLI — ลง: npm install -g @anthropic-ai/claude-code แล้ว login"
    prompt = SECRETARY_PROMPT.format(order=order_text)
    try:
        # -p = print mode (headless), อนุญาตให้แก้ไฟล์ได้เพื่อทำงานจริง
        res = subprocess.run(
            [claude, "-p", prompt, "--permission-mode", "acceptEdits"],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", timeout=1800,
        )
        ok = res.returncode == 0
        return ok, (res.stdout or res.stderr or "").strip()[-500:]
    except subprocess.TimeoutExpired:
        return False, "หมดเวลา (เกิน 30 นาที)"
    except Exception as e:
        return False, f"error: {e}"


def process_one(dry_run):
    d = load()
    o = next_order(d)
    if not o:
        return False
    print(f"▶ รับออเดอร์: {o['text']}")
    log(d, "🤖 Runner", f"เริ่มงาน: {o['text']}")
    save(d)

    ok, info = run_order(o["text"], dry_run)

    d = load()  # โหลดใหม่ เผื่อ agent แก้ระหว่างทาง
    for x in d.get("orders", []):
        if x.get("time") == o.get("time") and x.get("text") == o.get("text"):
            x["done"] = True
            x["result"] = "ok" if ok else "failed"
    log(d, "🤖 Runner", ("✓ เสร็จ: " if ok else "✗ ล้มเหลว: ") + o["text"] + (f" — {info}" if not ok else ""))
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
