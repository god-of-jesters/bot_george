from database import DB_PATH, USERS
import aiosqlite
from entityes.user import User

async def add_user(user: User):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT OR IGNORE INTO users (tg_id, fio, role, team_number, num_badge, reiting, balance, date_registered)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (user.user_id, user.fio, user.role, user.team_number, user.badge_number, user.reiting, user.balance, user.date_registered))
        await db.commit()
        USERS[user.user_id] = user

async def get_user(tg_id: int) -> User | None:
    if tg_id in USERS:
        return USERS[tg_id]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT tg_id, fio, team_number, role, num_badge, reiting, balance, date_registered FROM users WHERE tg_id = ?;", (tg_id,))
        row = await cursor.fetchone()
        if row:
            user = User(user_id=row[0], fio=row[1], team_number=row[2], role=row[3], num_badge=row[4], reiting=row[5], balance=row[6], date_registered=row[7])
            USERS[tg_id] = user
            return user
        return None

async def update_user(user: User):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE users
        SET fio = ?, role = ?, team_number = ?, num_badge = ?, reiting = ?, balance = ?, date_registered = ?
        WHERE tg_id = ?;
        """, (user.fio, user.role, user.team_number, user.num_badge, user.reiting, user.balance, user.date_registered, user.user_id))
        await db.commit()
        USERS[user.user_id] = user

async def delete_user(tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE tg_id = ?;", (tg_id,))
        await db.commit()
        if tg_id in USERS:
            del USERS[tg_id]

async def get_user_by_badge(badge_number: int) -> User | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT tg_id, fio, team_number, role, num_badge, reiting, balance, date_registered FROM users WHERE num_badge = ?;", (badge_number,))
        row = await cursor.fetchone()
        if row:
            return User(user_id=row[0], fio=row[1], team_number=row[2], role=row[3], badge_number=row[4], reiting=row[5], balance=row[6])
        return None

async def get_raiting_team_tg() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT tg_id FROM users WHERE role="Команда рейтинга"')
        row = await cursor.fetchall()
        return [i[0] for i in row]