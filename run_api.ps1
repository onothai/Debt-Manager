# รัน API แบบเดียวกับ: activate env แล้ว uvicorn
# ใช้: .\run_api.ps1
# แก้ Host/Port ด้านล่างได้ครั้งเดียวถ้าต้องการ

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$uvicornHost = "192.168.137.50"
$uvicornPort = 3500

if (-not (Test-Path ".\env\Scripts\Activate.ps1")) {
    Write-Host "ยังไม่มี venv — รันก่อน: python -m venv env && .\env\Scripts\activate && pip install -r requirements.txt"
    exit 1
}

. .\env\Scripts\Activate.ps1
Write-Host "venv OK — DB จากไฟล์ .env (ถ้ามี) — uvicorn http://${uvicornHost}:${uvicornPort}"
uvicorn api:app --host $uvicornHost --port $uvicornPort --reload
