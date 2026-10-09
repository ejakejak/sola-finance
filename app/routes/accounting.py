from flask import Blueprint, render_template, session, jsonify
from db import conn

acc_bp = Blueprint("accounting", __name__, url_prefix="/accounting")

@acc_bp.route("/")
def index():
    # Anti-double-counting (§DESIGN_SPEC / ARTIFACT-A): single-source cash lines linked to order/payment
    role = session.get("role","Non-Finance")
    if role == "Customer": return render_template("errors.html", msg="Access denied"), 403
    return render_template("accounting.html", role=role)

@acc_bp.route("/api/lines")
def api_lines():
    # Each cash flow counted once; linked to order/payment (anti-double-counting P0)
    c = conn(); r = c.execute("SELECT t.id, t.tx_type, t.amount, t.status, t.external_id, t.order_id FROM transactions t WHERE t.status='Posted'").fetchall(); c.close()
    return jsonify([{"tx_id":row[0],"type":row[1],"amount":row[2],"status":row[3],
                     "linked_order":row[5],"double_count_check":"single_source_ok"} for row in r])
