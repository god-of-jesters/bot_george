from database import DB_PATH, COMPLAINTS
import aiosqlite
from entityes.complaint import Complaint

async def add_complaint(complaint: Complaint):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO complaints (user_id, title, description, date_created, status, files)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (complaint.user_id, complaint.title, complaint.description, complaint.date_created, complaint.status, complaint.files))
        await db.commit()
        COMPLAINTS[complaint.complait_id] = complaint

async def get_complaint(complait_id: int) -> Complaint | None:
    if complait_id in COMPLAINTS:
        return COMPLAINTS[complait_id]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT complait_id, user_id, title, description, date_created, status FROM complaints WHERE complait_id = ?;", (complait_id,))
        row = await cursor.fetchone()
        if row:
            return Complaint(complait_id=row[0], user_id=row[1], title=row[2], description=row[3], date_created=row[4], status=row[5])
        return None

async def update_complaint(complaint: Complaint):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE complaints
        SET user_id = ?, title = ?, description = ?, date_created = ?, status = ?
        WHERE complait_id = ?;
        """, (complaint.user_id, complaint.title, complaint.description, complaint.date_created, complaint.status, complaint.complait_id))
        await db.commit()
        COMPLAINTS[complaint.complait_id] = complaint

async def delete_complaint(complait_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM complaints WHERE complait_id = ?;", (complait_id,))
        await db.commit()
        if complait_id in COMPLAINTS:
            del COMPLAINTS[complait_id]
