from database import DB_PATH, TEAMS
import aiosqlite
from entityes.team import Team

async def add_team(team: Team):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO teams (team_number, team_name)
        VALUES (?, ?);
        """, (team.team_number, team.team_name))
        await db.commit()
        TEAMS[team.team_number] = team

async def get_team(team_number: int) -> Team | None:
    if team_number in TEAMS:
        return TEAMS[team_number]
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
        TEAMS[team.team_number] = team

async def delete_team(team_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM teams WHERE team_number = ?;", (team_number,))
        await db.commit()
        if team_number in TEAMS:
            del TEAMS[team_number]
