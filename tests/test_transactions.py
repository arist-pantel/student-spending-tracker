import pytest

from spending_tracker.database import (
    get_connection,
    initialise_database,
)
from spending_tracker.services import add_expense, list_transactions
from spending_tracker.validation import parse_amount


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "test_tracker.db"
    initialise_database(path)
    return path


def find_category_id(database_path, name):
    connection = get_connection(database_path)

    try:
        row = connection.execute(
            "SELECT id FROM categories WHERE name = ?;",
            (name,),
        ).fetchone()

        return row["id"]
    finally:
        connection.close()


@pytest.mark.parametrize(
    "text, expected",
    [
        ("0.01", 1),
        ("12", 1200),
        ("12.5", 1250),
        ("12.50", 1250),
        (" 24.99 ", 2499),
    ],
)
def test_amount_conversion_is_exact(text, expected):
    assert parse_amount(text) == expected


def test_add_expense_and_list_it(database_path):
    category_id = find_category_id(database_path, "Groceries")

    transaction_id = add_expense(
        "24.50",
        "2026-11-06",
        category_id,
        "Weekly shop",
        database_path=database_path,
    )

    # Listing opens a separate connection.
    transactions = list_transactions(database_path)

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction["id"] == transaction_id
    assert transaction["amount_pence"] == 2450
    assert transaction["transaction_date"] == "2026-11-06"
    assert transaction["category_name"] == "Groceries"
    assert transaction["transaction_type"] == "expense"
    assert transaction["note"] == "Weekly shop"


@pytest.mark.parametrize(
    "amount, transaction_date",
    [
        ("", "2026-11-06"),
        ("0", "2026-11-06"),
        ("-5", "2026-11-06"),
        ("1.001", "2026-11-06"),
        ("NaN", "2026-11-06"),
        ("10", "2026-02-30"),
        ("10", "06/11/2026"),
    ],
)
def test_invalid_input_preserves_existing_data(
    database_path, amount, transaction_date
):
    category_id = find_category_id(database_path, "Groceries")

    add_expense(
        "5.00",
        "2026-11-01",
        category_id,
        database_path=database_path,
    )

    before = [
        dict(row) for row in list_transactions(database_path)
    ]

    with pytest.raises(ValueError):
        add_expense(
            amount,
            transaction_date,
            category_id,
            database_path=database_path,
        )

    after = [
        dict(row) for row in list_transactions(database_path)
    ]

    assert after == before


def test_income_category_is_rejected(database_path):
    category_id = find_category_id(database_path, "Wages")

    with pytest.raises(ValueError, match="expense category"):
        add_expense(
            "10.00",
            "2026-11-06",
            category_id,
            database_path=database_path,
        )

    assert list_transactions(database_path) == []


def test_missing_category_is_rejected(database_path):
    with pytest.raises(ValueError, match="does not exist"):
        add_expense(
            "10.00",
            "2026-11-06",
            999999,
            database_path=database_path,
        )

    assert list_transactions(database_path) == []