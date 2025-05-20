from flask import Blueprint, render_template
from db import get_db
from core import update_client_status

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
def index():
    update_client_status()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT nombre, estado, msgA, msgB, last_seen, msgC FROM clientes")
    data = cursor.fetchall()
    return render_template('index.html', data=data)
