"""DB migration — idempotent. Tables per ARTIFACT-A/B/C/D (§5 arithmetic corrected; audit §5)."""
import sqlite3, os
from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE, role TEXT NOT NULL DEFAULT 'Non-Finance',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tx_type TEXT NOT NULL CHECK(tx_type IN ('Receipt','Expense','Transfer','Adjustment')),
  amount REAL NOT NULL, direction TEXT DEFAULT 'in',
  status TEXT NOT NULL DEFAULT 'Draft' CHECK(status IN ('Draft','Posted','Reversed')),
  external_id TEXT UNIQUE,
  order_id INTEGER, reference TEXT, proof_path TEXT,
  created_by INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS transactions_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tx_id INTEGER NOT NULL, action TEXT NOT NULL, user_id INTEGER, note TEXT,
  ts TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS invoices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  external_id TEXT NOT NULL UNIQUE, customer_id INTEGER,
  amount REAL, hpp REAL, gross_profit REAL,
  status TEXT DEFAULT 'Open', created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS invoices_import (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  external_id TEXT UNIQUE NOT NULL, source_file TEXT,
  imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER, supplier_id INTEGER,
  amount REAL, method TEXT DEFAULT 'DP', status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','Verified','Reversed')),
  dp_amount REAL, cicilan REAL, partial REAL,
  proof_path TEXT, verified_by INTEGER, verified_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_tx_external ON transactions(external_id);
CREATE INDEX IF NOT EXISTS idx_inv_ext ON invoices(external_id);
CREATE INDEX IF NOT EXISTS idx_pay_cust ON payments(customer_id);
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_number TEXT UNIQUE NOT NULL,
  customer TEXT NOT NULL,
  description TEXT,
  estimated_cost REAL NOT NULL DEFAULT 0,
  actual_cost REAL NOT NULL DEFAULT 0,
  status TEXT DEFAULT 'Estimated' CHECK(status IN ('Estimated','On Track','Over Budget','Finalized')),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS reconciliation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account TEXT NOT NULL,
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  opening_balance REAL NOT NULL DEFAULT 0,
  total_cash_in REAL NOT NULL DEFAULT 0,
  total_cash_out REAL NOT NULL DEFAULT 0,
  current_balance REAL NOT NULL DEFAULT 0,
  unmatched_items TEXT,
  reconciled_by TEXT,
  reconciled_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS customer_aging (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer TEXT NOT NULL,
  current REAL DEFAULT 0,
  day_30 REAL DEFAULT 0,
  day_60 REAL DEFAULT 0,
  day_90_plus REAL DEFAULT 0,
  total REAL DEFAULT 0,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

def migrate():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.executescript(SCHEMA)
    conn.execute("INSERT OR IGNORE INTO users (username,role) VALUES ('finance@sola.id','Finance')")
    conn.execute("INSERT OR IGNORE INTO users (username,role) VALUES ('user@sola.id','Non-Finance')")
    conn.execute("INSERT OR IGNORE INTO users (username,role) VALUES ('customer@sola.id','Customer')")
    conn.commit(); conn.close()

if __name__ == "__main__": migrate()
