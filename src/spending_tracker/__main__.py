import sqlite3

from spending_tracker.cli import run
from spending_tracker.database import initialise_database


def main():
    try:
        initialise_database()
    except (sqlite3.Error, OSError):
        print("Could not initialise the database.")
        return

    run()


if __name__ == "__main__":
    main()