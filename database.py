import aiosqlite
from entityes.user import User
from entityes.file import File
from entityes.team import Team
from entityes.complaint import Complaint
from entityes.product import Product

DB_PATH = "georg.db"

USERS = {}
FILES = {}
TEAMS = {}
COMPLAINTS = {}
PRODUCTS = {}
PRODUCT_NAME_INDEX = {}
MESSAGES = {}


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")
        await db.execute("PRAGMA synchronous=NORMAL;")
        await db.execute("PRAGMA busy_timeout=5000;")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE,
            username TEXT,
            fio TEXT,
            role TEXT NOT NULL DEFAULT 'participant',
            team_number INTEGER,
            badge_number INTEGER UNIQUE,
            reiting INTEGER NOT NULL DEFAULT 0,
            balance INTEGER NOT NULL DEFAULT 0,
            date_registered TEXT
        );
        """)
        cursor = await db.execute("PRAGMA table_info(users);")
        user_columns = {row[1] for row in await cursor.fetchall()}

        if "gender" not in user_columns:
            await db.execute(
                "ALTER TABLE users ADD COLUMN gender TEXT CHECK (gender IN ('М', 'Ж'));"
            )

        # миграция: добавляем колонку username, если её ещё нет
        cursor = await db.execute("PRAGMA table_info(users);")
        user_columns = {row[1] for row in await cursor.fetchall()}
        if "username" not in user_columns:
            await db.execute("ALTER TABLE users ADD COLUMN username TEXT;")
        await db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_badge_number
        ON users(badge_number);
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER NOT NULL,
            tg_file_id TEXT NOT NULL,
            complaint_id INTEGER,
            file_name TEXT,
            mime_type TEXT,
            file_size INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE
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
            adresat INTEGER,
            violetion TEXT,
            description TEXT,
            date_created TEXT NOT NULL DEFAULT (datetime('now')),
            date_resolved TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            execution TEXT,
            FOREIGN KEY (user_id) REFERENCES users(tg_id) ON DELETE CASCADE
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS active (
            user_id INTEGER,
            role TEXT
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            cost INTEGER,
            amount INTEGER
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS sells (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            badge_number INTEGER,
            poduct_id INTEGER,
            date_created TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (badge_number) REFERENCES users(badge_number),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS promokodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phrase TEXT,
            amount INTEGER,
            bonus INTEGER,
            badge_number INTEGER,
            date_created TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (badge_number) REFERENCES users(badge_number)
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            actor_tg_id INTEGER,
            adresat_tg_id INTEGER,
            badge_number INTEGER,
            role TEXT,
            complaint_id INTEGER,
            file_row_id INTEGER,
            tg_file_id TEXT,
            solution TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            adresat TEXT NOT NULL,
            badge_number INTEGER NOT NULL DEFAULT 0,
            text TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            date_created TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(tg_id) ON DELETE CASCADE
        );
        """)
        cursor = await db.execute("PRAGMA table_info(messages);")
        message_columns = {row[1] for row in await cursor.fetchall()}
        if "badge_number" not in message_columns:
            await db.execute(
                "ALTER TABLE messages ADD COLUMN badge_number INTEGER NOT NULL DEFAULT 0;"
            )

        await db.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            badge_number INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            team_id INTEGER,
            daily_base INTEGER NOT NULL DEFAULT 100,
            penalties_sum INTEGER NOT NULL DEFAULT 0,
            bonuses_sum INTEGER NOT NULL DEFAULT 0,
            total_points INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT,
            FOREIGN KEY (badge_number) REFERENCES users(badge_number)
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS ratingteams (
            team_number INTEGER PRIMARY KEY,
            team_name TEXT NOT NULL,
            team_total_points INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT,
            FOREIGN KEY (team_number) REFERENCES teams(team_number)
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS complaints_counter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            complaint_id INTEGER NOT NULL DEFAULT 0,
            date_created TEXT,
            FOREIGN KEY (user_id) REFERENCES users(tg_id) ON DELETE CASCADE
        );
        """)
    
        await db.execute("""
        CREATE TABLE IF NOT EXISTS families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first INTEGER,
            second INTEGER,
            second_name TEXT,
            FOREIGN KEY (first) REFERENCES users(badge_number) ON DELETE CASCADE,
            FOREIGN KEY (second) REFERENCES users(badge_number) ON DELETE CASCADE
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_badge INTEGER NOT NULL,
            points INTEGER NOT NULL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'approved', 'rejected')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)

        await db.commit()


async def load_datastore():
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT tg_id, username, fio, team_number, role, badge_number, reiting, balance, date_registered FROM users;"
        )
        for row in await cursor.fetchall():
            user = User(
                tg_id=row[0],
                username=row[1],
                fio=row[2],
                team_number=row[3],
                role=row[4],
                badge_number=row[5],
                reiting=row[6],
                balance=row[7],
                date_registered=row[8],
            )
            USERS[user.tg_id] = user

        cursor = await db.execute(
            "SELECT id, tg_id, tg_file_id, complaint_id, file_name, mime_type, file_size, created_at FROM files;"
        )
        for row in await cursor.fetchall():
            file = File(
                id=row[0],
                tg_id=row[1],
                tg_file_id=row[2],
                complaint_id=row[3],
                file_name=row[4],
                mime_type=row[5],
                file_size=row[6],
                date_created=row[7]
            )
            FILES[file.tg_file_id] = file

        cursor = await db.execute("SELECT team_number, team_name FROM teams;")
        for row in await cursor.fetchall():
            team = Team(team_number=row[0], team_name=row[1])
            TEAMS[team.team_number] = team

        cursor = await db.execute(
            "SELECT id, user_id, adresat, violetion, description, date_created, date_resolved, status, execution FROM complaints;"
        )
        for row in await cursor.fetchall():
            complaint = Complaint(
                complaint_id=row[0],
                user_id=row[1],
                adresat=row[2],
                violetion=row[3],
                description=row[4],
                status=row[7],
                execution=row[8]
            )
            complaint.date_created = row[5]
            complaint.date_resolved = row[6]

            file_cursor = await db.execute(
                "SELECT id FROM files WHERE complaint_id = ?;",
                (row[0],)
            )
            complaint.files = [fr[0] for fr in await file_cursor.fetchall()]
            COMPLAINTS[complaint.complaint_id] = complaint

        cursor = await db.execute(
            "SELECT id, name, cost, amount FROM products;"
        )
        for row in await cursor.fetchall():
            product = Product(
                id=row[0],
                name=row[1],
                cost=row[2],
                amount=row[3]
            )
            PRODUCTS[product.id] = product
            PRODUCT_NAME_INDEX[product.name] = product.id
