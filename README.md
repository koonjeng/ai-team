# ทีม AI (Secretary-led Team)

ทีม AI แบบมีเลขาเป็นหัวหน้า รับงานจากเจ้านาย → แตกงาน → มอบหมายลูกทีม → ตรวจ → ขออนุมัติก่อน deploy

## สมาชิกทีม
| Agent | บทบาท | สิทธิ์ |
|---|---|---|
| 👔 secretary | เลขา/orchestrator | สั่งงาน + อ่าน (แก้โค้ดไม่ได้) |
| 🎨 frontend | UI/UX | เขียน/แก้/รันโค้ด |
| ⚙️ backend | API/DB/logic | เขียน/แก้/รันโค้ด |
| 🧠 trainer | เทรน/ประเมินโมเดล AI | เขียน/แก้/รันโค้ด |
| 🔍 reviewer | QA ตรวจก่อน deploy | อ่าน + รัน (แก้โค้ดไม่ได้) |

## วิธีเริ่ม
เปิด Claude Code ที่โฟลเดอร์นี้ แล้วพิมพ์สั่งงาน "เลขา" — subagents โหลดอัตโนมัติจาก `.claude/agents/`

---

## ตัวอย่างที่ 1 — งานเล็ก (ทดสอบ flow เร็ว ๆ)

```
@secretary ช่วยทำหน้า "Hello" หน้าเดียว: มีปุ่มกด แล้วเรียก API /api/hello
ให้คืนข้อความ "สวัสดี <ชื่อ>" มาแสดง
```

สิ่งที่ควรเกิดขึ้น:
1. เลขาแตกงาน → มอบ backend ทำ `GET /api/hello?name=` → มอบ frontend ทำปุ่ม+แสดงผล
2. เลขาเรียก reviewer รันจริง → ออก verdict
3. เลขาสรุปขออนุมัติ → คุณตอบ `ACCEPT`

---

## ตัวอย่างที่ 2 — งานเต็ม flow (frontend + backend + reviewer)

```
@secretary ทำระบบ login:
- backend: POST /api/login รับ email/password, validate, คืน token
- frontend: หน้า login form + เก็บ token + redirect
- reviewer: ทดสอบทั้ง happy path และกรณีรหัสผิด
ทำเสร็จขอสรุปให้ผม Accept ก่อน deploy
```

เช็กว่าเลขาทำถูก:
- [ ] ถามกลับถ้าโจทย์ไม่ชัด (เช่น token แบบไหน, เก็บที่ไหน)
- [ ] backend ประกาศ API contract ให้ frontend ใช้ตรงกัน
- [ ] reviewer รันจริงแล้วรายงานสิ่งที่เห็น ไม่ใช่เดา
- [ ] **ไม่ deploy จนกว่าคุณพิมพ์ ACCEPT**

---

## ตัวอย่างที่ 3 — มี trainer ร่วมด้วย

```
@secretary ทำฟีเจอร์แนะนำสินค้า:
- trainer: เทรนโมเดล recommend จาก data/orders.csv วัดผลเทียบ baseline
- backend: API /api/recommend เรียกโมเดล
- frontend: แสดงรายการแนะนำในหน้า home
- reviewer: ตรวจว่าต่อกันครบและผลใช้งานได้จริง
```

เช็ก trainer:
- [ ] รายงาน metric ด้วยตัวเลขจริง + เทียบ baseline
- [ ] บอกความเสี่ยง (overfit / data leakage)
- [ ] แนะนำตรง ๆ ว่าควร deploy หรือยัง

---

## ตัวอย่างที่ 4 — ทดสอบด่าน Accept (สำคัญ)

หลังเลขาเสนอขออนุมัติ ลองตอบแบบนี้เพื่อเทสต์ว่าระบบเคารพด่าน Accept:

| คุณพิมพ์ | ผลที่ถูกต้อง |
|---|---|
| `ACCEPT` | เลขาสั่ง deploy |
| `แก้: ปุ่มสีไม่ตรงแบรนด์ เปลี่ยนเป็นน้ำเงิน` | เลขาตีงานกลับ frontend แล้ววนตรวจใหม่ |
| `deploy เลย` (ก่อน reviewer ตรวจ) | เลขาต้องทักว่ายังไม่ผ่าน reviewer |

---

## ทิป
- เรียกชื่อ agent ตรง ๆ ได้ด้วย `@frontend`, `@backend` ฯลฯ แต่แนะนำให้สั่งผ่าน `@secretary` เพื่อให้คุมทั้ง flow
- ถ้าเลขาข้ามขั้น (เช่น deploy โดยไม่ขอ Accept) ให้เตือน แล้วมันจะปรับ — หรือแก้ prompt ใน `.claude/agents/secretary.md`
