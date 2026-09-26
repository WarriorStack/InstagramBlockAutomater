import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path(__file__).parent / "data" / "instagram.db"


def connect():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    con = sqlite3.connect(DB_PATH)

    con.row_factory = sqlite3.Row

    return con


# ======================================================
# Database initialization
# ======================================================

def init_db():

    with connect() as con:

        # Main username table
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Instagram accounts
        con.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Status of each target for each Instagram account
        con.execute("""
            CREATE TABLE IF NOT EXISTS user_account_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,

                status TEXT NOT NULL DEFAULT 'Pending',

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                UNIQUE(user_id, account_id),

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(account_id)
                    REFERENCES accounts(id)
                    ON DELETE CASCADE
            )
        """)

        con.commit()


# ======================================================
# Account management
# ======================================================

def get_or_create_account(account_username):

    account_username = (
        account_username
        .strip()
        .lstrip("@")
        .strip()
        .lower()
    )

    if not account_username:
        raise ValueError(
            "Instagram account username cannot be empty."
        )

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    with connect() as con:

        row = con.execute(
            """
            SELECT id
            FROM accounts
            WHERE username = ?
            """,
            (account_username,)
        ).fetchone()

        if row:
            account_id = row["id"]

        else:

            cursor = con.execute(
                """
                INSERT INTO accounts(
                    username,
                    created_at
                )
                VALUES (?, ?)
                """,
                (
                    account_username,
                    now
                )
            )

            account_id = cursor.lastrowid

        # Create Pending status for every existing user
        # if this account has never processed that user.
        con.execute(
            """
            INSERT OR IGNORE INTO user_account_status(
                user_id,
                account_id,
                status,
                created_at,
                updated_at
            )
            SELECT
                id,
                ?,
                'Pending',
                ?,
                ?
            FROM users
            """,
            (
                account_id,
                now,
                now
            )
        )

        con.commit()

        return account_id


def get_accounts():

    with connect() as con:

        return con.execute(
            """
            SELECT *
            FROM accounts
            ORDER BY username
            """
        ).fetchall()


# ======================================================
# Users
# ======================================================

def add_users(usernames):

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    added = 0

    with connect() as con:

        for username in usernames:

            u = (
                username
                .strip()
                .lstrip("@")
                .strip()
                .lower()
            )

            if not u:
                continue

            try:

                con.execute(
                    """
                    INSERT INTO users(
                        username,
                        status,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        u,
                        "Pending",
                        now,
                        now
                    )
                )

                added += 1

            except sqlite3.IntegrityError:

                pass

        con.commit()

    return added


# ======================================================
# Get users for active Instagram account
# ======================================================

def get_users(
    search="",
    account_id=None
):

    with connect() as con:

        if account_id is None:

            if search:

                return con.execute(
                    """
                    SELECT *
                    FROM users
                    WHERE username LIKE ?
                    ORDER BY username
                    """,
                    (
                        f"%{search.lower()}%",
                    )
                ).fetchall()

            return con.execute(
                """
                SELECT *
                FROM users
                ORDER BY username
                """
            ).fetchall()

        # Ensure every user has a status
        # for this account.
        now = datetime.now().isoformat(
            timespec="seconds"
        )

        con.execute(
            """
            INSERT OR IGNORE INTO user_account_status(
                user_id,
                account_id,
                status,
                created_at,
                updated_at
            )
            SELECT
                id,
                ?,
                'Pending',
                ?,
                ?
            FROM users
            """,
            (
                account_id,
                now,
                now
            )
        )

        if search:

            return con.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    COALESCE(
                        uas.status,
                        'Pending'
                    ) AS status,
                    u.created_at,
                    u.updated_at
                FROM users u

                LEFT JOIN user_account_status uas
                    ON uas.user_id = u.id
                    AND uas.account_id = ?

                WHERE u.username LIKE ?

                ORDER BY u.username
                """,
                (
                    account_id,
                    f"%{search.lower()}%"
                )
            ).fetchall()

        return con.execute(
            """
            SELECT
                u.id,
                u.username,
                COALESCE(
                    uas.status,
                    'Pending'
                ) AS status,
                u.created_at,
                u.updated_at
            FROM users u

            LEFT JOIN user_account_status uas
                ON uas.user_id = u.id
                AND uas.account_id = ?

            ORDER BY u.username
            """,
            (
                account_id,
            )
        ).fetchall()


# ======================================================
# Set status for an account
# ======================================================

def set_status(
    user_id,
    status,
    account_id=None
):

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    with connect() as con:

        # Old behavior fallback
        if account_id is None:

            con.execute(
                """
                UPDATE users
                SET
                    status = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    now,
                    user_id
                )
            )

        else:

            con.execute(
                """
                INSERT INTO user_account_status(
                    user_id,
                    account_id,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)

                ON CONFLICT(
                    user_id,
                    account_id
                )

                DO UPDATE SET
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    account_id,
                    status,
                    now,
                    now
                )
            )

        con.commit()


# ======================================================
# Statistics for active account
# ======================================================

def stats(account_id=None):

    if account_id is None:

        with connect() as con:

            rows = con.execute(
                """
                SELECT
                    status,
                    COUNT(*) AS n
                FROM users
                GROUP BY status
                """
            ).fetchall()

        d = {
            "Pending": 0,
            "Blocked": 0,
            "Skipped": 0,
            "Failed": 0
        }

        for row in rows:

            d[row["status"]] = row["n"]

        d["Total"] = sum(
            d.values()
        )

        return d

    with connect() as con:

        # Make sure every user has a record
        # for the selected account.
        now = datetime.now().isoformat(
            timespec="seconds"
        )

        con.execute(
            """
            INSERT OR IGNORE INTO user_account_status(
                user_id,
                account_id,
                status,
                created_at,
                updated_at
            )
            SELECT
                id,
                ?,
                'Pending',
                ?,
                ?
            FROM users
            """,
            (
                account_id,
                now,
                now
            )
        )

        rows = con.execute(
            """
            SELECT
                status,
                COUNT(*) AS n
            FROM user_account_status
            WHERE account_id = ?
            GROUP BY status
            """,
            (
                account_id,
            )
        ).fetchall()

    d = {
        "Pending": 0,
        "Blocked": 0,
        "Skipped": 0,
        "Failed": 0
    }

    for row in rows:

        d[row["status"]] = row["n"]

    d["Total"] = sum(
        d.values()
    )

    return d