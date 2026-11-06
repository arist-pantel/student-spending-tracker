import sqlite3

from spending_tracker.database import initialise_database


def main():
    print("Student Spending Tracker")

    try:
        initialise_database()
    except (sqlite3.Error, OSError) as error:
        print(f"Could not initialise the database: {error}")
        return

    print("Database ready.")


if __name__ == "__main__":
    main()