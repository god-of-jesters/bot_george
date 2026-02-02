from database import DB_PATH, MESSAGES
import aiosqlite
from entityes.message import Message

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

async def update_status(id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE messages SET status = "answered" WHERE id = ?', (id, )
        )
        await db.commit()