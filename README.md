# Student Spending Tracker

A Python terminal application for tracking student income and expenses.

## Current features

- Record income and expenses with a date, category, and optional note.
- List saved transactions, newest first.
- Store data locally in SQLite.
- Validate amounts, dates, and category types.
- Store money as integer pence to avoid floating-point rounding errors.

Category management, filtering, editing, deletion, budgets, reports,
and CSV export are planned.

## Requirements

Python 3.11 or later.

## Setup on Windows

Run these commands from the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

SQLite support is included with Python.

## Run

```powershell
.\.venv\Scripts\python.exe -m spending_tracker
```

Run from the project root. The application creates its database at
`data/spending_tracker.db`.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Tests use temporary databases rather than personal spending data.

## Structure

- `cli.py`: terminal input and output.
- `database.py`: connections, schema, and initial categories.
- `repositories.py`: SQL operations.
- `services.py`: application rules and transaction coordination.
- `validation.py`: monetary and date validation.

Application modules are inside `src/spending_tracker`.

## Privacy and limitations

Runtime databases and personal exports are excluded from Git.
Use synthetic data for public examples.

Version 1 supports one local user and GBP only.
It does not connect to banks. Budgets and monthly reports are not
implemented yet.