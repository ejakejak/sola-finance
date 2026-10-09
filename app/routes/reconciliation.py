"""Cash/Bank Reconciliation (P1 Task 2)."""
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from db import conn
import datetime

recon_bp = Blueprint("reconciliation", __name__, url_prefix="/reconciliation")

@recon_bp.route("/")
def index():
    c = conn()
    # Default period = last 30 days
    today = datetime.date.today()
    period_end = request.args.get("period_end") or today.isoformat()
    period_start = request.args.get("period_start") or (today - datetime.timedelta(days=30)).isoformat()
    account = request.args.get("account") or "Cash"
    # Previous period closing balance = most recent reconciliation with same account and earlier period_end
    prev = c.execute("SELECT current_balance FROM reconciliation WHERE account=? AND period_end < ? ORDER BY period_end DESC LIMIT 1", (account, period_start)).fetchone()
    opening = prev[0] if prev else 0
    # Cash in / out from transactions (use direction, amount; assume all apply to selected account for demo)
    tx_rows = c.execute("SELECT id, tx_type, amount, direction, status, order_id, external_id FROM transactions WHERE (created_at >= ? AND created_at < ?) OR (created_at IS NULL) ORDER BY created_at DESC", (period_start, period_end)).fetchall()
    # For simplicity include all transactions in period; compute sums from direction
    total_in = sum((r[2] or 0) for r in tx_rows if r[3]=="in")
    total_out = sum((r[2] or 0) for r in tx_rows if r[3]=="out")
    current = opening + total_in - total_out
    # Flag unmatched: any transaction without order_id and status Draft could be unmatched
    flags = []
    for r in tx_rows:
        if (r[4]=="Draft" or r[4]=="Reversed") and not r[5]:
            flags.append(r)
    c.close()
    return render_template("reconciliation.html", account=account, period_start=period_start, period_end=period_end,
                           opening=opening, total_in=total_in, total_out=total_out, current=current,
                           tx_rows=tx_rows, flags=flags, role=session.get("role"))

@recon_bp.route("/save", methods=["POST"])
def save():
    c = conn(); account = request.form.get("account","Cash")
    start = request.form.get("period_start"); end = request.form.get("period_end")
    # Recompute
    prev = c.execute("SELECT current_balance FROM reconciliation WHERE account=? AND period_end < ? ORDER BY period_end DESC LIMIT 1", (account, start)).fetchone()
    opening = prev[0] if prev else 0
    tx_rows = c.execute("SELECT amount, direction FROM transactions WHERE created_at >= ? AND created_at < ?", (start, end)).fetchall()
    total_in = sum((r[0] or 0) for r in tx_rows if r[1]=="in")
    total_out = sum((r[0] or 0) for r in tx_rows if r[1]=="out")
    current = opening + total_in - total_out
    unmatched = ""  # placeholder
    c.execute("INSERT INTO reconciliation (account,period_start,period_end,opening_balance,total_cash_in,total_cash_out,current_balance,unmatched_items,reconciled_by,reconciled_at) VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))",
              (account, start, end, opening, total_in, total_out, current, unmatched, session.get("username") or session.get("role","User")))
    c.commit(); c.close()
    flash("Reconciled and saved","ok"); return redirect(url_for("reconciliation.index", account=account, period_start=start, period_end=end))

@recon_bp.route("/api/period")
def api_period():
    c = conn(); cur = c.execute("SELECT account, period_start, period_end, opening_balance, total_cash_in, total_cash_out, current_balance FROM reconciliation ORDER BY created_at DESC LIMIT 20"); rows=cur.fetchall(); cols=[d[0] for d in cur.description]; c.close()
    return jsonify([{cols[i]: r[i] for i in range(len(cols))} for r in rows])
