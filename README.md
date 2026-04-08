# Debt Manager API + Flet App

ระบบนี้พัฒนาตาม datadic จากไฟล์ `ตาราง หนี้.pdf` และอิง schema ใน MariaDB ของงานนี้:

- `user`
- `debt`
- `installment`

## ค่ามาตรฐานเครื่อง lab (ให้ตรงกันทั้งโปรเจกต์)

รหัสผ่านผู้ใช้ฐานข้อมูล **`api_user`** ใน MariaDB และค่า **`DB_PASSWORD`** ในไฟล์ `.env` ใช้ค่าเดียวกัน:

**`P@ssw0rd`**

ถ้าเครื่องคุณใช้รหัสอื่น ให้แก้ทั้งใน MariaDB และใน `.env` ให้ตรงกัน — อย่า commit ไฟล์ `.env` ขึ้น git

## เริ่มต้นครั้งแรก (ทำตามลำดับนี้)

1. **โฟลเดอร์โปรเจกต์**  
   ตัวอย่าง: `D:\Dowloard_D\kimp` (ถ้าโฟลเดอร์อยู่ที่อื่น ให้ `cd` ไปที่ที่มี `api.py`)

2. **สร้าง venv แล้วติดตั้งแพ็กเกจ**

```powershell
cd D:\Dowloard_D\kimp
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
```

3. **สร้างไฟล์ `.env`**  
   คัด `.env.example` ไปเป็นไฟล์ชื่อ `.env` ในโฟลเดอร์เดียวกับ `api.py`  
   ค่าเริ่มต้นใน `.env.example` ใช้ `DB_PASSWORD=P@ssw0rd` และ API พอร์ต **3500** อยู่แล้ว — แก้เฉพาะ `DB_HOST` ถ้า IP เครื่อง MariaDB ไม่ใช่ `192.168.137.50`

4. **ฐานข้อมูล MariaDB / MySQL**  
   - สร้างฐานชื่อ **`bidkom`**  
   - สร้างผู้ใช้ **`api_user`** รหัส **`P@ssw0rd`** และให้สิทธิ์บน `bidkom.*`  
   - ทำใน phpMyAdmin ก็ได้ หรือรัน SQL (ถ้า user มีอยู่แล้วอาจได้ error ซ้ำ — ให้ข้ามหรือใช้ `ALTER USER`)

```sql
CREATE DATABASE IF NOT EXISTS bidkom CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'api_user'@'%' IDENTIFIED BY 'P@ssw0rd';
GRANT ALL PRIVILEGES ON bidkom.* TO 'api_user'@'%';
FLUSH PRIVILEGES;
```

   **ทางลัด:** import ไฟล์ **`dump-bidkom-*.sql`** (ถ้ามีในโปรเจกต์) จะได้ทั้งโครงตารางและข้อมูลตัวอย่าง — หลัง import ยังต้องให้ `api_user` + รหัส `P@ssw0rd` เชื่อมกับฐานนี้ได้ตามที่ตั้งใน `.env`

5. **รัน API** (เปิด venv ก่อนทุกครั้ง)

```powershell
cd D:\Dowloard_D\kimp
.\env\Scripts\activate
uvicorn api:app --host 192.168.137.50 --port 3500 --reload
```

   - **`--host` / `--port` ต้องตรงกับ `UVICORN_HOST` / `UVICORN_PORT` ใน `.env`** ไม่งั้นแอป Flet จะเรียก API ผิดที่  
   - ทดสอบ: เปิด `http://192.168.137.50:3500/docs` หรือ `/health`  
   - ทางลัด: `.\run_api.ps1` หรือดับเบิลคลิก `run_api.bat` (ตั้ง host/port ใน `.ps1` ได้ — ค่าเริ่มต้น **พอร์ต 3500** ให้ตรง `.env`)

6. **รันแอป Flet** (เทอร์มินัลใหม่ ยัง activate venv)

```powershell
cd D:\Dowloard_D\kimp
.\env\Scripts\activate
python flet_app.py
```

   หรือแบบเว็บ (พอร์ต Flet เว็บเริ่มต้นมัก **3500** — **คนละตัวกับ API** ถ้า API ก็ใช้ 3500 อยู่แล้ว ให้ตั้งพอร์ต Flet เป็นอย่างอื่น เช่น 3550):

```powershell
$env:FLET_WEB_PORT = "3550"
python run_flet_web.py
```

## พอร์ต API: 3500 กับ 8000 (อย่าสลับโดยไม่แก้ `.env`)

| วิธีรัน | พอร์ต API ที่ใช้ | ต้องตั้งใน `.env` |
|--------|------------------|-------------------|
| คำสั่งในข้อ 5 ด้านบน / `run_api.ps1` / `run_api.bat` (ค่าเริ่มต้นโปรเจกต์) | **3500** | `UVICORN_PORT=3500` |
| `run_all.py`, `run_all_web.py` | **8000** | `UVICORN_PORT=8000` |

`app_config.py` ประกอบ URL ที่ Flet ใช้เรียก API จาก `UVICORN_*` (หรือ `API_BASE_URL`) — **พอร์ตใน `.env` ต้องตรงกับพอร์ตที่ uvicorn ฟังจริง**

## ไฟล์สำคัญ

- `api.py` — FastAPI สำหรับ CRUD และคำนวณตารางผ่อน/วันจบหนี้; สร้างตารางให้อัตโนมัติเมื่อรัน API (ถ้าเชื่อม DB ได้)
- `flet_app.py` — entrypoint แอป Flet
- `ui/` — หน้าจอแยกไฟล์ (login / signup / dashboard / result ฯลฯ)
- `requirements.txt` — dependency
- `.env.example` — แม่แบบ `.env` (รหัส lab `P@ssw0rd`)

### อัปโหลดไปเซิร์ฟเวอร์ (FileZilla ฯลฯ) — อย่าอัปโหลดโฟลเดอร์ `env`

โฟลเดอร์ venv (`env`) เก็บ path แบบเต็มไปที่ Python เครื่องที่สร้าง — คัดไปเครื่องอื่นจะ error แบบ `did not find executable at ...`

**บนเครื่องที่รันจริง:** อัปโหลดโค้ด + `requirements.txt` (+ สร้าง `.env` บนเซิร์ฟเวอร์) แล้วสร้าง venv ใหม่:

```powershell
cd D:\Dowloard_D\kimp
Remove-Item -Recurse -Force env -ErrorAction SilentlyContinue
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --host 192.168.137.50 --port 3500 --reload
```

ต้องมี Python บนเซิร์ฟเวอร์ (`python --version`) — แนะนำติดตั้งจาก [python.org](https://www.python.org/downloads/) ถ้าไม่ใช้ Microsoft Store

## ทางเลือก: ตั้งค่า DB ชั่วคราวด้วยตัวแปรสภาพแวดล้อม (ไม่ใช้ `.env`)

```powershell
$env:DB_HOST = "192.168.137.50"
$env:DB_USER = "api_user"
$env:DB_PASSWORD = "P@ssw0rd"
$env:DB_NAME = "bidkom"
uvicorn api:app --host 0.0.0.0 --port 3500 --reload
```

ถ้าใช้วิธีนี้ แอป Flet ยังต้องรู้พอร์ต API — ตั้ง `UVICORN_PORT` / `API_BASE_URL` ให้ตรง หรือพึ่งค่า default ใน `app_config.py`

## เปิดบนมือถือ (WiFi / LAN เดียวกับคอม)

**หลักการ:** หน้าเว็บ Flet รันที่ PC; มือถือเปิดเบราว์เซอร์เข้า `http://<IPv4-ของคอม>:<พอร์ต-Flet>`  
การเรียก FastAPI ทำที่ Python บน PC (`httpx` ใน `ui/api_client`) — ใน `.env` ให้ `UVICORN_*` ชี้ไปที่ API บนเครื่องเดียวกับที่รัน `run_flet_web.py` (บนเครื่องเดียวกันมักใช้ `http://127.0.0.1:<พอร์ต-api>` ได้)

**ขั้นตอนสั้น ๆ**

1. คอมกับมือถืออยู่วง WiFi เดียวกัน  
2. รัน API: `uvicorn api:app --host 0.0.0.0 --port 3500 --reload`  
3. รัน Flet เว็บด้วยพอร์ตคนละตัว เช่น `FLET_WEB_PORT=3550` แล้ว `python run_flet_web.py`  
4. ดู IP คอม: `ipconfig` → IPv4 ของ WiFi  
5. บนมือถือเปิด `http://<IP-คอม>:3550` — **ห้ามใช้ `127.0.0.1` บนมือถือ**  
6. ถ้าเข้าไม่ได้ — ตรวจ Windows Firewall (Inbound TCP พอร์ตที่ใช้)

### ค้างที่หน้า “Working...”

มาจาก Flet Web ขณะโหลด / WebSocket — ดูตารางด้านล่าง

| สาเหตุที่พบบ่อย | ทำอย่างไร |
|------------------|-----------|
| โหลดครั้งแรกช้า (มือถือ) | รอ 1–3 นาที; ค่าเริ่มต้น `FLET_WEB_RENDERER=canvaskit` ใน `run_flet_web.py` — ถ้าอยากเบาลงลอง `auto` |
| Firewall / AP isolation | อนุญาตพอร์ต Flet; ปิด client isolation บนเราเตอร์ถ้ามี |
| ใช้ `127.0.0.1` บนมือถือ | ใช้ `http://<IP-คอม>:พอร์ต` เท่านั้น |
| ค้างนาน | ลอง `FLET_DISABLE_BG_GIF_WEB=1`; ทดสอบบน Chrome ที่คอม `http://127.0.0.1:<พอร์ต-Flet>` |

### GIF พื้นหลังบนมือถือนิ่ง

`FLET_WEB_RENDERER=auto` บนมือถือมักทำให้ GIF ไม่ขยับ — `run_flet_web.py` ตั้ง `canvaskit` เป็นค่าเริ่มต้น  
มีทางสำรองด้วย Pillow (อยู่ใน `requirements.txt`)

**ถ้าโจทต้องการแอปติดเครื่อง / Store** — โปรเจกต์นี้เป็น Python + Flet; ส่วนใหญ่งาน lab ใช้การเปิดผ่านเบราว์เซอร์ตามด้านบนก็เพียงพอ

---

## ตั้งค่า Database (สรุป env)

ค่าที่ `api.py` อ่าน (แก้ใน `.env` หรือตัวแปรระบบ):

- `DB_HOST` — เช่น `192.168.137.50`
- `DB_PORT` — `3306`
- `DB_USER` — **`api_user`** (ไม่แนะนำใช้ `root` เป็นค่าเริ่มต้น ถ้า root ใช้ `auth_gssapi` จะเจอ PyMySQL error **2059**)
- `DB_PASSWORD` — **`P@ssw0rd`** (มาตรฐาน lab ใน `.env.example`)
- `DB_NAME` — `bidkom`

## สคริปต์ช่วยรัน

| ไฟล์ | ทำอะไร |
|------|--------|
| `run_all.py` | ถ้า API ที่ `127.0.0.1:8000` ยังไม่ขึ้น จะสตาร์ท uvicorn พอร์ต **8000** แล้วเปิด `flet_app.py` — ตั้ง `UVICORN_PORT=8000` ใน `.env` ก่อน |
| `run_all_web.py` | เหมือนกันแต่เปิดเว็บผ่าน `run_flet_web.py` — เช่นกัน API **8000** |
| `run_flet_web.py` | รันเฉพาะ Flet เว็บ — ต้องมี API รันอยู่แล้ว และ `.env` ชี้พอร์ต API ถูกต้อง |
| `run_api.ps1` / `run_api.bat` | activate venv แล้ว uvicorn — พอร์ตเริ่มต้น **3500** ให้คู่กับ `.env.example` |

## อัปโหลดขึ้นเซิร์ฟเวอร์ด้วย FileZilla

### แก้เฉพาะ backend

1. อัปโหลด `api.py`, `app_config.py` (ถ้าแก้), `requirements.txt` (ถ้าแก้ dependency)  
2. บนเซิร์ฟเวอร์: `pip install -r requirements.txt` ใน venv  
3. รีสตาร์ท: `uvicorn api:app --host 0.0.0.0 --port 3500` (หรือพอร์ตที่ deploy ใช้)

### แก้หน้าจอ Flet / `ui/`

อัปโหลดไฟล์ที่แก้ เช่น `flet_app.py`, `ui\**`, `img\**`, `run_flet_web.py`

### หมายเหตุ

- ไม่อัปโหลด `env/` — สร้าง venv บนเซิร์ฟเวอร์  
- `.env` มักไม่ใส่ใน zip — สร้างบนเซิร์ฟเวอร์จาก `.env.example` แล้วใส่ `DB_PASSWORD` ให้ตรงเครื่องนั้น  
- ไฟล์ API หลักคือ **`api.py`**
