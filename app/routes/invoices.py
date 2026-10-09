from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from db import conn

invc_bp = Blueprint("invoices", __name__, url_prefix="/invoices")

@invc_bp.route("/")
def index():
    c = conn(); rows = c.execute("SELECT i.id, i.external_id, i.customer_id, i.amount, i.hpp, i.gross_profit, i.status, i.created_at, u.username FROM invoices i LEFT JOIN users u ON i.customer_id=u.id ORDER BY i.created_at DESC LIMIT 50").fetchall(); c.close()
    return render_template("invoices.html", invoices=rows, role=session.get("role"))

@invc_bp.route("/import", methods=["POST"])
def import_invoices():
    # Import/link by external ID; no duplicates (ARTIFACT-A + §10 P0)
    ext_id = request.form.get("external_id").strip()
    amount = float(request.form.get("amount") or 0)
    c = conn()
    existing = c.execute("SELECT id FROM invoices WHERE external_id=?",(ext_id,)).fetchone()
    if existing: flash("Duplicate blocked (external-ID linkage): %s" % ext_id,"warn")
    else:
        c.execute("INSERT INTO invoices (external_id,amount,status) VALUES (?,?,?)",(ext_id,amount,"Open"))
        # import log (separate from "Catat Transaksi")
        c.execute("INSERT OR IGNORE INTO invoices_import (external_id,source_file) VALUES (?,?)",(ext_id,"upload"))
        c.commit(); flash("Invoice imported (no duplicate)","ok")
    c.close()
    return redirect(url_for("invoices.index"))

@invc_bp.route("/api/link")
def api_link():
    q = request.args.get("external_id")
    c = conn(); r = c.execute("SELECT * FROM invoices WHERE external_id=?",(q,)).fetchone(); c.close()
    return jsonify({"linked": bool(r),"row": dict(r) if r else None, "duplicate_blocked": bool(r)})
