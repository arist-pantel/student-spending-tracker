import sqlite3

import pytest

from spending_tracker.database import (
    DEFAULT_CATEGORIES,
    get_connection,
    initialise_database,
)


@pytest.fixture
def database_path(tmp_path):
    """Create a separate temporary database for each test."""
    path = tmp_path / "test_spending_tracker.db"
    initialise_database(path)
    return path


def test_initialisation_creates_tables(database_path):
    connection = get_connection(database_path)

    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table';
            """
        ).fetchall()

        table_names = {row["name"] for row in rows}

        assert {
            "categories",
            "transactions",
            "monthly_budgets",
            "category_budgets",
        }.issubset(table_names)

    finally:
        connection.close()


def test_initialisation_does_not_duplicate_categories(database_path):
    initialise_database(database_path)

    connection = get_connection(database_path)

    try:
        rows = connection.execute(
            """
            SELECT name, transaction_type
            FROM categories;
            """
        ).fetchall()

        actual_categories = [
            (row["name"], row["transaction_type"])
            for row in rows
        ]

        assert sorted(actual_categories) == sorted(DEFAULT_CATEGORIES)

    finally:
        connection.close()


def test_transaction_persists_after_reopening(database_path):
    connection = get_connection(database_path)

    try:
        category = connection.execute(
            """
            SELECT id
            FROM categories
            WHERE name = ? AND transaction_type = ?;
            """,
            ("Groceries", "expense"),
        ).fetchone()

        cursor = connection.execute(
            """
            INSERT INTO transactions (
                amount_pence,
                transaction_date,
                category_id,
                note
            )
            VALUES (?, ?, ?, ?);
            """,
            (2450, "2026-11-06", category["id"], "Weekly shop"),
        )

        transaction_id = cursor.lastrowid
        connection.commit()

    finally:
        connection.close()

    connection = get_connection(database_path)

    try:
        transaction = connection.execute(
            """
            SELECT amount_pence, transaction_date, category_id, note
            FROM transactions
            WHERE id = ?;
            """,
            (transaction_id,),
        ).fetchone()

        assert transaction is not None
        assert transaction["amount_pence"] == 2450
        assert transaction["transaction_date"] == "2026-11-06"
        assert transaction["category_id"] == category["id"]
        assert transaction["note"] == "Weekly shop"

    finally:
        connection.close()


def test_foreign_keys_reject_missing_category(database_path):
    connection = get_connection(database_path)

    try:
        foreign_keys = connection.execute(
            "PRAGMA foreign_keys;"
        ).fetchone()[0]

        assert foreign_keys == 1

        missing_id = connection.execute(
            "SELECT MAX(id) + 1 FROM categories;"
        ).fetchone()[0]

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO transactions (
                    amount_pence,
                    transaction_date,
                    category_id
                )
                VALUES (?, ?, ?);
                """,
                (500, "2026-11-06", missing_id),
            )

        connection.rollback()

        count = connection.execute(
            "SELECT COUNT(*) FROM transactions;"
        ).fetchone()[0]

        assert count == 0

    finally:
        connection.close()


def test_income_category_cannot_have_spending_budget(database_path):
    connection = get_connection(database_path)

    try:
        category = connection.execute(
            """
            SELECT id
            FROM categories
            WHERE name = ? AND transaction_type = ?;
            """,
            ("Wages", "income"),
        ).fetchone()

        with pytest.raises(
            sqlite3.IntegrityError,
            match="Spending budgets require an expense category",
        ):
            connection.execute(
                """
                INSERT INTO category_budgets (
                    month,
                    category_id,
                    amount_pence
                )
                VALUES (?, ?, ?);
                """,
                ("2026-11", category["id"], 10000),
            )

        connection.rollback()

        count = connection.execute(
            "SELECT COUNT(*) FROM category_budgets;"
        ).fetchone()[0]

        assert count == 0

    finally:
        connection.close()