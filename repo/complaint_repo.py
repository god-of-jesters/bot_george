from database import DB_PATH, COMPLAINTS
import aiosqlite
from entityes.complaint import Complaint
from repo.file_repo import get_file, update_file

async def add_complaint(complaint: Complaint):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        INSERT INTO complaints (user_id, adresat, description, status, execution)
        VALUES (?, ?, ?, ?, ?);
        """, (complaint.user_id, complaint.adresat, complaint.description, complaint.status, complaint.execution))
        complaint.complaint_id = cursor.lastrowid
        await db.commit()
        # Update files with complaint_id
        for file_id in complaint.files:
            file = await get_file(file_id)
            if file:
                file.complaint_id = complaint.complaint_id
                await update_file(file)
        COMPLAINTS[complaint.complaint_id] = complaint
        print("Добавил жалобу")

async def get_complaint(complaint_id: int) -> Complaint | None:
    if complaint_id in COMPLAINTS:
        return COMPLAINTS[complaint_id]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, user_id, adresat, violetion, description, date_created, date_resolved, status, execution FROM complaints WHERE id = ?;", (complaint_id,))
        row = await cursor.fetchone()
        if row:
            complaint = Complaint(complaint_id=row[0], user_id=row[1], adresat=row[2], violetion=row[3], description=row[4], date_created=row[5], date_resolved=[6], status=row[7], execution=row[8])
            complaint.date_created = row[4]
            complaint.date_resolved = row[5]
            # Load files
            from repo.file_repo import get_files_by_complaint
            files = await get_files_by_complaint(complaint_id)
            complaint.files = [f.file_id for f in files]
            return complaint
        return None

async def update_complaint(complaint: Complaint):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE complaints
        SET user_id = ?, adresat = ?, violetion = ?, description = ?, date_resolved = ?, status = ?, execution = ?
        WHERE id = ?;
        """, (complaint.user_id, complaint.adresat, complaint.violetion, complaint.description, complaint.date_resolved, complaint.status, complaint.execution, complaint.complaint_id))
        await db.commit()
        COMPLAINTS[complaint.complaint_id] = complaint

async def update_execution(complaint_id, execution):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE complaints
        SET execution = ?
        WHERE id = ?;
        """, (complaint_id, execution))
        await db.commit()
        COMPLAINTS[complaint_id].execution = execution

async def delete_complaint(complaint_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM complaints WHERE id = ?;", (complaint_id,))
        await db.commit()
        if complaint_id in COMPLAINTS:
            del COMPLAINTS[complaint_id]

async def get_user_complaints(user_id: int) -> list[Complaint]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM complaints WHERE user_id=?", (user_id))
        row = await cursor.fetchall()
        return [Complaint(row[0], )]
    
async def get_oldest_complaint() -> Complaint:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT *
            FROM complaints
            WHERE status IN ('alert', 'soon', 'other_issues') AND execution == "new" 
            ORDER BY
              CASE status
                WHEN 'alert' THEN 1
                WHEN 'soon' THEN 2
                WHEN 'other_issues' THEN 3  
                ELSE 99
              END,
              date_created ASC,
              id ASC
            LIMIT 1
        """)
        row = await cur.fetchone()
        print(row)
        return row