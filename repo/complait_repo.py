from database import DB_PATH
import aiosqlite
from entityes.complait import Complaint

async def add_complaint(complaint: Complaint):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO complaints (user_id, title, description, date_created, status)
        VALUES (?, ?, ?, ?, ?);
        """, (complaint.user_id, complaint.title, complaint.description, complaint.date_created, complaint.status))
        await db.commit()