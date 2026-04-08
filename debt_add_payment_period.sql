-- MariaDB / MySQL: ความถี่งวดจ่าย (รันครั้งเดียวถ้ายังไม่มีคอลัมน์)
ALTER TABLE debt ADD COLUMN payment_period VARCHAR(16) NOT NULL DEFAULT 'month';
