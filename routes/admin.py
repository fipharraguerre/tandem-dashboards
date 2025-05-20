from flask import Blueprint, request, render_template, redirect, url_for, session
from db import get_db
from auth import check_auth, failed_login, authenticate

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/', methods=['GET', 'POST'])
def admin():
    auth = request.authorization

    if failed_login():
        return 'Too many failed attempts. Try again later.', 403

    if not auth or not check_auth(auth.username, auth.password):
        failed_login()
        return authenticate()

    session['failed_logins'] = 0
    session.pop('lockout_time', None)

    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        client_name = request.form['client_name']
        host_name = request.form['host_name']
        cursor.execute("INSERT INTO client_hosts (client_name, host_name) VALUES (%s, %s)", (client_name, host_name))
        db.commit()

    cursor.execute("SELECT nombre FROM clientes")
    clients = cursor.fetchall()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    cursor.execute("SELECT client_name, host_name FROM client_hosts")
    client_host_relations = cursor.fetchall()

    return render_template('admin.html', clients=clients, tables=tables, client_host_relations=client_host_relations)

@admin_bp.route('/add_client', methods=['POST'])
def add_client():
    db = get_db()
    cursor = db.cursor()
    client_name = request.form['new_client_name']
    cursor.execute("INSERT INTO clientes (nombre) VALUES (%s)", (client_name,))
    db.commit()
    return redirect(url_for('admin.admin'))

@admin_bp.route('/delete_client', methods=['POST'])
def delete_client():
    db = get_db()
    cursor = db.cursor()
    client_name = request.form['delete_client_name']
    cursor.execute("DELETE FROM clientes WHERE nombre = %s", (client_name,))
    db.commit()
    return redirect(url_for('admin.admin'))
