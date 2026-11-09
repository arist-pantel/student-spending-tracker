def get_categories(connection, transaction_type):
    """Return categories belonging to the requested type."""
    return connection.execute(
        """
        SELECT id, name
        FROM categories
        WHERE transaction_type = ?
        ORDER BY name;
        """,
        (transaction_type,),
    ).fetchall()


def get_expense_categories(connection):
    """Return expense categories."""
    return get_categories(connection, "expense")

def get_category(connection, category_id):
    """Return one category, or None if it does not exist."""
    return connection.execute(
        """
        SELECT id, name, transaction_type
        FROM categories
        WHERE id = ?;
        """,
        (category_id,),
    ).fetchone()


def insert_transaction(
    connection,
    amount_pence,
    transaction_date,
    category_id,
    note,
):
    """Insert a transaction and return its ID."""
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
        (amount_pence, transaction_date, category_id, note),
    )

    return cursor.lastrowid


def get_transactions(connection):
    """Return transactions with their category names and types."""
    return connection.execute(
        """
        SELECT
            transactions.id,
            transactions.amount_pence,
            transactions.transaction_date,
            transactions.note,
            categories.name AS category_name,
            categories.transaction_type
        FROM transactions
        JOIN categories
            ON transactions.category_id = categories.id
        ORDER BY
            transactions.transaction_date DESC,
            transactions.id DESC;
        """
    ).fetchall()