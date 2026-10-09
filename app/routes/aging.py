"""Customer Aging (P1 Task 3 + P2 Task 7)."""
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from db import conn
import datetime, csv, io

aging_bp = Blueprint("aging", __name__, url_prefix="/aging")

def _refresh_aging(c):
    # Clear and recompute from payments (unpaid / not verified / no proof?)
    # Simplified: use all payments grouped by party_name / customer reference
    # Use payments.customer_id joined with users to get name; if no user, use party
    c.execute("DELETE FROM customer_aging")
    # Group by customer from payments (use customer_id -> users.username or payments.party_name)
    rows = c.execute("""
        SELECT COALESCE(u.username, CAST(p.customer_id AS TEXT)) as customer,
               SUM(CASE WHEN p.created_at >= datetime('now','-30 days') THEN p.amount ELSE 0 END) as current,
               SUM(CASE WHEN p.created_at < datetime('now','-30 days') AND p.created_at >= datetime('now','-60 days') THEN p.amount ELSE 0 END) as day_30,
               SUM(CASE WHEN p.created_at < datetime('now','-60 days') AND p.created_at >= datetime('now','-90 days') THEN p.amount ELSE 0 END) as day_60,
               SUM(CASE WHEN p.created_at < datetime('now','-90 days') THEN p.amount ELSE 0 END) as day_90_plus
        FROM payments p LEFT JOIN users u ON p.customer_id=u.id
        GROUP BY customer
    """).fetchall()
    for r in rows:
        customer = r[0] or "Unknown"
        cur = r[1] or 0; d30 = r[2] or 0; d60 = r[3] or 0; d90 = r[4] or 0; total = cur+d30+d60+d90
        c.execute("INSERT INTO customer_aging (customer,current,day_30,day_60,day_90_plus,total) VALUES (?,?,?,?,?,?)",
                  (customer, cur, d30, d60, d90, total))

def _csv_export(rows, filename):
    out = io.StringIO(); w = csv.writer(out)
    w.writerow(["Customer","Current","30d","60d","90+","Total"])
    for r in rows:
        w.writerow([r[1], r[2], r[3], r[4], r[5], r[6]])
    return out.getvalue()

@aging_bp.route("/")
def index():
    c = conn(); period_start = request.args.get("period_start") or (datetime.date.today()-datetime.timedelta(days=90)).isoformat(); period_end = request.args.get("period_end") or datetime.date.today().isoformat()
    # Refresh on demand
    if request.args.get("refresh") == "1":
        _refresh_aging(c); c.commit()
    rows = c.execute("SELECT id, customer, current, day_30, day_60, day_90_plus, total FROM customer_aging ORDER BY total DESC").fetchall()
    c.close()
    return render_template("aging.html", rows=rows, period_start=period_start, period_end=period_end, role=session.get("role"))

@aging_bp.route("/refresh", methods=["POST"])
def refresh():
    c = conn(); _refresh_aging(c); c.commit(); c.close()
    flash("Aging refreshed","ok"); return redirect(url_for("aging.index"))

@aging_bp.route("/export")
def export():
    c = conn(); rows = c.execute("SELECT * FROM customer_aging ORDER BY total DESC").fetchall(); c.close()
    data = _csv_export(rows, "aging.csv")
    from flask import Response
    return Response(data, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=aging.csv"})

@aging_bp.route("/detail/<customer>")
def detail(customer):
    c = conn(); rows = c.execute("SELECT p.*, u.username FROM payments p LEFT JOIN users u ON p.customer_id=u.id WHERE COALESCE(u.username, CAST(p.customer_id AS TEXT))=? ORDER BY p.created_at DESC LIMIT 50", (customer,)).fetchall(); c.close()
    return render_template("aging.html", rows=[{"customer":customer}], detail=rows, detail_customer=customer, role=session.get("role"))
