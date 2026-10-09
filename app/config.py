"""Configuration — design tokens, DB path, roles, roles lock (§DESIGN_SPEC 3.3/149/158-171/239)."""
import os
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "sola_finance.db")
DB_PATH = os.path.abspath(DB_PATH)
SECRET_KEY = os.environ.get("SECRET_KEY", "sola-finance-dev-key-change")
DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"

BRAND = "#CCA300"
NAVY = "#0F172A"
STATUS_OK = "#16A34A"; STATUS_WARN = "#F59E0B"; STATUS_ERR = "#DC2626"; STATUS_INFO = "#0EA5E9"
BORDER = "#E2E8F0"; BG = "#F8FAFC"; SURFACE = "#FFFFFF"
FOCUS_RING = "3px #CCA300 at 20% opacity"
INPUT_H = 36; INPUT_BORDER = "1px #E2E8F0"; CARD_RADIUS = 12

# Roles (§1.6 / §3.3 / 149 / 158-171 / 239)
ROLE_FINANCE = "Finance"
ROLE_NONFINANCE = "Non-Finance"
ROLE_CUSTOMER = "Customer"

# Lock matrix (P0): Finance sees HPP/margin/price/invoice/payment; Non-finance hides
FINANCE_VISIBLE = {"hpp","margin","price","invoice","payment","reports","transactions","accounting"}
NONFINANCE_VISIBLE = {"dashboard","reports_light","transactions_view","customer_aging"}
CUSTOMER_VISIBLE = {"customer_aging","customer_payments","dashboard"}
