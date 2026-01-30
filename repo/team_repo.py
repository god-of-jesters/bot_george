from database import DB_PATH, TEAMS
import aiosqlite
from entityes.team import Team
from datetime import datetime, timezone
import io

def now_iso():
    return datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")

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

async def upsert_rating_rows(rows: list[dict]) -> int:
    if not rows:
        return 0

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys=ON;")
        await db.executemany(
            """
            INSERT INTO ratings (
                badge_number, full_name, team_id, daily_base,
                penalties_sum, bonuses_sum, total_points, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(badge_number) DO UPDATE SET
                full_name=excluded.full_name,
                team_id=excluded.team_id,
                daily_base=excluded.daily_base,
                penalties_sum=excluded.penalties_sum,
                bonuses_sum=excluded.bonuses_sum,
                total_points=excluded.total_points,
                updated_at=excluded.updated_at
            """,
            [
                (
                    r["badge_number"],
                    r["full_name"],
                    r["team_id"],
                    r["daily_base"],
                    r["penalties_sum"],
                    r["bonuses_sum"],
                    r["total_points"],
                    r["updated_at"],
                )
                for r in rows
            ],
        )
        await db.commit()

    return len(rows)

async def recalc_team_totals():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys=ON;")

        cur = await db.execute(
            """
            SELECT team_id, SUM(total_points) AS s
            FROM ratings
            WHERE team_id IS NOT NULL
            GROUP BY team_number
            """
        )
        team_sums = await cur.fetchall()

        now = now_iso()
        await db.executemany(
            """
            INSERT INTO ratingteams (team_id, team_name, team_total_points, updated_at)
            VALUES (?, COALESCE((SELECT team_name FROM ratingteams WHERE team_id = ?), ''), ?, ?)
            ON CONFLICT(team_id) DO UPDATE SET
                team_total_points=excluded.team_total_points,
                updated_at=excluded.updated_at
            """,
            [(row["team_id"], row["team_id"], int(row["s"] or 0), now) for row in team_sums],
        )
        await db.commit()