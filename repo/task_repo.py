from typing import Optional

import aiosqlite

from entityes.task import Taski
from database import DB_PATH


async def add_task(task: Taski) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO tasks (creator, us, price, bonus, description, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.creator,
                task.us,
                task.price,
                task.bonus,
                task.description,
                task.status,
                task.date_created,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_task(task_id: int) -> Optional[Taski]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = await cursor.fetchone()

    if not row:
        return None

    return Taski(
        id=row["id"],
        description=row["description"] or "",
        price=row["price"] or 0,
        bonus=row["bonus"] or 0,
        status=row["status"],
        creator=row["creator"],
        us=row["us"],
        date_created=row["created_at"],
    )


async def del_task(task_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,),
        )
        await db.commit()
        return cursor.rowcount


async def update_task(task: Taski) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE tasks
            SET creator = ?, us = ?, price = ?, bonus = ?, description = ?, status = ?, created_at = ?
            WHERE id = ?
            """,
            (
                task.creator,
                task.us,
                task.price,
                task.bonus,
                task.description,
                task.status,
                task.date_created,
                task.id,
            ),
        )
        await db.commit()
        return cursor.rowcount


async def get_all_tasks_string() -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, description, price, bonus
            FROM tasks
            WHERE status = "new"
            ORDER BY id
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()

    if not rows:
        return "Заданий пока нет."

    result = []
    for task_id, description, price, bonus in rows:
        result.append(f"{task_id}. Цена: {price}, вознаграждение: {bonus}\n {description}\n")

    return "\n".join(result)

async def get_user_task(badge_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id
            FROM tasks
            WHERE status = "process" AND us = ?
            ORDER BY id
            """, (badge_number, )
        )
        row = await cursor.fetchone()
        if not row:
            return None
        else:
            return row[0]
    
async def get_process_task(i: int) -> Taski:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM tasks WHERE id = ? AND status = ?
            """, (i, 'process'))
        row = await cursor.fetchone()

    if not row:
        return None

    return Taski(
        id=row["id"],
        description=row["description"],
        price=row["price"],
        bonus=row["bonus"],
        status=row["status"],
        us=row['us'],
        creator=row["creator"],
        date_created=row["created_at"],
    )