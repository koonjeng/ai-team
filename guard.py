"""
guard.py — ตัวกั้นแก้ไฟล์หลัก (Claude Code PreToolUse hook)

บล็อกการ Edit/Write ไฟล์แกนของ Home Office / เว็บหลัก
เว้นแต่จะ "เปิดอนุญาต" ไว้ก่อน (มีไฟล์ token .claude/.allow-core)

agent ทำงานทั่วไปให้เขียน output ลงโฟลเดอร์ workspace/ เท่านั้น (ไม่ถูกบล็อก)

เปิด/ปิดอนุญาตด้วย:  python approve.py on   |   python approve.py off
"""
import sys, json
from pathlib import Path

try:
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent.resolve()
TOKEN = ROOT / ".claude" / ".allow-core"

# ไฟล์/โฟลเดอร์แกนที่ต้องขออนุญาตก่อนแก้
PROTECTED = [
    ROOT / "app.py",
    ROOT / "team.py",
    ROOT / "runner.py",
    ROOT / "guard.py",
    ROOT / "approve.py",
    ROOT / "state.json",
    ROOT / "README.md",
    ROOT / "web",
    ROOT / ".claude",
]


def is_protected(target: Path) -> bool:
    try:
        target = target.resolve()
    except Exception:
        return False
    for p in PROTECTED:
        if target == p or p in target.parents:
            return True
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # อ่าน payload ไม่ได้ -> ปล่อยผ่าน

    fp = (data.get("tool_input") or {}).get("file_path")
    if not fp:
        sys.exit(0)

    target = Path(fp)
    if not target.is_absolute():
        target = ROOT / target

    if is_protected(target) and not TOKEN.exists():
        # exit code 2 = บล็อก tool + ส่งข้อความให้ Claude เห็น
        sys.stderr.write(
            f"⛔ ถูกกั้นโดย guard: ห้ามแก้ไฟล์หลักของ Home Office/เว็บหลัก ({target.name})\n"
            "ถ้าต้องแก้จริง ขออนุญาตเจ้านายก่อน แล้วให้รัน: python approve.py on\n"
            "งานทั่วไปให้เขียน output ลงโฟลเดอร์ workspace/ แทน\n"
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
