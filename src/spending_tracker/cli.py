import sqlite3

from spending_tracker import services
from spending_tracker.validation import format_money


def add_expense_screen():
    categories = services.list_expense_categories()

    if not categories:
        print("No expense categories are available.")
        return

    print("\nExpense categories")

    for category in categories:
        print(f"{category['id']}. {category['name']}")

    print("\nEnter the category ID, or press Enter to cancel.")
    category_text = input("Category ID: ").strip()

    if not category_text:
        print("Cancelled.")
        return

    try:
        category_id = int(category_text)
    except ValueError:
        raise ValueError("Category ID must be a whole number.") from None

    amount_text = input("Amount in GBP, for example 12.50: ")
    date_text = input("Date as YYYY-MM-DD: ")
    note = input("Note (optional): ")

    confirmation = input("Save this expense? [y/N]: ").strip().lower()

    if confirmation != "y":
        print("Cancelled.")
        return

    transaction_id = services.add_expense(
        amount_text,
        date_text,
        category_id,
        note,
    )

    print(f"Expense saved with ID {transaction_id}.")


def view_transactions_screen():
    transactions = services.list_transactions()

    if not transactions:
        print("\nNo transactions saved yet.")
        return

    print("\nSaved transactions")

    for transaction in transactions:
        amount = format_money(transaction["amount_pence"])

        print(
            f"\n#{transaction['id']} | "
            f"{transaction['transaction_date']} | "
            f"{transaction['transaction_type']} | "
            f"{transaction['category_name']} | "
            f"{amount}"
        )

        if transaction["note"]:
            print(f"  Note: {transaction['note']}")


def run():
    while True:
        print("\nStudent Spending Tracker")
        print("1. Add expense")
        print("2. View transactions")
        print("0. Exit")

        try:
            choice = input("Choose an option: ").strip()

            if choice == "1":
                add_expense_screen()
            elif choice == "2":
                view_transactions_screen()
            elif choice == "0":
                print("Goodbye.")
                return
            else:
                print("Choose 1, 2, or 0.")

        except ValueError as error:
            print(f"Invalid input: {error}")

        except (sqlite3.Error, OSError):
            print("Could not access or save the data. Please try again.")

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            return