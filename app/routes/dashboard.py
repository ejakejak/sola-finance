from flask import Blueprint, render_template, session
from app.config import FINANCE_VISIBLE, NONFINANCE_VISIBLE, CUSTOMER_VISIBLE
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="")

@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def index():
    role = session.get("role","Non-Finance")
    if role == "Finance": visible = FINANCE_VISIBLE
    elif role == "Customer": visible = CUSTOMER_VISIBLE
    else: visible = NONFINANCE_VISIBLE
    return render_template("dashboard.html", role=role, visible=visible)
