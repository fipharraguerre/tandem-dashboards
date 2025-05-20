from flask import Blueprint, render_template
from db import get_db

unsuccessful_bp = Blueprint('unsuccessful', __name__)

@unsuccessful_bp.route('/unsuccessful_tasks')
def unsuccessful_tasks():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT hostname, datetime, vmname, type, result, detail FROM doomed_tasks ORDER BY datetime desc")
    data = cursor.fetchall()
    return render_template('unsuccessful_tasks.html', results=data)
