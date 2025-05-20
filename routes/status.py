from flask import Blueprint, render_template
from db import get_db
from logger import logger
from datetime import datetime

status_bp = Blueprint('status', __name__)

@status_bp.route('/status/<client_name>')
def client_status(client_name):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT host_name FROM client_hosts WHERE client_name = %s", (client_name,))
    host_names = cursor.fetchall()

    results = []
    history_data = []

    for host_name in host_names:
        cursor.execute(f"SELECT datetime, vmname, type, result, detail FROM `{host_name[0]}`")
        results += cursor.fetchall()

        cursor.execute("""
            SELECT datetime, descriptor, value
            FROM history
            WHERE hostname = %s AND datetime >= NOW() - INTERVAL 7 DAY
            ORDER BY datetime ASC
        """, (host_name[0],))
        history_results = cursor.fetchall()

        for row in history_results:
            date = row[0] if isinstance(row[0], datetime) else datetime.fromisoformat(row[0])
            history_data.append({
                'datetime': date.strftime('%Y-%m-%d'),
                'descriptor': row[1],
                'value': row[2],
                'hostname': host_name[0]
            })

    logger.debug(history_data)

    return render_template('client_status.html', client_name=client_name, results=results, history_data=history_data)
