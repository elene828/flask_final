# Finance Tracker

Lightweight personal finance tracker built with Flask. Provides user authentication, categories, transactions, and a small REST API for retrieving and creating transactions and balance summaries.

## Features
- User registration, login, logout (Flask-Login)
- Create, list, and soft-delete transactions
- Category management per-user
- Monthly balance summary with currency conversion
- Simple REST API under `/api`

## Tech
- Python, Flask
- Flask-Login, Flask-SQLAlchemy
- SQLite by default (configurable via `DATABASE_URL`)

## Quickstart

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a `.env` file at the project root (optional) and set:

- `SECRET_KEY` — application secret
- `DATABASE_URL` — SQLAlchemy database URL (defaults to `sqlite:///finance.db`)

Example `.env`:

```
SECRET_KEY=replace-with-a-secret
DATABASE_URL=sqlite:///finance.db
```

3. Run the app (development):

```bash
python app.py
```

The app will create the database tables automatically on first run.

## API

Base path: `/api`

- `GET /api/transactions` — list transactions (supports `page`, `per_page`, `start_date`, `end_date`, `category_id`, `type`)
- `POST /api/transactions` — create transaction (JSON: `category_id`, `type`, `amount`, optional `date` and `description`)
- `DELETE /api/transactions/<id>` — soft-delete a transaction
- `GET /api/balance` — monthly balance summary (returns GEL and converted amount)
- `GET /api/categories` — list user categories

All API endpoints require an authenticated user (the project uses session-based auth via the web UI).

## Project structure

- `app.py` — application factory and app entrypoint
- `config.py` — configuration and environment loading
- `extensions.py` — Flask extensions initialization (DB, login manager)
- `services.py` — business logic helpers (e.g., currency conversion)
- `helpers.py` — route helpers and decorators
- `models/` — SQLAlchemy models (`User`, `Transaction`, `Category`, etc.)
- `routes/` — Flask blueprints for auth, dashboard, admin, API, categories, settings
- `templates/` — Jinja2 templates for the web UI

## Notes
- On registration the app creates a set of default categories for the user.
- Currency conversion is handled by `services.CurrencyConverter` and used by the `/api/balance` endpoint.
- The project defaults to SQLite for quick local development but can use any database supported by SQLAlchemy via `DATABASE_URL`.

## Contributing

Feel free to open issues or submit PRs. For quick local testing, ensure you have a virtual env and `requirements.txt` installed.

## Setup
1. Create and activate a virtual environment:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy the environment example file and update it if needed:
   - `copy .example.env .env`

## Usage
1. Run the app:
   - `python app.py`
2. Open your browser and go to:
   - `http://127.0.0.1:5000`
3. Register a user account and start managing your finances.
