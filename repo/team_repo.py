from database import DB_PATH
import aiosqlite
from entityes.team import Team

async def add_team(team: Team):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO teams (team_number, team_name)
        VALUES (?, ?);
        """, (team.team_number, team.team_name))
        await db.commit()

async def get_team(team_number: int) -> Team | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT team_number, team_name FROM teams WHERE team_number = ?;", (team_number,))
        row = await cursor.fetchone()
        if row:
            return Team(team_number=row[0], team_name=row[1])
        return None

async def update_team(team: Team):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE teams
        SET team_name = ?
        WHERE team_number = ?;
        """, (team.team_name, team.team_number))
        await db.commit()

async def delete_team(team_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM teams WHERE team_number = ?;", (team_number,))
        await db.commit()

async def get_all_teams() -> list[Team]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT team_number, team_name FROM teams;")
        rows = await cursor.fetchall()
        teams = [Team(team_number=row[0], team_name=row[1]) for row in rows]
        return teams