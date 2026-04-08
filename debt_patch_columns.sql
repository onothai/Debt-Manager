-- รันครั้งเดียวบน MariaDB/MySQL ถ้า GET /debts ได้ 500 (คอลัมน์ไม่ตรงโมเดล)
-- ถ้าขึ้น Duplicate column ให้ข้ามบรรทัดนั้น

ALTER TABLE debt ADD COLUMN interest_rate_basis VARCHAR(16) NOT NULL DEFAULT 'year';
ALTER TABLE debt ADD COLUMN payment_period VARCHAR(16) NOT NULL DEFAULT 'month';
