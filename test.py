from database import init_db
from repo.user_repo import *
from repo.file_repo import *
from repo.team_repo import *
from repo.complaint_repo import *
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
    user1 = User(user_id=5732277748, fio="Test User", team_number=1, role="Участник", badge_number=123, reiting=0, balance=0)
    await add_user(user1)
    user2 = User(user_id=1170037101, fio="Another User", team_number=1, role="Участник", badge_number=120, reiting=0, balance=0)
    await add_user(user2)
    user3 = User(user_id=1438564718, fio="Test User", team_number=1, role="Команда рейтинга", badge_number=12, reiting=0, balance=0)
    await add_user(user3)
    print("User added")
    team = Team(team_number=1, team_name="Test Team")
    await add_team(team)
    print("Team added")


async def show_all():
    async with aiosqlite.connect(DB_PATH) as db:
        c = await db.execute("SELECT * FROM users")
        r = await c.fetchall()
        print(r)
        
asyncio.run(show_all())
asyncio.run(get_oldest_complaint())