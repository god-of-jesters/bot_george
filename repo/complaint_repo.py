from database import DB_PATH, COMPLAINTS
import aiosqlite
from entityes.complaint import Complaint
from repo.file_repo import get_file, update_file

async def add_complaint(complaint: Complaint):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        INSERT INTO complaints (user_id, adresat, violetion, description, status, execution)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (complaint.user_id, complaint.adresat, complaint.violetion, complaint.description, complaint.status, complaint.execution))
        complaint.complaint_id = cursor.lastrowid
        await db.commit()
        # Update files with complaint_id
        for file_id in complaint.files:
            file = await get_file(file_id)
            if file:
                file.complaint_id = complaint.complaint_id
                await update_file(file)
        COMPLAINTS[complaint.complaint_id] = complaint
        return complaint.complaint_id
        

async def get_complaint(complaint_id: int) -> Complaint | None:
    if complaint_id in COMPLAINTS:
        return COMPLAINTS[complaint_id]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, user_id, adresat, violetion, description, date_created, date_resolved, status, execution "
            "FROM complaints WHERE id = ?;",
            (complaint_id,)
        )
        row = await cursor.fetchone()
        if row:
            # columns: 0=id, 1=user_id, 2=adresat, 3=violetion, 4=description,
            # 5=date_created, 6=date_resolved, 7=status, 8=execution
            complaint = Complaint(
                complaint_id=row[0],
                user_id=row[1],
                adresat=row[2],
                violetion=row[3],
                description=row[4],
                status=row[7],
                execution=row[8],
            )
            complaint.date_created = row[5]
            complaint.date_resolved = row[6]
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
        """, (execution, complaint_id))
        await db.commit()
        COMPLAINTS[complaint_id].execution = execution

async def delete_complaint(complaint_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM complaints WHERE id = ?;", (complaint_id,))
        await db.commit()
        if complaint_id in COMPLAINTS:
            del COMPLAINTS[complaint_id]

async def get_user_complaints(tg_id: int) -> list[Complaint]:
    if not tg_id:
        return []
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, user_id, adresat, violetion, description, date_created, date_resolved, status, execution "
            "FROM complaints WHERE user_id = ?;",
            (tg_id,)
        )
        rows = await cursor.fetchall()
        complaints = []
        for row in rows:
            c = Complaint(
                complaint_id=row["id"],
                user_id=row["user_id"],
                adresat=row["adresat"],
                violetion=row["violetion"],
                description=row["description"],
                status=row["status"],
                execution=row["execution"],
            )
            c.date_created = row["date_created"]
            c.date_resolved = row["date_resolved"]
            complaints.append(c)
        return complaints

async def get_room_problems() -> list[Complaint]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM complaints WHERE status = "room_problems"')
        rows = await cursor.fetchall()
    result = []
    for r in rows:
        c = Complaint(
            complaint_id=r["id"],
            user_id=r["user_id"],
            adresat=r["adresat"],
            violetion=r["violetion"],
            description=r["description"],
            status=r["status"],
            execution=r["execution"],
        )
        c.date_created = r["date_created"]
        c.date_resolved = r["date_resolved"]
        result.append(c)
    return result

async def get_oldest_complaint() -> Complaint:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT *
            FROM complaints
            WHERE execution = "new" AND status = "alert"
            LIMIT 1
        """)
        row = await cur.fetchone()
        if row:
            return Complaint(
                complaint_id=row["id"],
                user_id=row["user_id"],
                adresat=row["adresat"],
                violetion=row["violetion"],
                description=row["description"],
                status=row["status"],
                execution=row["execution"],
            )
        cur = await db.execute("""
            SELECT *
            FROM complaints
            WHERE execution = "new" AND status = "soon"
            LIMIT 1
        """)
        row = await cur.fetchone()
        if row:
            return Complaint(
                complaint_id=row["id"],
                user_id=row["user_id"],
                adresat=row["adresat"],
                violetion=row["violetion"],
                description=row["description"],
                status=row["status"],
                execution=row["execution"],
            )
        cur = await db.execute("""
            SELECT *
            FROM complaints
            WHERE execution = "new"
            LIMIT 1
        """)
        row = await cur.fetchone()
        if row:
            return Complaint(
                complaint_id=row["id"],
                user_id=row["user_id"],
                adresat=row["adresat"],
                violetion=row["violetion"],
                description=row["description"],
                status=row["status"],
                execution=row["execution"],
            )
        return None

async def get_user_complaint_counter(tg_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM complaints_counter
            WHERE user_id = ? AND complaint_id != 0
            """,
            (tg_id,)
        )
        result = await cursor.fetchone()
        return result[0]