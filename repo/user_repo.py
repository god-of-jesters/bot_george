from sqlite3 import connect
from database import DB_PATH, USERS
import aiosqlite
from entityes.user import User

async def add_user(user: User):
    """
    Добавляет нового пользователя, если в системе ещё нет
    ни такого же badge_number
    """
    # защита от повторной вставки одного и того же человека
    if user.badge_number is not None and await get_user_by_badge(user.badge_number):
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (
                tg_id, username, fio, role, team_number,
                badge_number, reiting, balance, gender, date_registered
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user.tg_id,
                user.username,
                user.fio,
                user.role,
                user.team_number,
                user.badge_number,
                user.reiting,
                user.balance,
                user.gender,
                user.date_registered,
            ),
        )
        await db.commit()
        USERS[user.tg_id] = user

async def get_user(tg_id: int) -> User | None:
    if tg_id in USERS:
        return USERS[tg_id]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT tg_id, username, fio, team_number, role, badge_number, reiting, balance, gender, date_registered FROM users",
            (tg_id,),
        )
        row = await cursor.fetchone()
        if row:
            user = User(
                tg_id=row[0],
                username=row[1],
                fio=row[2],
                team_number=row[3],
                role=row[4],
                badge_number=row[5],
                reiting=row[6],
                balance=row[7],
                gender=row[8],
                date_registered=row[9],
            )
            USERS[tg_id] = user
            return user
        return None
    
async def get_all_users() -> list[User]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT tg_id, username, fio, team_number, role, badge_number, reiting, balance, gender, date_registered FROM users;"
        )
        rows = await cursor.fetchall()
        users = []
        for row in rows:
            user = User(
                tg_id=row[0],
                username=row[1],
                fio=row[2],
                team_number=row[3],
                role=row[4],
                badge_number=row[5],
                reiting=row[6],
                balance=row[7],
                gender=row[8],
                date_registered=row[9],
            )
            users.append(user)
        return users

async def update_user(user: User):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE users
        SET tg_id = ?, username = ?, fio = ?, role = ?, team_number = ?, reiting = ?, balance = ?, gender = ?, date_registered = ?
        WHERE badge_number = ?;
        """, (
            user.tg_id,
            user.username,
            user.fio,
            user.role,
            user.team_number,
            user.reiting,
            user.balance,
            user.gender,
            user.date_registered,
            user.badge_number,
        ))
        await db.commit()
        USERS[user.tg_id] = user

async def upsert_users_rows(rows: list[dict]) -> int:
    if not rows:
        return 0

    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            """
            INSERT INTO users (tg_id, username, fio, role, team_number, badge_number, reiting, balance, date_registered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tg_id) DO UPDATE SET
                username=excluded.username,
                fio=excluded.fio,
                role=excluded.role,
                team_number=excluded.team_number,
                badge_number=excluded.badge_number,
                reiting=excluded.reiting,
                balance=excluded.balance,
                gender=excluded.balance,
                date_registered=excluded.date_registered
            """,
            [
                (
                    r["tg_id"],
                    r.get("username"),
                    r["fio"],
                    r["role"],
                    r["team_number"],
                    r["badge_number"],
                    r["reiting"],
                    r["balance"],
                    r['genger'],
                    r["date_registered"],
                )
                for r in rows
            ],
        )
        await db.commit()

    for r in rows:
        USERS[r["tg_id"]] = User(
            tg_id=r["tg_id"],
            username=r.get("username"),
            fio=r["fio"],
            team_number=r["team_number"],
            role=r["role"],
            badge_number=r["badge_number"],
            reiting=r["reiting"],
            balance=r["balance"],
            gender=r["gender"],
            date_registered=r["date_registered"],
        )

    return len(rows)

async def delete_user(badge_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE badge_number = ?;", (badge_number,))
        await db.commit()

async def get_user_by_badge(badge_number: int) -> User | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT tg_id, username, fio, team_number, role, badge_number, reiting, balance, gender, date_registered "
            "FROM users WHERE badge_number = ?;",
            (badge_number,),
        )
        row = await cursor.fetchone()
        if row:
            return User(
                tg_id=row[0],
                username=row[1],
                fio=row[2],
                team_number=row[3],
                role=row[4],
                badge_number=row[5],
                reiting=row[6],
                balance=row[7],
                gender=row[8],
                date_registered=row[9],
            )
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

async def update_tg_id(badge_number: int, tg: int, username: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE users SET tg_id=Null WHERE tg_id = ?",
            (tg, )
        )
        cursor = await db.execute(
            "UPDATE users SET tg_id=?, username=? WHERE badge_number = ?",
            (tg, username, badge_number,)
        )
        await db.commit()
    USERS[tg] = await get_user_by_badge(badge_number)

async def get_user_by_fio(fio: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT tg_id, team_number, role, badge_number, reiting, balance, gender, date_registered FROM users WHERE fio = ?;"
        )
        row = await cursor.fetchone()
    if row:
        return User(tg_id=row[0], fio=fio, team_number=row[1], role=row[2], badge_number=row[3], reiting=row[4], balance=row[5], gender=row[6], date_registered=row[7])
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

async def add_rating(badge_number: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("UPDATE ratings SET total_points = total_points + ? WHERE badge_number = ?;", (amount, badge_number))
        cursor = await db.execute("UPDATE ratings SET bonuses_sum = bonuses_sum + ? WHERE badge_number = ?;", (amount, badge_number))
        await db.commit()

async def subtract_rating(badge_number: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("UPDATE ratings SET total_points = total_points - ? WHERE badge_number = ?;", (amount, badge_number))
        cursor = await db.execute("UPDATE ratings SET penalties_sum = penalties_sum + ? WHERE badge_number = ?;", (amount, badge_number))
        await db.commit()

async def update_reiting(badge_number: int, amount: int):
    """
    Отнимает рейтинг у пользователя с указанным номером бейджа
    и синхронно обновляет таблицу ratings, работая напрямую через SQL.
    """
    if amount <= 0:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        # уменьшаем рейтинг пользователя в таблице users
        await db.execute(
            "UPDATE users SET reiting = COALESCE(reiting, 0) - ? WHERE badge_number = ?;",
            (amount, badge_number),
        )
        # обновляем агрегированную таблицу рейтингов
        await db.execute(
            "UPDATE ratings "
            "SET total_points = total_points - ?, penalties_sum = penalties_sum + ? "
            "WHERE badge_number = ?;",
            (amount, amount, badge_number),
        )
        await db.commit()

async def del_from_active(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM active WHERE user_id = ?;", (user_id, ))
        await db.commit()

async def get_admins() -> list[User]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE role = ?;",
            ("Администратор",),
        )
        rows = await cursor.fetchall()

    return [
        User(
            tg_id=row["tg_id"],
            username=row["username"],
            fio=row["fio"],
            team_number=row["team_number"],
            role=row["role"],
            badge_number=row["badge_number"],
            reiting=row["reiting"],
            balance=row["balance"],
            gender=row["gender"],
            date_registered=row["date_registered"],
        )
        for row in rows
    ]

async def add_bonus(badge_number: int, bonus: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users "
            "SET balance = balance + ? "
            "WHERE badge_number = ?;",
            (bonus, badge_number),
        )
        await db.commit()

async def buy_product(cost: int, badge_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users "
            "SET balance = balance - ? "
            "WHERE badge_number = ?;",
            (cost, badge_number),
        )
        await db.commit()

async def get_rpg_users() -> list[User]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT * FROM users WHERE role = ?;',
            ('РПГ',),
        )
        rows = await cursor.fetchall()

    return [
        User(
            tg_id=row["tg_id"],
            username=row["username"],
            fio=row["fio"],
            team_number=row["team_number"],
            role=row["role"],
            badge_number=row["badge_number"],
            reiting=row["reiting"],
            balance=row["balance"],
            gender=row["gender"],
            date_registered=row["date_registered"],
        )
        for row in rows
    ]

async def get_user_balance(badge_number: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT balance FROM users WHERE badge_number = ?;",
            (badge_number,),
        )
        row = await cursor.fetchone()

    if not row:
        return None

    return row[0]