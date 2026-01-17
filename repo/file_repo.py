from database import DB_PATH, FILES
import aiosqlite
from entityes.file import File

async def add_file(file: File):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        INSERT INTO files (tg_id, tg_file_id, complaint_id, file_name, mime_type, file_size)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (file.tg_id, file.tg_file_id, file.complaint_id, file.file_name, file.mime_type, file.file_size))
        file.file_id = cursor.lastrowid
        await db.commit()
        FILES[file.file_id] = file

async def get_file(file_id: int) -> File | None:
    if file_id in FILES:
        return FILES[file_id]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, tg_id, tg_file_id, complaint_id, file_name, mime_type, file_size, created_at FROM files WHERE id = ?;", (file_id,))
        row = await cursor.fetchone()
        if row:
            return File(id=row[0], tg_id=row[1], tg_file_id=row[2], complaint_id=row[3], file_name=row[4], mime_type=row[5], file_size=row[6], date_created=row[7])
        return None

async def update_file(file: File):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE files
        SET tg_file_id = ?, complaint_id = ?, file_name = ?, mime_type = ?, file_size = ?
        WHERE id = ?;
        """, (file.tg_file_id, file.complaint_id, file.file_name, file.mime_type, file.file_size, file.file_id))
        await db.commit()
        FILES[file.file_id] = file

async def delete_file(file_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM files WHERE id = ?;", (file_id,))
        await db.commit()
        if file_id in FILES:
            del FILES[file_id]

async def get_files_by_complaint(complaint_id: int) -> list[File]:
    files = []
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, tg_id, tg_file_id, complaint_id, file_name, mime_type, file_size, created_at FROM files WHERE complaint_id = ?;", (complaint_id,))
        rows = await cursor.fetchall()
        for row in rows:
            file = File(id=row[0], tg_id=row[1], tg_file_id=row[2], complaint_id=row[3], file_name=row[4], mime_type=row[5], file_size=row[6], date_created=row[7])
            files.append(file)
    return files

async def get_files_by_complaint_id(complaint_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT id, tg_file_id, mime_type, file_name
            FROM files
            WHERE complaint_id = ?
            ORDER BY created_at ASC, id ASC
        """, (complaint_id,))
        return await cur.fetchall()
    
async def link_files_to_complaint(complaint_id: int, file_ids: list[int]) -> None:
    if not file_ids:
        return

    placeholders = ",".join("?" for _ in file_ids)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE files SET complaint_id = ? WHERE id IN ({placeholders})",
            (complaint_id, *file_ids)
        )
        await db.commit()