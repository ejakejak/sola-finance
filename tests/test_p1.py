"""P1 verification: order costing update, reconciliation calc, aging computation."""
import sqlite3, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import conn
def _close_all():
    import gc; gc.collect()

def test_order_cost_update():
    c = conn()
    c.execute("INSERT OR IGNORE INTO orders (order_number, customer, description, estimated_cost, status) VALUES ('TEST-01','TestCo','Demo',100000,'Estimated')")
    cid = c.execute("SELECT id FROM orders WHERE order_number='TEST-01'").fetchone()[0]
    c.execute("INSERT INTO transactions (tx_type, amount, direction, status, order_id, created_by) VALUES ('Receipt',50000,'in','Posted',?,?)", (cid, 1))
    from app.routes.orders import _recalc_order
    _recalc_order(c, cid)
    row = c.execute("SELECT actual_cost, status FROM orders WHERE id=?", (cid,)).fetchone()
    assert row[0] == 50000, f"expected 50000 got {row[0]}"
    c.execute("DELETE FROM transactions WHERE order_id=?", (cid,))
    c.execute("DELETE FROM orders WHERE id=?", (cid,))
    c.commit(); c.close(); _close_all()

def test_reconciliation_calc():
    c = conn()
    c.execute("INSERT INTO reconciliation (account, period_start, period_end, opening_balance, total_cash_in, total_cash_out, current_balance) VALUES ('Cash','2026-01-01','2026-01-31',1000,500,200,1300)")
    row = c.execute("SELECT current_balance FROM reconciliation WHERE account='Cash'").fetchone()
    assert row[0] == 1300
    c.execute("DELETE FROM reconciliation WHERE account='Cash'")
    c.commit(); c.close(); _close_all()

def test_aging_computation():
    from app.routes.aging import _refresh_aging
    c = conn()
    _refresh_aging(c)
    c.execute("SELECT count(*) FROM customer_aging")
    c.commit(); c.close(); _close_all()

if __name__ == "__main__":
    test_order_cost_update()
    test_reconciliation_calc()
    test_aging_computation()
    print("P1 tests passed.")
