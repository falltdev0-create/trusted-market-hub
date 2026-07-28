"""
backend/create_admin.py — Create or upgrade the first super_admin.

Usage:
    python backend/create_admin.py --email admin@moamalati.local --password 'Admin@12345' --name 'Super Admin'
"""
import argparse, asyncio, sys, uuid
from sqlalchemy import text

sys.path.insert(0, ".")
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password


async def run(email: str, password: str, name: str, phone: str):
    async with AsyncSessionLocal() as db:
        row = (await db.execute(text("SELECT id FROM users WHERE email = :e"), {"e": email})).first()
        if row:
            uid = row[0]
            await db.execute(text("UPDATE users SET password_hash=:p, kyc_status='verified', is_active=1 WHERE id=:id"),
                             {"p": hash_password(password), "id": uid})
        else:
            uid = str(uuid.uuid4())
            await db.execute(text("""INSERT INTO users (id, full_name, email, phone, password_hash, kyc_status, is_active, created_at)
                VALUES (:id, :n, :e, :ph, :p, 'verified', 1, NOW())"""),
                {"id": uid, "n": name, "e": email, "ph": phone, "p": hash_password(password)})

        arow = (await db.execute(text("SELECT id FROM admins WHERE user_id = :u"), {"u": uid})).first()
        if arow:
            await db.execute(text("UPDATE admins SET role='super_admin', is_active=1 WHERE id=:id"), {"id": arow[0]})
        else:
            await db.execute(text("INSERT INTO admins (id, user_id, role, is_active, created_at) VALUES (:id, :u, 'super_admin', 1, NOW())"),
                             {"id": str(uuid.uuid4()), "u": uid})
        await db.commit()
        print(f"✅ super_admin ready: {email}  (user_id={uid})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default="admin@moamalati.local")
    ap.add_argument("--password", default="Admin@12345")
    ap.add_argument("--name", default="Super Admin")
    ap.add_argument("--phone", default="000000000")
    a = ap.parse_args()
    asyncio.run(run(a.email, a.password, a.name, a.phone))
