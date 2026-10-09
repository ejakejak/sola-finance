from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from db import conn

auth_bp = Blueprint("auth", __name__, url_prefix="")

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        pw = request.form.get("password")  # dummy (design spec auth only requires role selection for P0)
        c = conn(); row = c.execute("SELECT username,role FROM users WHERE username=?",(u,)).fetchone(); c.close()
        if row: session["user"]=row[0]; session["role"]=row[1]; return redirect(url_for("dashboard.index"))
        flash("Login failed", "error")
    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout(): session.clear(); return redirect(url_for("auth.login"))

# quick role switch for demo (design verification)
@auth_bp.route("/set_role/<r>")
def set_role(r):
    if r in ("Finance","Non-Finance","Customer"): session["role"]=r
    return redirect(url_for("dashboard.index"))
