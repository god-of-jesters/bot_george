from database import DB_PATH
import aiosqlite
from entityes.file import File

async def add_file(file: File):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO files (tg_id, tg_file_id, file_name, mime_type, file_size)
        VALUES (?, ?, ?, ?, ?);
        """, (file.file_tg_id, file.file_tg_file_id, file.file_name, file.mime_type, file.file_size))
        await db.commit()

async def get_file(file_id: int) -> File | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, tg_id, tg_file_id, file_name, mime_type, file_size, created_at FROM files WHERE id = ?;", (file_id,))
        row = await cursor.fetchone()
        if row:
            return File(id=row[0], tg_id=row[1], tg_file_id=row[2], file_name=row[3], mime_type=row[4], file_size=row[5], date_created=row[6])
        return None

async def update_file(file: File):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE files
        SET tg_file_id = ?, file_name = ?, mime_type = ?, file_size = ?
        WHERE id = ?;
        """, (file.file_tg_file_id, file.file_name, file.mime_type, file.file_size, file.file_id))
        await db.commit()

async def delete_file(file_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM files WHERE id = ?;", (file_id,))
        await db.commit()