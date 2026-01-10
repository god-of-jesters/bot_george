from database import DB_PATH
import aiosqlite
from entityes.complait import Complaint

async def add_complaint(complaint: Complaint):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO complaints (user_id, title, description, date_created, status, files)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (complaint.user_id, complaint.title, complaint.description, complaint.date_created, complaint.status, complaint.files))
        await db.commit()

async def get_complaint(complait_id: int) -> Complaint | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT complait_id, user_id, title, description, date_created, status FROM complaints WHERE complait_id = ?;", (complait_id,))
        row = await cursor.fetchone()
        if row:
            return Complaint(complait_id=row[0], user_id=row[1], title=row[2], description=row[3], date_created=row[4], status=row[5])
        return None
