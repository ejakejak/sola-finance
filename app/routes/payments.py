from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, Response
import csv, io
from db import conn

pay_bp = Blueprint("payments", __name__, url_prefix="/payments")

@pay_bp.route("/")
def index():
    c = conn(); rows = c.execute("SELECT p.id, p.customer_id, p.supplier_id, p.amount, p.method, p.status, p.dp_amount, p.cicilan, p.partial, p.proof_path, p.verified_by, p.verified_at, p.created_at, u.username FROM payments p LEFT JOIN users u ON p.customer_id=u.id ORDER BY p.created_at DESC LIMIT 50").fetchall(); c.close()
    return render_template("payments.html", payments=rows, role=session.get("role"))

@pay_bp.route("/add", methods=["POST"])
def add():
    # DP / cicilan / partial / proof / verification (ARTIFACT-A)
    amt = float(request.form.get("amount") or 0); dp = float(request.form.get("dp_amount") or 0)
    cicilan = float(request.form.get("cicilan") or 0); partial = float(request.form.get("partial") or 0)
    proof = request.form.get("proof_path") or None
    c = conn()
    c.execute("INSERT INTO payments (customer_id,amount,method,status,dp_amount,cicilan,partial,proof_path) VALUES (?,?,?,?,?,?,?,?)",
              (1, amt, request.form.get("method","DP"), "Pending", dp, cicilan, partial, proof))
    c.commit(); c.close(); flash("Payment recorded (DP/cicilan/partial + proof)","ok")
    return redirect(url_for("payments.index"))

@pay_bp.route("/verify/<int:id>", methods=["POST"])
def verify(id):
    c = conn(); c.execute("UPDATE payments SET status='Verified',verified_by=1,verified_at=datetime('now') WHERE id=?",(id,)); c.commit(); c.close()
    flash("Verified","ok"); return redirect(url_for("payments.index"))

@pay_bp.route("/export")
def export():
    c = conn(); cur = c.execute("SELECT * FROM payments LIMIT 500"); rows = cur.fetchall(); cols = [d[0] for d in cur.description]; c.close()
    out = io.StringIO(); w = csv.writer(out); w.writerow(cols)
    for r in rows: w.writerow(r)
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=payments.csv"})

@pay_bp.route("/aging-refresh", methods=["POST"])
def aging_refresh():
    from app.routes.aging import _refresh_aging
    c = conn(); _refresh_aging(c); c.commit(); c.close()
    flash("Aging refreshed","ok"); return redirect(url_for("payments.index"))

@pay_bp.route("/api/balance")
def api_balance():
    c = conn(); r = c.execute("SELECT SUM(amount) s FROM payments WHERE status='Verified'").fetchone(); c.close()
    return jsonify({"verified_total": r[0] or 0})
