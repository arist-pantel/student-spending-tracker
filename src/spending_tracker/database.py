import sqlite3
from pathlib import Path


DEFAULT_DATABASE_PATH = Path("data") / "spending_tracker.db"

DEFAULT_CATEGORIES = [
    ("Groceries", "expense"),
    ("Eating out", "expense"),
    ("Transport", "expense"),
    ("Accommodation", "expense"),
    ("Entertainment", "expense"),
    ("University", "expense"),
    ("Other", "expense"),
    ("Student finance", "income"),
    ("Wages", "income"),
    ("Gifts", "income"),
]


SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,

    name TEXT NOT NULL COLLATE NOCASE
        CHECK (length(trim(name)) > 0)
        CHECK (name = trim(name)),

    transaction_type TEXT NOT NULL
        CHECK (transaction_type IN ('income', 'expense')),

    UNIQUE (name, transaction_type)
);


CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,

    amount_pence INTEGER NOT NULL
        CHECK (
            typeof(amount_pence) = 'integer'
            AND amount_pence > 0
        ),

    transaction_date TEXT NOT NULL,

    category_id INTEGER NOT NULL,

    note TEXT,

    created_at TEXT NOT NULL DEFAULT (
        strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    ),

    FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS monthly_budgets (
    id INTEGER PRIMARY KEY,

    month TEXT NOT NULL UNIQUE,

    amount_pence INTEGER NOT NULL
        CHECK (
            typeof(amount_pence) = 'integer'
            AND amount_pence >= 0
        )
);


CREATE TABLE IF NOT EXISTS category_budgets (
    id INTEGER PRIMARY KEY,

    month TEXT NOT NULL,

    category_id INTEGER NOT NULL,

    amount_pence INTEGER NOT NULL
        CHECK (
            typeof(amount_pence) = 'integer'
            AND amount_pence >= 0
        ),

    FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE RESTRICT,

    UNIQUE (month, category_id)
);


CREATE INDEX IF NOT EXISTS idx_transactions_date
ON transactions(transaction_date);


CREATE TRIGGER IF NOT EXISTS prevent_category_type_change
BEFORE UPDATE OF transaction_type ON categories
FOR EACH ROW
WHEN NEW.transaction_type != OLD.transaction_type
BEGIN
    SELECT RAISE(
        ABORT,
        'A category transaction type cannot be changed.'
    );
END;


CREATE TRIGGER IF NOT EXISTS check_budget_category_insert
BEFORE INSERT ON category_budgets
FOR EACH ROW
WHEN (
    SELECT transaction_type
    FROM categories
    WHERE id = NEW.category_id
) = 'income'
BEGIN
    SELECT RAISE(
        ABORT,
        'Spending budgets require an expense category.'
    );
END;


CREATE TRIGGER IF NOT EXISTS check_budget_category_update
BEFORE UPDATE OF category_id ON category_budgets
FOR EACH ROW
WHEN (
    SELECT transaction_type
    FROM categories
    WHERE id = NEW.category_id
) = 'income'
BEGIN
    SELECT RAISE(
        ABORT,
        'Spending budgets require an expense category.'
    );
END;
"""


def get_connection(database_path=DEFAULT_DATABASE_PATH):
    """Open a database connection with foreign keys enabled."""
    database_path = Path(database_path)

    # Create the folder containing the database if it is missing.
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)

    try:
        connection.row_factory = sqlite3.Row

        connection.execute("PRAGMA foreign_keys = ON;")
    except sqlite3.Error:
        connection.close()
        raise

    return connection


def initialise_database(database_path=DEFAULT_DATABASE_PATH):
    """Create the schema and add any missing default categories."""
    connection = get_connection(database_path)

    try:
        connection.executescript("BEGIN;\n" + SCHEMA)

        connection.executemany(
            """
            INSERT INTO categories (name, transaction_type)
            VALUES (?, ?)
            ON CONFLICT (name, transaction_type) DO NOTHING;
            """,
            DEFAULT_CATEGORIES,
        )

        connection.commit()

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()