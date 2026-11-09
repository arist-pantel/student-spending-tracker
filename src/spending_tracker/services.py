from spending_tracker import repositories
from spending_tracker.database import (
    DEFAULT_DATABASE_PATH,
    get_connection,
)
from spending_tracker.validation import parse_amount, parse_date


def validate_transaction_type(transaction_type):
    """Only income and expense are valid transaction types."""
    if transaction_type not in ("income", "expense"):
        raise ValueError("Transaction type must be income or expense.")


def list_categories(
    transaction_type,
    database_path=DEFAULT_DATABASE_PATH,
):
    validate_transaction_type(transaction_type)

    connection = get_connection(database_path)

    try:
        return repositories.get_categories(
            connection, transaction_type
        )
    finally:
        connection.close()


def list_expense_categories(database_path=DEFAULT_DATABASE_PATH):
    return list_categories("expense", database_path)


def add_transaction(
    amount_text,
    date_text,
    category_id,
    transaction_type,
    note="",
    database_path=DEFAULT_DATABASE_PATH,
):
    """Validate and save an income or expense transaction."""
    validate_transaction_type(transaction_type)

    amount_pence = parse_amount(amount_text)
    transaction_date = parse_date(date_text)

    if type(category_id) is not int or category_id <= 0:
        raise ValueError("Choose a valid category ID.")

    note = note.strip() or None

    connection = get_connection(database_path)

    try:
        with connection:
            category = repositories.get_category(
                connection, category_id
            )

            if category is None:
                raise ValueError("That category does not exist.")

            if category["transaction_type"] != transaction_type:
                if transaction_type == "expense":
                    raise ValueError("Choose an expense category.")

                raise ValueError("Choose an income category.")

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


def add_expense(
    amount_text,
    date_text,
    category_id,
    note="",
    database_path=DEFAULT_DATABASE_PATH,
):
    """Save an expense using the shared transaction function."""
    return add_transaction(
        amount_text,
        date_text,
        category_id,
        transaction_type="expense",
        note=note,
        database_path=database_path,
    )


def add_income(
    amount_text,
    date_text,
    category_id,
    note="",
    database_path=DEFAULT_DATABASE_PATH,
):
    """Save income using the shared transaction function."""
    return add_transaction(
        amount_text,
        date_text,
        category_id,
        transaction_type="income",
        note=note,
        database_path=database_path,
    )


def list_transactions(database_path=DEFAULT_DATABASE_PATH):
    connection = get_connection(database_path)

    try:
        return repositories.get_transactions(connection)
    finally:
        connection.close()