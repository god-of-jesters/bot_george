import aiosqlite
from database import DB_PATH

async def log_login(tg_id: int, badge_number: int | None, role: str | None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO audit_log(event, actor_tg_id, badge_number, role)
            VALUES('login', ?, ?, ?)
        """, (tg_id, badge_number, role))
        await db.commit()


async def log_complaint_created(actor_tg_id: int, adresat_tg_id: int, complaint_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO audit_log(event, actor_tg_id, adresat_tg_id, complaint_id)
            VALUES('complaint_created', ?, ?, ?)
        """, (actor_tg_id, adresat_tg_id, complaint_id))
        await db.commit()


async def log_file_attached(tg_id: int, file_row_id: int, tg_file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO audit_log(event, actor_tg_id, file_row_id, tg_file_id)
            VALUES('complaint_file', ?, ?, ?)
        """, (tg_id, file_row_id, tg_file_id))
        await db.commit()


async def log_complaint_processed(actor_tg_id: int, complaint_id: int, solution: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO audit_log(event, actor_tg_id, complaint_id, solution)
            VALUES('complaint_processed', ?, ?, ?)
        """, (actor_tg_id, complaint_id, solution))
        await db.commit()
