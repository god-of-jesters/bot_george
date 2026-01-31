from sqlite3 import connect
from database import DB_PATH, USERS
import aiosqlite
from entityes.user import User

async def add_user(user: User):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT OR IGNORE INTO users (tg_id, fio, role, team_number, badge_number, reiting, balance, date_registered)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (user.user_id, user.fio, user.role, user.team_number, user.badge_number, user.reiting, user.balance, user.date_registered))
        await db.commit()
        USERS[user.user_id] = user

async def get_user(tg_id: int) -> User | None:
    if tg_id in USERS:
        return USERS[tg_id]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT tg_id, fio, team_number, role, badge_number, reiting, balance, date_registered FROM users WHERE tg_id = ?;", (tg_id,))
        row = await cursor.fetchone()
        if row:
            user = User(user_id=row[0], fio=row[1], team_number=row[2], role=row[3], badge_number=row[4], reiting=row[5], balance=row[6], date_registered=row[7])
            USERS[tg_id] = user
            return user
        return None
    
async def get_all_users() -> list[User]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT tg_id, fio, team_number, role, badge_number, reiting, balance, date_registered FROM users;")
        rows = await cursor.fetchall()
        users = []
        for row in rows:
            user = User(user_id=row[0], fio=row[1], team_number=row[2], role=row[3], badge_number=row[4], reiting=row[5], balance=row[6], date_registered=row[7])
            users.append(user)
        return users

async def update_user(user: User):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE users
        SET fio = ?, role = ?, team_number = ?, badge_number = ?, reiting = ?, balance = ?, date_registered = ?
        WHERE tg_id = ?;
        """, (user.fio, user.role, user.team_number, user.badge_number, user.reiting, user.balance, user.date_registered, user.user_id))
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
        cursor = await db.execute("SELECT tg_id, fio, team_number, role, badge_number, reiting, balance, date_registered FROM users WHERE badge_number = ?;", (badge_number,))
        row = await cursor.fetchone()
        if row:
            return User(user_id=row[0], fio=row[1], team_number=row[2], role=row[3], badge_number=row[4], reiting=row[5], balance=row[6])
        return None

async def get_raiting_team_tg() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT tg_id FROM users WHERE role="Команда рейтинга"')
        row = await cursor.fetchall()
        return [i[0] for i in row]

async def get_active_users() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT user_id FROM active')
        row = await cursor.fetchall()
        return [i[0] for i in row]

async def add_active(user_id: int, role: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('INSERT INTO active VALUES(?, ?)', (user_id, role))
        await db.commit()

async def get_roles_stats_message() -> str:
    ROLE_TITLES = {
        "participant": "Участники",
        "organizer": "Организаторы",
        "rating_team": "Команда рейтинга",
        "rpg_organizers": "РПГ",
        "room_administrators": "Администраторы по комнатам",
        "media_team": "Медиа",
        "chief_organizer": "Главный организатор",
    }
    
    roles_order = [
        "participant",
        "rating_team",
        "organizer",
        "rpg_organizers",
        "room_administrators",
        "media_team",
        "chief_organizer",
    ]

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT role, COUNT(*) as n
            FROM users
            GROUP BY role;
        """)
        users_counts = {row[0]: row[1] for row in await cursor.fetchall()}

        cursor = await db.execute("""
            SELECT role, COUNT(*) as g
            FROM active
            GROUP BY role;
        """)
        active_counts = {row[0]: row[1] for row in await cursor.fetchall()}

    lines = []
    for role in roles_order:
        title = ROLE_TITLES.get(role, role)
        n = users_counts.get(role, 0)
        g = active_counts.get(role, 0)
        lines.append(f"{title}: {n} | активные: {g}")

    return "\n".join(lines)

async def get_participants_tg_ids(exclude_tg_id: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT tg_id FROM users WHERE role = ? AND tg_id != ?;",
            ("Участник", exclude_tg_id),
        )
        rows = await cursor.fetchall()
    return [r[0] for r in rows]

async def get_participants_and_room_admins_tg_ids(exclude_tg_id: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT DISTINCT tg_id
            FROM users
            WHERE role IN (?, ?) AND tg_id != ?;
            """,
            ("Участник", "Администраторы по комнатам", exclude_tg_id),
        )
        rows = await cursor.fetchall()
    return [r[0] for r in rows]

async def get_permission_maling(badge_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT maling FROM permissions WHERE badge_number = ?",
            (badge_number, )
        )
        row = await cursor.fetchone()
    return True if row == 1 else False
