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
    user1 = User(tg_id=5732277748, fio="Тест 1", team_number=10, role="Участник", gender='Ж', badge_number=999, reiting=0, balance=0)
    await add_user(user1)
    user3 = User(tg_id=1438564718, fio="Тест 2", team_number=10, role="Участник", gender='М', badge_number=998, reiting=0, balance=0)
    await add_user(user3)
    user2 = User(tg_id=1438564719, fio="Дмитрий", team_number=10, role="Рейтинг", gender='М', badge_number=99, reiting=0, balance=0)
    await add_user(user2)
    team = Team(team_number=1, team_name="VФактор")
    team2 = Team(team_number=2, team_name="ИИдиллия")
    team3 = Team(team_number=3, team_name="С.К.Р.")
    team4 = Team(team_number=4, team_name="НЭА")
    team5 = Team(team_number=5, team_name="МоделИ РеальностИ")
    team6 = Team(team_number=6, team_name="Рефлекс")
    team7 = Team(team_number=7, team_name="Квантор")
    team8 = Team(team_number=8, team_name="Нейротонин")
    team9 = Team(team_number=9, team_name="БAiТ")
    team10 = Team(team_number=10, team_name="Тестеры")
    await add_team(team)
    await add_team(team2)
    await add_team(team3)
    await add_team(team4)
    await add_team(team5)
    await add_team(team6)
    await add_team(team7)
    await add_team(team8)
    await add_team(team9)
    await add_team(team10)

async def show_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        c = await db.execute("SELECT * FROM users WHERE badge_number = ?", (124, ))
        r = await c.fetchall()
        print(r)

async def show_all_files():
    async with aiosqlite.connect(DB_PATH) as db:
        c = await db.execute("SELECT * FROM files")
        r = await c.fetchall()
        print(r)

async def show_all_complaints():
    async with aiosqlite.connect(DB_PATH) as db:
        c = await db.execute("SELECT * FROM complaints")
        r = await c.fetchall()
        print(r)

async def show_all_reiting():
    async with aiosqlite.connect(DB_PATH) as db:
        c = await db.execute("SELECT * FROM ratings")
        r = await c.fetchall()
        print(r)

async def get():
    us = await get_user(1170037101)
    u = await get_user_by_badge(0)
    print(us.gender)
    print(u.gender)


async def show_all_thanks():
    async with aiosqlite.connect(DB_PATH) as db:
        c = await db.execute("SELECT * FROM ratings")
        r = await c.fetchall()
        print(r)

async def full_ratings():
    users = await get_all_users()
    print(users[10].fio)
    async with aiosqlite.connect(DB_PATH) as db:
        for user in users:
            if user.role == 'Участник':
                await db.execute(
                    """INSERT INTO ratings(badge_number, full_name, team_id, updated_at) VALUES(?, ?, ?, ?);""", (user.badge_number, user.fio, user.badge_number//100, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                await db.commit()

async def drop(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"DROP TABLE IF EXISTS {name}")
        await db.commit()

async def del_pait():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"DELETE FROM sons WHERE parent=121 AND son=318")
        await db.commit()

#asyncio.run(drop("isks"))
#asyncio.run(drop("sons"))
#asyncio.run(drop("ratings"))
#asyncio.run(get())
#asyncio.run(add())
#asyncio.run(full_ratings())
#asyncio.run(show_all_thanks())
asyncio.run(del_pait())