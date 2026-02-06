from typing import Optional

import aiosqlite

from entityes.promokod import Promokod
from database import DB_PATH


async def add_promokod(promokod: Promokod) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO promokodes (phrase, amount, bonus, badge_number)
            VALUES (?, ?, ?, ?)
            """,
            (promokod.phrase, promokod.amount, promokod.bonus, promokod.badge_number),
        )
        await db.commit()
        return cursor.lastrowid


async def get_promokod(promokod_id: int) -> Optional[Promokod]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM promokodes WHERE id = ?",
            (promokod_id,),
        )
        row = await cursor.fetchone()

    if not row:
        return None

    return Promokod(
        id=row["id"],
        phrase=row["phrase"],
        amount=row["amount"],
        bonus=row["bonus"],
        badge_number=row["badge_number"],
        date_created=row["date_created"],
    )


async def del_promokod(promokod_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM promokodes WHERE id = ?",
            (promokod_id,),
        )
        await db.commit()
        return cursor.rowcount


async def update_promokod(promokod_id: int, bonus: int, amount: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE promokodes
            SET bonus = ?, amount = ?
            WHERE id = ?
            """,
            (bonus, amount, promokod_id),
        )
        await db.commit()
        return cursor.rowcount

async def get_promo_by_pharse(phrase: str) -> Promokod:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
                """
                SELECT id, amount, bonus, badge_number
                FROM promokodes
                WHERE phrase = ?;
                """,
                (phrase,),
            )
        row = await cur.fetchone()
        if row:
            if row[1] > 0:
                return Promokod(row[0], phrase, row[1], row[2], row[3])
        return
    
async def is_promo_used_by_user(badge_number: int, promo_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT 1
            FROM uses_promo
            WHERE badge_number = ? AND promo_id = ?
            LIMIT 1
            """,
            (badge_number, promo_id),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row is not None

async def mark_promo_as_used(badge_number: int, promo_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO uses_promo (badge_number, promo_id)
            VALUES (?, ?)
            """,
            (badge_number, promo_id),
        )
        await db.commit()
    
async def add_thanks(user: int, fr: int, text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO thanks (badge_number_user, badge_number_from, text, status)
            VALUES (?, ?, ?, "new")
            """,
            (user, fr, text),
        )
        await db.commit()

async def set_gift_status(th_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE thanks
            SET status = ?
            WHERE id = ?
            """,
            (status, th_id),
        )
        await db.commit()

async def get_oldest_request():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, badge_number_user, badge_number_from, text, status
            FROM thanks
            WHERE status IS NULL OR status = '' OR status = 'pending'
            ORDER BY id ASC
            LIMIT 1
            """
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row