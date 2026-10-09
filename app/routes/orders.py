"""Order Costing Module (P1 Task 1)."""
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from db import conn

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")

def _recalc_order(c, order_id):
    row = c.execute("SELECT estimated_cost FROM orders WHERE id=?", (order_id,)).fetchone()
    if not row:
        return
    est = row[0] or 0
    # Sum linked transactions amounts
    tx_sum = c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE order_id=? AND status!='Reversed'", (order_id,)).fetchone()[0]
    c.execute("UPDATE orders SET actual_cost=? WHERE id=?", (tx_sum, order_id))
    # Status logic
    if est > 0 and tx_sum >= est:
        status = "Over Budget"
    elif est > 0 and tx_sum <= est * 0.9:
        status = "On Track"
    else:
        status = "Estimated"
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))

@orders_bp.route("/")
def index():
    c = conn()
    rows = c.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    # For finance role visibility of cost details; all can see orders
    c.close()
    return render_template("orders.html", orders=rows, role=session.get("role"), is_finance=(session.get("role")=="Finance"))

@orders_bp.route("/add", methods=["POST"])
def add():
    c = conn()
    c.execute("INSERT INTO orders (order_number,customer,description,estimated_cost,status) VALUES (?,?,?,?,?)",
              (request.form.get("order_number"), request.form.get("customer"), request.form.get("description"),
               float(request.form.get("estimated_cost") or 0), "Estimated"))
    c.commit(); c.close()
    flash("Order added","ok"); return redirect(url_for("orders.index"))

@orders_bp.route("/edit/<int:id>", methods=["POST"])
def edit(id):
    c = conn()
    # Lock if finalized
    current = c.execute("SELECT status FROM orders WHERE id=?", (id,)).fetchone()
    if current and current[0] == "Finalized":
        flash("Order finalized — editing locked","err"); c.close(); return redirect(url_for("orders.index"))
    c.execute("UPDATE orders SET order_number=?, customer=?, description=?, estimated_cost=? WHERE id=?",
              (request.form.get("order_number"), request.form.get("customer"), request.form.get("description"),
               float(request.form.get("estimated_cost") or 0), id))
    _recalc_order(c, id)
    c.commit(); c.close()
    flash("Order updated","ok"); return redirect(url_for("orders.index"))

@orders_bp.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    c = conn(); c.execute("DELETE FROM orders WHERE id=?", (id,)); c.commit(); c.close()
    flash("Order deleted","ok"); return redirect(url_for("orders.index"))

@orders_bp.route("/finalize/<int:id>", methods=["POST"])
def finalize(id):
    c = conn()
    _recalc_order(c, id)
    c.execute("UPDATE orders SET status='Finalized' WHERE id=?", (id,))
    c.commit(); c.close()
    flash("Order finalized and locked","ok"); return redirect(url_for("orders.index"))

@orders_bp.route("/api/list")
def api_list():
    c = conn(); cur = c.execute("SELECT id, order_number, customer, description, estimated_cost, actual_cost, status FROM orders");
    rows = cur.fetchall(); cols = [d[0] for d in cur.description]; c.close()
    return jsonify([{cols[i]: r[i] for i in range(len(cols))} for r in rows])
