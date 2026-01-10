import aiosqlite
from entityes.user import User
from entityes.file import File

DB_PATH = "georg.db"
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
            title TEXT NOT NULL,
            description TEXT,
            date_created TEXT NOT NULL DEFAULT (datetime('now')),
            status TEXT NOT NULL DEFAULT 'open',
            FOREIGN KEY (user_id) REFERENCES users(tg_id) ON DELETE CASCADE
        );
        """)

        await db.commit()