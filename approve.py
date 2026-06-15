"""
approve.py — เปิด/ปิดสิทธิ์แก้ไฟล์หลักของ Home Office/เว็บหลัก

  python approve.py on      # อนุญาตให้แก้ไฟล์หลักได้ (ใช้เมื่อเจ้านายอนุมัติ)
  python approve.py off     # ล็อกกลับ (ค่าเริ่มต้น = ล็อก)
  python approve.py status  # ดูสถานะ

ค่าเริ่มต้น: ล็อก (ไม่มี token) -> guard.py จะบล็อกการแก้ไฟล์หลัก
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent.resolve()
TOKEN = ROOT / ".claude" / ".allow-core"


def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    if cmd == "on":
        TOKEN.parent.mkdir(exist_ok=True)
        TOKEN.write_text("allowed\n", encoding="utf-8")
        print("🔓 ปลดล็อกแล้ว — แก้ไฟล์หลักได้ (อย่าลืม python approve.py off เมื่อเสร็จ)")
    elif cmd == "off":
        TOKEN.unlink(missing_ok=True)
        print("🔒 ล็อกแล้ว — ไฟล์หลักถูกป้องกัน แก้ไม่ได้จนกว่าจะอนุญาต")
    else:
        print("🔓 ปลดล็อก (แก้ได้)" if TOKEN.exists() else "🔒 ล็อก (ป้องกันอยู่)")


if __name__ == "__main__":
    main()
