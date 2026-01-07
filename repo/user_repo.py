from database import DB_PATH
import aiosqlite
from entityes.user import User

async def add_user(user: User):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT OR IGNORE INTO users (tg_id, fio, role, team_number, num_badge, date_registered)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (user.user_id, user.fio, user.role, user.team_number, user.num_badge, user.date_registered))
        await db.commit()

async def get_user(tg_id: int) -> User | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT tg_id, fio, team_number, role, num_badge, date_registered FROM users WHERE tg_id = ?;", (tg_id,))
        row = await cursor.fetchone()
        if row:
            return User(user_id=row[0], fio=row[1], team_number=row[2], role=row[3], num_badge=row[4], date_registered=row[5])
        return None

async def update_user(user: User):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE users
        SET fio = ?, role = ?, team_number = ?, num_badge = ?, date_registered = ?
        WHERE tg_id = ?;
        """, (user.fio, user.role, user.team_number, user.num_badge, user.date_registered, user.user_id))
        await db.commit()

async def delete_user(tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE tg_id = ?;", (tg_id,))
        await db.commit()
