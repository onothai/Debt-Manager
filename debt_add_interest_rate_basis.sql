-- MariaDB / MySQL: เพิ่มคอลัมน์ฐานอัตราดอกเบี้ย (รันครั้งเดียวถ้ายังไม่มีคอลัมน์)
ALTER TABLE debt ADD COLUMN interest_rate_basis VARCHAR(16) NOT NULL DEFAULT 'year';
