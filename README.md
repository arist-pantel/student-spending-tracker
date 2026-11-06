# Student Spending Tracker

A Python terminal application for recording student income and expenses,
setting monthly budgets, and viewing spending summaries.

## Status

Initial project setup. Transaction and budget features are not implemented yet.

## Technology

- Python 3.11 or later
- SQLite through Python's built-in sqlite3 module
- pytest for automated tests

Money will be stored as integer pence to avoid floating-point rounding errors.

## Setup on Windows

Create a virtual environment:

```powershell
py -m venv .venv