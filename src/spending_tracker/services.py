from spending_tracker import repositories
from spending_tracker.database import (
    DEFAULT_DATABASE_PATH,
    get_connection,
)
from spending_tracker.validation import parse_amount, parse_date


def list_expense_categories(database_path=DEFAULT_DATABASE_PATH):
    connection = get_connection(database_path)

    try:
        return repositories.get_expense_categories(connection)
    finally:
        connection.close()


def add_expense(
    amount_text,
    date_text,
    category_id,
    note="",
    database_path=DEFAULT_DATABASE_PATH,
):
    """Validate and save an expense, returning its ID."""
    amount_pence = parse_amount(amount_text)
    transaction_date = parse_date(date_text)

    if type(category_id) is not int or category_id <= 0:
        raise ValueError("Choose a valid category ID.")

    note = note.strip() or None

    connection = get_connection(database_path)

    try:
        # Commit on success; roll back if an exception occurs.
        with connection:
            category = repositories.get_category(
                connection, category_id
            )

            if category is None:
                raise ValueError("That category does not exist.")

            if category["transaction_type"] != "expense":
                raise ValueError("Choose an expense category.")

            transaction_id = repositories.insert_transaction(
                connection,
                amount_pence,
                transaction_date,
                category_id,
                note,
            )

        return transaction_id

    finally:
        connection.close()


def list_transactions(database_path=DEFAULT_DATABASE_PATH):
    connection = get_connection(database_path)

    try:
        return repositories.get_transactions(connection)
    finally:
        connection.close()