from sqlite3 import connect
from database import DB_PATH, USERS
import aiosqlite
from entityes.user import User

async def add_user(user: User):
    if not await get_user_by_badge(user.badge_number):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
            INSERT OR IGNORE INTO users (tg_id, fio, role, team_number, badge_number, reiting, balance, date_registered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (user.tg_id, user.fio, user.role, user.team_number, user.badge_number, user.reiting, user.balance, user.date_registered))
            await db.commit()
            USERS[user.tg_id] = user

async def get_user(tg_id: int) -> User | None:
    if tg_id in USERS:
        return USERS[tg_id]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT tg_id, fio, team_number, role, badge_number, reiting, balance, date_registered FROM users WHERE tg_id = ?;", (tg_id,))
        row = await cursor.fetchone()
        if row:
            user = User(tg_id=row[0], fio=row[1], team_number=row[2], role=row[3], badge_number=row[4], reiting=row[5], balance=row[6], date_registered=row[7])
            USERS[tg_id] = user
            return user
        return None
    
async def get_all_users() -> list[User]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT tg_id, fio, team_number, role, badge_number, reiting, balance, date_registered FROM users;")
        rows = await cursor.fetchall()
        users = []
        for row in rows:
            user = User(tg_id=row[0], fio=row[1], team_number=row[2], role=row[3], badge_number=row[4], reiting=row[5], balance=row[6], date_registered=row[7])
            users.append(user)
        return users

async def update_user(user: User):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE users
        SET tg_id = ?, fio = ?, role = ?, team_number = ?, reiting = ?, balance = ?, date_registered = ?
        WHERE badge_number = ?;
        """, (user.tg_id, user.fio, user.role, user.team_number, user.reiting, user.balance, user.date_registered, user.badge_number))
        await db.commit()
        USERS[user.tg_id] = user

async def upsert_users_rows(rows: list[dict]) -> int:
    if not rows:
        return 0

    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            """
            INSERT INTO users (tg_id, fio, role, team_number, badge_number, reiting, balance, date_registered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tg_id) DO UPDATE SET
                fio=excluded.fio,
                role=excluded.role,
                team_number=excluded.team_number,
                badge_number=excluded.badge_number,
                reiting=excluded.reiting,
                balance=excluded.balance,
                date_registered=excluded.date_registered
            """,
            [
                (
                    r["tg_id"],
                    r["fio"],
                    r["role"],
                    r["team_number"],
                    r["badge_number"],
                    r["reiting"],
                    r["balance"],
                    r["date_registered"],
                )
                for r in rows
            ],
        )
        await db.commit()

    for r in rows:
        USERS[r["tg_id"]] = User(
            tg_id=r["tg_id"],
            fio=r["fio"],
            team_number=r["team_number"],
            role=r["role"],
            badge_number=r["badge_number"],
            reiting=r["reiting"],
            balance=r["balance"],
            date_registered=r["date_registered"],
        )

    return len(rows)

async def delete_user(badge_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE badge_number = ?;", (badge_number,))
        await db.commit()

async def get_user_by_badge(badge_number: int) -> User | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT tg_id, fio, team_number, role, badge_number, reiting, balance, date_registered FROM users WHERE badge_number = ?;", (badge_number,))
        row = await cursor.fetchone()
        if row:
            return User(tg_id=row[0], fio=row[1], team_number=row[2], role=row[3], badge_number=row[4], reiting=row[5], balance=row[6])
        return None

async def get_raiting_team_tg() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT tg_id FROM users WHERE role="Рейтинг" AND tg_id NOT NULL')
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
    roles_order = [
        "Участник",
        "Организатор",
        "Рейтинг",
        "Администратор", 
        "Медиа"
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
        n = users_counts.get(role, 0)
        g = active_counts.get(role, 0)
        lines.append(f"{role}: {n} | активные: {g}")

    return "\n".join(lines)

async def get_participants_user_ids(exclude_tg_id: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT tg_id FROM users WHERE role = ? AND tg_id != ? AND tg_id NOT NULL;",
            ("Участник", exclude_tg_id),
        )
        rows = await cursor.fetchall()
    return [r[0] for r in rows]

async def get_participants_and_room_admins_user_ids(exclude_tg_id: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT DISTINCT tg_id
            FROM users
            WHERE role IN (?, ?) AND tg_id != ? AND tg_id NOT NULL;
            """,
            ("Участник", "Администратор", exclude_tg_id),
        )
        rows = await cursor.fetchall()
    return [r[0] for r in rows]

async def update_tg_id(badge_number: int, tg: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE users SET tg_id=Null WHERE tg_id = ?",
            (tg, )
        )
        cursor = await db.execute(
            "UPDATE users SET tg_id=? WHERE badge_number = ?",
            (tg, badge_number,)
        )
        await db.commit()
    USERS[tg] = await get_user_by_badge(badge_number)

async def get_user_by_fio(fio: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT tg_id, team_number, role, badge_number, reiting, balance, date_registered FROM users WHERE fio = ?;"
        )
        row = await cursor.fetchone()
    if row:
        return User(tg_id=row[0], fio=fio, team_number=row[1], role=row[2], badge_number=row[3], reiting=row[4], balance=row[5], date_registered=row[6])
    else:
        return None

async def get_users_by_team(team_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE team_number = ?",
            (team_number,)
        )
        rows = await cursor.fetchall()

    return [
        User(
            tg_id=row["tg_id"],
            fio=row["fio"],
            role=row["role"],
            team_number=row["team_number"],
            badge_number=row["badge_number"],
            reiting=row["reiting"],
            balance=row["balance"],
            date_registered=row["date_registered"],
        )
        for row in rows
    ]