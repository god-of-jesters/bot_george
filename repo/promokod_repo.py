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
