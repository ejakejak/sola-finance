from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, Response
import csv, io
from db import conn

tx_bp = Blueprint("transactions", __name__, url_prefix="/transactions")

@tx_bp.route("/")
def index():
    c = conn(); rows = c.execute("SELECT t.id, t.tx_type, t.amount, t.direction, t.status, t.external_id, t.order_id, t.reference, u.username FROM transactions t LEFT JOIN users u ON t.created_by=u.id ORDER BY t.created_at DESC LIMIT 50").fetchall()
    orders = c.execute("SELECT id, order_number, customer FROM orders ORDER BY order_number").fetchall(); c.close()
    return render_template("transactions.html", txs=rows, orders=orders, role=session.get("role"))

@tx_bp.route("/add", methods=["POST"])
def add():
    # Receipt / Expense / Transfer / Adjustment (ARTIFACT-A/C)
    tx_type = request.form.get("tx_type"); amount = float(request.form.get("amount") or 0)
    status = request.form.get("status","Draft")  # Draft vs Posted visible (P0)
    ext_id = request.form.get("external_id") or None
    order_id = int(request.form.get("order_id") or 0) or None
    c = conn()
    c.execute("INSERT INTO transactions (tx_type,amount,status,external_id,order_id,created_by) VALUES (?,?,?,?,?,?)",
              (tx_type, amount, status, ext_id, order_id, None))
    txid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.execute("INSERT INTO transactions_audit (tx_id,action,note) VALUES (?,?,?)",(txid,"created","P0 add"))
    if order_id:
        from app.routes.orders import _recalc_order
        _recalc_order(c, order_id)
    c.commit(); c.close()
    flash("Transaction saved (draft/post state visible)", "ok")
    return redirect(url_for("transactions.index"))

@tx_bp.route("/reversal/<int:id>", methods=["POST"])
def reversal(id):
    c = conn(); c.execute("UPDATE transactions SET status='Reversed' WHERE id=?",(id,));
    c.execute("INSERT INTO transactions_audit (tx_id,action,note) VALUES (?,?,?)",(id,"reversed","P0 reversal"))
    c.commit(); c.close(); flash("Reversed with audit log","ok"); return redirect(url_for("transactions.index"))

@tx_bp.route("/export")
def export():
    c = conn(); cur = c.execute("SELECT * FROM transactions WHERE status='Posted' LIMIT 500"); rows = cur.fetchall(); cols = [d[0] for d in cur.description]; c.close()
    out = io.StringIO(); w = csv.writer(out); w.writerow(cols)
    for r in rows: w.writerow(r)
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=transactions.csv"})

@tx_bp.route("/api/list")
def api_list():
    c = conn(); cur = c.execute("SELECT * FROM transactions WHERE status='Posted' LIMIT 100"); r = cur.fetchall(); cols=[d[0] for d in cur.description]; c.close()
    return jsonify([{cols[i]: row[i] for i in range(len(cols))} for row in r])
