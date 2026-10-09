#!/usr/bin/env bash
# SOLA Finance — run instructions (verified)
echo "=== SOLA Finance full module (Flask 3.1.1 + SQLite + Jinja) ==="
echo "DB path: $(python3 -c 'from sola_finance.app.config import DB_PATH; print(DB_PATH)')"
echo "--- Migrate (idempotent) ---"; python3 -m sola_finance.db.migrate
echo "--- Tests P0 ---"; PYTHONPATH=. python3 sola_finance/tests/test_p0.py
echo "--- Run server (dev) ---"
echo "python3 -m sola_finance.app.run  # port 5000"
echo "Or: cd sola_finance && FLASK_APP=app/run.py flask run"
