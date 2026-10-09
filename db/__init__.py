import sqlite3,os
from app.config import DB_PATH
def conn():
    connection=sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False); connection.row_factory=sqlite3.Row; return connection
def init():
    from db.migrate import migrate
    migrate()
