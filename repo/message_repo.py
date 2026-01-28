from database import DB_PATH, MESSAGES
import aiosqlite
from entityes.message import Message

async def add_message(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO messages (user_id, adresat, text, status, date_created)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                message.user_id,
                message.adresat,
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
            SELECT id, user_id, adresat, text, status, date_created
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
                text=row[3],
                status=row[4],
                date_created=row[5],
            )
            MESSAGES[message_id] = message
            return message
        return None


async def update_message(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE messages
            SET user_id = ?, adresat = ?, text = ?, status = ?, date_created = ?
            WHERE id = ?;
            """,
            (
                message.user_id,
                message.adresat,
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
