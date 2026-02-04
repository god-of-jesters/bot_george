from database import DB_PATH, MESSAGES
import aiosqlite
from entityes.message import Message
from datetime import datetime, timedelta

async def add_message(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO messages (user_id, adresat, badge_number, text, status, date_created)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                message.user_id,
                message.adresat,
                message.badge_number,
                message.text,
                message.status,
                message.date_created,
            ),
        )
        await db.commit()
        message.id = cursor.lastrowid
        MESSAGES[message.id] = message


async def get_message(message_id: int) -> Message | None:
    if message_id in MESSAGES:
        return MESSAGES[message_id]

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, user_id, adresat, badge_number, text, status, date_created
            FROM messages
            WHERE id = ?;
            """,
            (message_id,),
        )
        row = await cursor.fetchone()
        if row:
            message = Message(
                id=row[0],
                user_id=row[1],
                adresat=row[2],
                badge_number=row[3],
                text=row[4],
                status=row[5],
                date_created=row[6],
            )
            MESSAGES[message_id] = message
            return message
        return None


async def update_message(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE messages
            SET user_id = ?, adresat = ?, badge_number = ?, text = ?, status = ?, date_created = ?
            WHERE id = ?;
            """,
            (
                message.user_id,
                message.adresat,
                message.badge_number,
                message.text,
                message.status,
                message.date_created,
                message.id,
            ),
        )
        await db.commit()
        MESSAGES[message.id] = message


async def delete_message(message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM messages WHERE id = ?;",
            (message_id,),
        )
        await db.commit()
        if message_id in MESSAGES:
            del MESSAGES[message_id]

async def get_new_messages() -> list[Message]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT * FROM messages WHERE status = "new"'
        )
        rows = await cursor.fetchall()
    return [
        Message(
            id=row['id'],
            user_id=row['user_id'],
            adresat=row['adresat'],
            badge_number=row['badge_number'],
            text=row['text']
        )
        for row in rows
    ]

async def get_latest_message_by_user(user_id: int) -> Message | None:
    """
    Получить самое позднее сообщение для конкретного пользователя (по user_id).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM messages
            WHERE user_id = ?
            ORDER BY date_created DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = await cursor.fetchone()

    if not row:
        return None

    return Message(
        id=row["id"],
        user_id=row["user_id"],
        adresat=row["adresat"],
        badge_number=row["badge_number"],
        text=row["text"],
        status=row["status"],
        date_created=row["date_created"],
    )

async def update_status(id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE messages SET status = ? WHERE id = ?', (status, id, )
        )
        await db.commit()
    
async def update_status_skip_new():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE messages SET status = "new" WHERE status = "skip"'
        )
        await db.commit()

def _parse_sqlite_dt(s: str) -> datetime | None:
    if not s:
        return None
    # SQLite datetime('now') обычно даёт "YYYY-MM-DD HH:MM:SS"
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass
    # если вдруг ISO
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None

async def get_message_access(user_id: int, minutes: int = 30) -> bool:
    last_msg = await get_latest_message_by_user(user_id)
    if not last_msg or not last_msg.date_created:
        return True

    last_dt = _parse_sqlite_dt(last_msg.date_created)
    if not last_dt:
        return True

    return datetime.now() - last_dt >= timedelta(minutes=minutes)