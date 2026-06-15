"""
team.py — เครื่องมือให้ agent เขียนสถานะ/ประวัติลง state.json (ใช้กับ dashboard)

วิธีใช้ (agent เรียกผ่าน Bash ตอนทำงาน):
  # อัปเดตสถานะตัวเอง (อัปเดตเฉพาะฟิลด์ที่ส่งมา)
  python team.py status backend --status working --task "POST /api/login" --thought "เขียน validate" --progress 75

  # บันทึกกิจกรรมลงฟีดกลาง
  python team.py log backend "ส่ง API contract ให้ frontend แล้ว"

ทุกครั้งที่ status เปลี่ยน task/thought จะถูกบันทึกเข้า history ของ agent ด้วยอัตโนมัติ
"""
import sys, json, argparse
from pathlib import Path
from datetime import datetime

# ให้ print ภาษาไทย/อีโมจิลง console Windows ได้ไม่ error
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

STATE = Path(__file__).parent / "state.json"


def load():
    return json.loads(STATE.read_text(encoding="utf-8"))


def save(data):
    STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now():
    return datetime.now().strftime("%H:%M")


def find_agent(data, agent_id):
    for a in data["agents"]:
        if a["id"] == agent_id:
            return a
    raise SystemExit(f"ไม่พบ agent: {agent_id}")


def cmd_status(args):
    data = load()
    a = find_agent(data, args.agent)
    changed = []
    if args.status is not None: a["status"] = args.status; changed.append(f"สถานะ→{args.status}")
    if args.task is not None:   a["task"] = args.task;     changed.append(f"งาน: {args.task}")
    if args.thought is not None: a["thought"] = args.thought
    if args.progress is not None: a["progress"] = args.progress; changed.append(f"{args.progress}%")

    # บันทึกประวัติราย agent
    a.setdefault("history", [])
    note = args.task if args.task is not None else a.get("task", "")
    a["history"].insert(0, {"time": now(), "status": a["status"], "text": note or " · ".join(changed) or "อัปเดต"})
    a["history"] = a["history"][:30]

    # ลงฟีดกลางด้วย
    data.setdefault("activity", [])
    data["activity"].insert(0, {"time": now(), "who": f'{a["icon"]} {a["name"]}', "text": " · ".join(changed) or "อัปเดตสถานะ"})
    data["activity"] = data["activity"][:50]

    save(data)
    print(f"✓ อัปเดต {a['name']}: {' · '.join(changed) or '(thought)'}")


def cmd_log(args):
    data = load()
    a = find_agent(data, args.agent)
    data.setdefault("activity", [])
    data["activity"].insert(0, {"time": now(), "who": f'{a["icon"]} {a["name"]}', "text": args.text})
    data["activity"] = data["activity"][:50]
    a.setdefault("history", [])
    a["history"].insert(0, {"time": now(), "status": a.get("status", ""), "text": args.text})
    a["history"] = a["history"][:30]
    save(data)
    print(f"✓ log {a['name']}: {args.text}")


def main():
    p = argparse.ArgumentParser(description="อัปเดตสถานะทีมลง state.json")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="อัปเดตสถานะ agent")
    s.add_argument("agent")
    s.add_argument("--status", choices=["working", "waiting", "idle"])
    s.add_argument("--task")
    s.add_argument("--thought")
    s.add_argument("--progress", type=int)
    s.set_defaults(func=cmd_status)

    l = sub.add_parser("log", help="บันทึกกิจกรรมลงฟีด")
    l.add_argument("agent")
    l.add_argument("text")
    l.set_defaults(func=cmd_log)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
