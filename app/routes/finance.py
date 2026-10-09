from flask import Blueprint, render_template, session
from app.config import FINANCE_VISIBLE, NONFINANCE_VISIBLE, CUSTOMER_VISIBLE
finance_bp = Blueprint("finance", __name__, url_prefix="/finance")

@finance_bp.route("/")
def index():
    role = session.get("role","Non-Finance")
    if role not in ("Finance",):
        return render_template("errors.html", msg="Finance module blocked for %s (role lock §DESIGN_SPEC 149/158-171/239)"%role), 403
    # HPP / margin / price role-blocked for non-finance
    return render_template("finance.html", role=role)
