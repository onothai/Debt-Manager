# Debt Manager API + Flet App

ระบบนี้พัฒนาตาม datadic จากไฟล์ `ตาราง หนี้.pdf` และอิง schema ใน MariaDB ของงานนี้:
- `user`
- `debt`
- `instalment`

## ไฟล์สำคัญ
- `api.py` : FastAPI สำหรับ CRUD และคำนวณตารางผ่อน/วันจบหนี้
- `flet_app.py` : entrypoint แอป Flet
- `ui/` : โครงสร้างหน้าแอปแบบแยกไฟล์ (login / signup / dashboard / result)
- `requirements.txt` : dependency สำหรับติดตั้งก่อน deploy
- MySQL DB : ระบบจะสร้างตารางให้อัตโนมัติเมื่อรัน API

## ติดตั้ง (ครั้งแรกบนเครื่อง)
```powershell
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
```

### อัปโหลดไปเซิร์ฟเวอร์ (FileZilla ฯลฯ) — อย่าอัปโหลดโฟลเดอร์ `env`

โฟลเดอร์ venv (`env`) เก็บ **path แบบเต็ม** ไปที่ Python เครื่องที่สร้าง — ถ้าคัด `env` จากเครื่องหนึ่งไปอีกเครื่อง จะ error แบบ `did not find executable at ... PythonSoftwareFoundation...`

**บนเครื่องที่รันจริง:** อัปโหลดแค่โค้ด + `requirements.txt` (+ `.env` หรือสร้างใหม่บนเซิร์ฟเวอร์) แล้วสร้า venv ใหม่ที่นั่น:

```powershell
cd C:\mobileapp_api
Remove-Item -Recurse -Force env   # ถ้ามี env เก่าที่คัดมาผิด ๆ — ลบทิ้ง
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --host 192.168.137.50 --port 3500 --reload
```

ต้องมี Python ติดตั้งบนเซิร์ฟเวอร์แล้ว (`python --version` ใช้ได้) — ถ้าใช้ Python จาก Microsoft Store บนเครื่อง dev แต่เซิร์ฟเวอร์ไม่มี ให้ติดตั้ง Python จาก [python.org](https://www.python.org/downloads/) บนเซิร์ฟเวอร์ก่อน

## วิธีรันโค้ด (แนวเดียวกับโปรเจกต์ lab `mobileapp_api`: bookstore_api + uvicorn)

ทุกครั้งที่จะรัน ให้เข้า **virtual environment** ก่อน แล้วค่อยสั่งคำสั่งด้านล่าง

### 1) ตั้งค่า DB แบบครั้งเดียว (หลังรีบูตเครื่องไม่ต้องทำใหม่)

คัด `.env.example` เป็นไฟล์ชื่อ **`.env`** ในโฟลเดอร์เดียวกับ `api.py` แล้วแก้รหัสผ่านให้ตรง MariaDB:

```
DB_HOST=192.168.137.50
DB_PORT=3306
DB_USER=api_user
DB_PASSWORD=รหัสของคุณ
DB_NAME=bidkom

UVICORN_HOST=192.168.137.50
UVICORN_PORT=3500
```

`UVICORN_*` ให้ตรงกับคำสั่ง `uvicorn` — แอป Flet จะใช้ `http://UVICORN_HOST:UVICORN_PORT` เรียก API อัตโนมัติ (ดู `app_config.py`)  
`api.py` โหลด `.env` ผ่าน `app_config` + `python-dotenv`

### 2) เปิด venv แล้วรัน API (แบบเดียวกับโปรเจกต์เก่า / lab)

เข้าโฟลเดอร์ที่มี `api.py` กับ `requirements.txt` แล้ว activate แล้วรัน `uvicorn` ตรง ๆ — **ไม่ต้องตั้ง `$env:` ทุกครั้ง** ถ้ามีไฟล์ `.env` แล้ว (ข้อ 1)

```powershell
cd D:\Dowloard_D\kimp
.\env\Scripts\activate
uvicorn api:app --host 192.168.137.50 --port 3500 --reload
```

(ถ้าโปรเจกต์อยู่ `C:\mobileapp_api` ให้ `cd` ไปที่นั้น) — **host/port ต้องตรงกับ `UVICORN_*` ใน `.env`**  
ตรวจ API: `http://192.168.137.50:3500/docs` หรือ `/health`

**ทางเลือก:** ดับเบิลคลิก `run_api.bat` หรือ `.\run_api.ps1` — สคริปต์จะ activate แล้วรัน uvicorn ให้ (แก้ Host/Port ในไฟล์สคริปต์ได้)

### 3) ทางเลือก: ตั้งค่า DB แบบชั่วคราวด้วย env (ไม่ใช้ .env)

```powershell
$env:DB_HOST = "192.168.137.50"
$env:DB_USER = "api_user"
$env:DB_PASSWORD = "รหัสของคุณ"
$env:DB_NAME = "bidkom"
uvicorn api:app --host 0.0.0.0 --port 8000
```

### 4) รันแอป Flet (เปิดหน้าต่างอื่น โดยยังเปิด venv อยู่)

ถ้าใน `.env` มี `UVICORN_HOST` / `UVICORN_PORT` ตรงกับ uvicorn แล้ว แอปจะเรียก API ที่ **`http://<host>:<port>`** นั้นโดยอัตโนมัติ — หรือใส่ **`API_BASE_URL`** เต็ม ๆ แทนได้ (จะ override `UVICORN_*`)  
ถ้าไม่มีทั้งคู่ โปรเจกต์นี้มีค่า fallback ใน `app_config.py` (เช่น `192.168.137.50:3500`) — ดูไฟล์นั้นและ `.env.example`

```powershell
python flet_app.py
```
หรือรันเว็บ Flet (พอร์ต **เว็บ** Flet เริ่มต้น 3500 ใน `run_flet_web.py` — **คนละพอร์ตกับ FastAPI**; ถ้า uvicorn ใช้พอร์ต 3500 อยู่แล้ว ให้ตั้ง `$env:FLET_WEB_PORT='3550'` ก่อนรัน Flet เว็บ):
```powershell
python run_flet_web.py
```

### 5) เปิดบนมือถือ (WiFi / วง LAN เดียวกับคอม)

**แนวที่โจทมักต้องการ:** มือถือเปิด **เบราว์เซอร์** (Chrome/Safari) แล้วเข้าแอปแบบเว็บ — **ไม่ต้องติดตั้งแอปจาก Store** ถ้าอาจารย์ไม่ระบุ

**หลักการสั้น ๆ**

- หน้าเว็บ Flet รันที่ **PC** — มือถือแค่โหลด UI ผ่านเครือข่าย
- การเรียก **FastAPI** ทำที่ **Python บน PC** (`httpx` ใน `ui/api_client`) ไม่ใช่ให้มือถือยิง API ตรง ๆ ดังนั้นใน `.env` ให้ `API_BASE_URL` / `UVICORN_*` ชี้ไปที่ API บนเครื่องเดียวกับที่รัน `run_flet_web.py` (ปกติใช้ `http://127.0.0.1:<พอร์ต-api>` ก็ได้ ถ้า API รันบนเครื่องเดียวกัน)

**ขั้นตอนแนะนำ**

1. **คอมกับมือถือต่อ WiFi วงเดียวกัน** (หรือมือถือต่อ hotspot จากคอม — แล้วใช้ IP ฝั่งคอมในวงนั้น)
2. **รัน FastAPI ให้ฟังทุก interface** (ให้มือถือ “เข้าถึงเครื่องคอม” ได้เมื่อต้องตรวจจากมือถือ — ส่วนใหญ่โฟกัสที่หน้าเว็บ Flet; ถ้า API อยู่คอมเดียวกับ Flet ใช้ `--host 0.0.0.0` สะดวกที่สุด):
   ```powershell
   uvicorn api:app --host 0.0.0.0 --port 3500 --reload
   ```
3. **รัน Flet แบบเว็บ** โดย bind `0.0.0.0` (เป็นค่าเริ่มต้นใน `run_flet_web.py`) และใช้ **พอร์ตคนละตัวกับ API** — ถ้า API ใช้ 3500 แล้ว ให้ใช้พอร์ตอื่น เช่น 3550:
   ```powershell
   $env:FLET_WEB_PORT = "3550"
   python run_flet_web.py
   ```
4. ดู **IP ของคอมในวงเดียวกัน** (PowerShell): `ipconfig` → หา `IPv4 Address` ของอแดปเตอร์ WiFi (เช่น `192.168.137.50`)
5. **บนมือถือ** เปิดเบราว์เซอร์ไปที่ **`http://<IPv4-ของคอม>:3550`**  
   - **ห้ามใช้** `http://127.0.0.1:...` บนมือถือ — `127.0.0.1` หมายถึงตัวมือถือเอง ไม่ใช่คอม
6. ถ้าเปิดไม่ได้ — เปิด **Windows Defender Firewall** ให้อนุญาต **Inbound** TCP สำหรับพอร์ตที่ใช้ (พอร์ต Flet เว็บ + พอร์ต API ถ้าต้องเข้าถึง `/docs` จากมือถือ) หรือสร้างกฎอนุญาต `python.exe`

### ค้างที่หน้า “Working...” (จุดฟ้า + ตัวหนังสือ)

ข้อความนี้มาจาก **Flet Web** เอง ยังไม่ใช่หน้า login ของโปรเจกต์ — หมายถึงเบราว์เซอร์กำลังโหลด engine / เชื่อม **WebSocket** ไปที่เครื่อง `python run_flet_web.py`

| สาเหตุที่พบบ่อย | ทำอย่างไร |
|------------------|-----------|
| โหลดครั้งแรกช้า (โดยเฉพาะมือถือ) | รอ 1–3 นาทีครั้งแรก; ค่าเริ่มต้นใช้ **`FLET_WEB_RENDERER=canvaskit`** เพื่อให้ GIF พื้นหลังขยับ — ถ้าอยากโหลดเบาลง: ตั้ง **`auto`** (พื้นหลังอาจนิ่งบนมือถือ) |
| ไฟร์วอลล์ / เราเตอร์ตัด client-to-client | เปิดอนุญาตพอร์ต Flet (เช่น 3550); ปิด **AP isolation / Client isolation** บน WiFi ถ้ามี |
| ใช้ `127.0.0.1` บนมือถือ | ต้องใช้ `http://<IP-คอม>:พอร์ต` เท่านั้น |
| ยังค้างนาน | ลอง `FLET_DISABLE_BG_GIF_WEB=1` แล้วรันใหม่; หรือเปิดบน **Chrome บนคอม** ที่ `http://127.0.0.1:3550` ถ้าคอมได้แต่มือถือไม่ได้ = ปัญหาเครือข่ายไม่ใช่โค้ดแอป |

### GIF พื้นหลังบนมือถือเป็นภาพนิ่ง (บนคอมขยับได้)

**สาเหตุหลัก:** โหมด **`FLET_WEB_RENDERER=auto`** บนมือถือมักใช้ renderer ที่อัปเดตรูปพื้นหลังไม่สม่ำเสมอ — **`run_flet_web.py` ตั้งค่าเริ่มต้นเป็น `canvaskit` แล้ว** (โหลดครั้งแรกหนักกว่าแต่ GIF มักขยับได้)

โปรเจกต์ยังใช้ **Pillow สลับเฟรม** บนเว็บ (ต้อง `pip install Pillow`) เป็นเส้นทางสำรองเมื่อ GIF แบบ native ไม่เล่น

- อยากให้เว็บใช้ `ft.Image` แบบเดิม (พฤติกรรมเหมือนก่อน): `FLET_BG_GIF_WEB_NATIVE=1`
- ปิดการสลับเฟรม: `FLET_DISABLE_MANUAL_GIF_ANIM=1`

**ถ้าโจทต้องการ “แอปแท้บนมือถือ” (ไอคอนติดเครื่อง / Store)**  
โปรเจกต์นี้เป็นแพ็กเกจ Python + Flet — ทางที่ทำได้ในโลกจริงคือ **build เป็น native** (Flet mobile build / Android APK / iOS ผ่าน toolchain ของ Flet) หรือ **PWA**  
สำหรับงาน lab ส่วนใหญ่ **การเข้าเว็บผ่าน WiFi ตามข้อ 5** ถือว่าครบโจท “รันบนมือถือ + วงเน็ตเดียวกัน” แล้ว — ถ้าอาจารย์กำหนดรูปแบบ build ชัดเจน ค่อยทำขั้นตอน packaging เพิ่ม

---

## ตั้งค่า Database (MySQL)
ค่าเริ่มต้นใน `api.py` (แก้ได้ด้วย env):
- `DB_HOST=192.168.137.50`
- `DB_PORT=3306`
- `DB_USER=api_user` — **ไม่ใช้ `root` เป็นค่าเริ่มต้น** เพราะ MariaDB หลายเครื่องใช้ `auth_gssapi` กับ root แล้ว PyMySQL จะ error **2059**
- `DB_PASSWORD=P@ssw0rd` — ต้องตรงกับที่สร้าง `api_user` ใน MariaDB
- `DB_NAME=bidkom`

ถ้าต้องการเปลี่ยนค่าในเครื่องเซิร์ฟเวอร์ สามารถตั้ง ENV ก่อนรันได้ — **PowerShell** ใช้ `$env:DB_HOST=...` (ดูตัวอย่างในข้อ 2 ด้านบน); ถ้าใช้ **cmd** ใช้ `set DB_HOST=...`

## สคริปต์ช่วยรัน (ทางลัด)

| ไฟล์ | ทำอะไร |
|------|--------|
| `run_all.py` | ถ้ายังไม่มี API ที่พอร์ต 8000 จะสตาร์ท `uvicorn` ให้ แล้วเปิด `flet_app.py` (แอปหน้าต่าง) |
| `run_all_web.py` | แบบเดียวกันแต่เปิดเว็บผ่าน `run_flet_web.py` |
| `run_flet_web.py` | รันเฉพาะ Flet แบบเว็บ (พอร์ตเริ่มต้น 3500) — ต้องมี API รันอยู่แล้ว |

## อัปโหลดขึ้นเซิร์ฟเวอร์ด้วย FileZilla

แยกตามว่าแก้ **ฝั่ง API อย่างเดียว** หรือแก้ **ทั้งแอป**

### กรณีแก้เฉพาะ backend (แนะนำแบบงานเก่า — อัปโหลดน้อยที่สุด)

ถ้าแก้แค่ logic / endpoint ใน FastAPI ชัดเจนว่า **ไม่ได้เพิ่มไลบรารีใหม่** ใน `requirements.txt`:

1. อัปโหลดทับบนเซิร์ฟเวอร์เฉพาะ:
   - `api.py`
   - `app_config.py` (ถ้าโค้ดรุ่นใหม่มี — ใช้ร่วมกับ Flet เรื่อง URL API)
2. ถ้ามีการแก้ `requirements.txt` (เพิ่ม/เปลี่ยนแพ็กเกจ) ให้อัปโหลดเพิ่ม:
   - `requirements.txt`
3. SSH/RDP ไปที่เซิร์ฟเวอร์ แล้วใน venv รัน:
   ```powershell
   pip install -r requirements.txt
   ```
4. รีสตาร์ท API:
   ```powershell
   uvicorn api:app --host 0.0.0.0 --port 8000
   ```

สรุป: **ขั้นต่ำที่มักใช้จริงคือ `api.py` + `requirements.txt` (เฉพาะเมื่อไฟล์ req เปลี่ยน)**

### กรณีแก้หน้าจอแอป Flet / โฟลเดอร์ `ui/`

ต้องอัปโหลดไฟล์ที่แก้ด้วย เช่น `flet_app.py`, `ui\**`, `img\**`, `run_flet_web.py` ตามที่เปลี่ยนจริง — ไม่ได้จำกัดแค่สองไฟล์เหมือนข้างบน

### หมายเหตุ

- โฟลเดอร์ `env/` ไม่ต้องอัปโหลด — สร้าง venv บนเซิร์ฟเวอร์เองแล้ว `pip install -r requirements.txt`
- ไฟล์ **`.env` มักไม่ได้อยู่ใน zip / ไม่ได้อัปโหลด** (หรือลืม) — ถ้าไม่มี ให้ **สร้างบนเซิร์ฟเวอร์** โดยคัดจาก `.env.example` หรืออัปโหลด `.env` แยกใน FileZilla อย่างตั้งใจ ไม่เช่นนั้นแอปอาจใช้ค่า fallback จาก `app_config.py` เท่านั้น
- ชื่อไฟล์ API ของโปรเจกต์นี้คือ **`api.py`** (เทียบเท่า `bookstore_api.py` ในงาน lab)
