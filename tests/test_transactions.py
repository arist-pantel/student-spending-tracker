import pytest

from spending_tracker.database import (
    get_connection,
    initialise_database,
)
from spending_tracker.services import (
    add_expense,
    add_income,
    add_transaction,
    list_categories,
    list_transactions,
)
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

def test_add_income_and_list_it(database_path):
    category_id = find_category_id(database_path, "Wages")

    transaction_id = add_income(
        "300.50",
        "2026-11-09",
        category_id,
        "Part-time work",
        database_path=database_path,
    )

    transactions = list_transactions(database_path)

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction["id"] == transaction_id
    assert transaction["amount_pence"] == 30050
    assert transaction["transaction_date"] == "2026-11-09"
    assert transaction["category_name"] == "Wages"
    assert transaction["transaction_type"] == "income"
    assert transaction["note"] == "Part-time work"


def test_income_rejects_expense_category(database_path):
    category_id = find_category_id(database_path, "Groceries")

    with pytest.raises(ValueError, match="income category"):
        add_income(
            "100.00",
            "2026-11-09",
            category_id,
            database_path=database_path,
        )

    assert list_transactions(database_path) == []


def test_income_categories_exclude_expense_categories(database_path):
    categories = list_categories(
        "income",
        database_path=database_path,
    )

    names = {category["name"] for category in categories}

    assert names == {"Student finance", "Wages", "Gifts"}


def test_income_and_expenses_are_stored_together(database_path):
    groceries_id = find_category_id(database_path, "Groceries")
    wages_id = find_category_id(database_path, "Wages")

    expense_id = add_expense(
        "24.50",
        "2026-11-08",
        groceries_id,
        database_path=database_path,
    )

    income_id = add_income(
        "300.00",
        "2026-11-09",
        wages_id,
        database_path=database_path,
    )

    transactions = list_transactions(database_path)

    assert len(transactions) == 2

    # Newest transaction date comes first.
    assert transactions[0]["id"] == income_id
    assert transactions[0]["transaction_type"] == "income"
    assert transactions[0]["amount_pence"] == 30000

    assert transactions[1]["id"] == expense_id
    assert transactions[1]["transaction_type"] == "expense"
    assert transactions[1]["amount_pence"] == 2450


def test_invalid_transaction_type_leaves_data_unchanged(database_path):
    category_id = find_category_id(database_path, "Groceries")

    add_expense(
        "5.00",
        "2026-11-08",
        category_id,
        database_path=database_path,
    )

    before = [
        dict(row) for row in list_transactions(database_path)
    ]

    with pytest.raises(ValueError, match="Transaction type"):
        add_transaction(
            "10.00",
            "2026-11-09",
            category_id,
            transaction_type="refund",
            database_path=database_path,
        )

    after = [
        dict(row) for row in list_transactions(database_path)
    ]

    assert after == before


@pytest.mark.parametrize("amount", ["0", "-10", "1.001"])
def test_income_rejects_invalid_amounts(database_path, amount):
    category_id = find_category_id(database_path, "Wages")

    with pytest.raises(ValueError):
        add_income(
            amount,
            "2026-11-09",
            category_id,
            database_path=database_path,
        )

    assert list_transactions(database_path) == []    