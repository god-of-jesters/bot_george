from database import init_db
from repo.user_repo import *
from repo.file_repo import *
import asyncio

async def test():
    got = await get_user(12)
    print("GET =", got)

async def add():
    from entityes.user import User
    #async with aiosqlite.connect("test.db") as db:
    #    await db.execute("DROP TABLE users;")
    #    await db.commit()
    await init_db()
    #user1 = User(user_id=120, fio="Test User", team_number=1, role="Участник", num_badge=123, reiting=0, balance=0, date_registered="2024-01-01 00:00:00")
    user2 = User(user_id=1438564718, fio="Another User", team_number=0, role="Организатор", num_badge=12, reiting=0, balance=0)
    await add_user(user2)
    print("Added")

asyncio.run(add())
