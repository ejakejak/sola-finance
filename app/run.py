"""Flask 3.1.1 entry. Role lock (§DESIGN_SPEC 3.3/149/158-171/239), all blueprints."""
from flask import Flask, session, redirect, url_for, request
from app.config import SECRET_KEY, DEBUG

def create_app():
    from db import init; init()
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = SECRET_KEY; app.debug = DEBUG
    # role guard helper stored on app
    @app.context_processor
    def inject():
        role = session.get("role","Non-Finance")
        return dict(role=role,
                    is_finance=(role=="Finance"),
                    is_customer=(role=="Customer"),
                    brand="#CCA300")
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.reports import reports_bp
    from app.routes.transactions import tx_bp as transactions_bp
    from app.routes.invoices import invc_bp as invoices_bp
    from app.routes.payments import pay_bp as payments_bp
    from app.routes.finance import finance_bp
    from app.routes.accounting import acc_bp as accounting_bp
    from app.routes.orders import orders_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(accounting_bp)
    app.register_blueprint(orders_bp)
    from app.routes.reconciliation import recon_bp
    app.register_blueprint(recon_bp)
    from app.routes.aging import aging_bp
    app.register_blueprint(aging_bp)
    @app.errorhandler(404)
    def e404(e): return "Not found", 404
    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000, debug=True)
