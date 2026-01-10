import aiosqlite
from entityes.user import User
from entityes.file import File
from entityes.team import Team
from entityes.complaint import Complaint

DB_PATH = "georg.db"
USERS = {}
FILES = {}
TEAMS = {}
COMPLAINTS = {}

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")      # лучше для конкуренции
        await db.execute("PRAGMA foreign_keys=ON;")       # включить FK
        await db.execute("PRAGMA synchronous=NORMAL;")    # баланс скорость/надёжность
        await db.execute("PRAGMA busy_timeout=5000;")     # ждать, если БД занята

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER NOT NULL UNIQUE,
            fio TEXT,
            role TEXT NOT NULL DEFAULT 'participant',
            team_number INTEGER,
            num_badge INTEGER,
            reiting INTEGER NOT NULL DEFAULT 0,
            balance INTEGER NOT NULL DEFAULT 0,
            date_registered TEXT
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER NOT NULL,
            tg_file_id TEXT NOT NULL,
            file_name TEXT,
            mime_type TEXT,
            file_size INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_number INTEGER PRIMARY KEY,
            team_name TEXT NOT NULL, 
            reiting INTEGER NOT NULL DEFAULT 0
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            adresat TEXT NOT NULL,
            description TEXT,
            date_created TEXT NOT NULL DEFAULT (datetime('now')),
            date_resolved TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            execution TEXT,
            FOREIGN KEY (user_id) REFERENCES users(tg_id) ON DELETE CASCADE
        );
        """)

        await db.commit()

async def load_datastore():
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        # Load users
        cursor = await db.execute("SELECT tg_id, fio, team_number, role, num_badge, reiting, balance, date_registered FROM users;")
        rows = await cursor.fetchall()
        for row in rows:
            user = User(user_id=row[0], fio=row[1], team_number=row[2], role=row[3], badge_number=row[4], reiting=row[5], balance=row[6])
            USERS[user.user_id] = user

        # Load files
        cursor = await db.execute("SELECT id, tg_id, tg_file_id, file_name, mime_type, file_size, created_at FROM files;")
        rows = await cursor.fetchall()
        for row in rows:
            file = File(id=row[0], tg_id=row[1], tg_file_id=row[2], file_name=row[3], mime_type=row[4], file_size=row[5], date_created=row[6])
            FILES[file.id] = file

        # Load teams
        cursor = await db.execute("SELECT team_number, team_name FROM teams;")
        rows = await cursor.fetchall()
        for row in rows:
            team = Team(team_number=row[0], team_name=row[1])
            TEAMS[team.team_number] = team

        # Load complaints
        cursor = await db.execute("SELECT id, user_id, adresat, description, date_created, date_resolved, status, execution FROM complaints;")
        rows = await cursor.fetchall()
        for row in rows:
            complaint = Complaint(complaint_id=row[0], user_id=row[1], adresat=row[2], description=row[3], date_created=row[4], date_resolved=row[5], status=row[6], execution=row[7])
            COMPLAINTS[complaint.complaint_id] = complaint