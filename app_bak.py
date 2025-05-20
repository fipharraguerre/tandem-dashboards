from flask import Flask, render_template, request, Response, session, redirect, url_for
import mariadb
import datetime
import os
import time
from dateutil import parser
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler

# Configuración del logger
log_file = "app.log"
logger = logging.getLogger("MyAppLogger")
logger.setLevel(logging.DEBUG)  # Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Rotating File Handler
handler = RotatingFileHandler(log_file, maxBytes=1 * 1024 * 1024, backupCount=5)  # 1 MB, 5 backups
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Agregar el handler al logger
logger.addHandler(handler)

# Ejemplo de uso
logger.debug("Esto es un mensaje de debug")
logger.info("Esto es un mensaje de info")
logger.warning("Esto es un mensaje de warning")
logger.error("Esto es un mensaje de error")
logger.critical("Esto es un mensaje crítico")

app = Flask(__name__)

app.secret_key = os.urandom(32)  # Needed for session management

MAX_ATTEMPTS = 10
LOCKOUT_TIME = 1  # Lockout time in seconds

def check_auth(username, password):
    return username == 'admin' and password == "Tandem228" #os.getenv('ADMIN_PASSWORD')

def failed_login():
    # Check if user is locked out
    if 'lockout_time' in session and time.time() < session['lockout_time']:
        print(f"User is locked out. Current time: {time.time()} Lockout time: {session['lockout_time']}")
        return True
    
    # Increment failed attempts
    session['failed_logins'] = session.get('failed_logins', 0) + 1
    print(f"Failed logins incremented: {session['failed_logins']}")

    # Lockout if attempts exceed the maximum allowed
    if session['failed_logins'] >= MAX_ATTEMPTS:
        session['lockout_time'] = time.time() + LOCKOUT_TIME
        print(f"User locked out. Current time: {time.time()} Lockout time set to: {session['lockout_time']}")
        session['failed_logins'] = 0  # Reset the failed login counter after lockout
        return True

    return False

def authenticate():
    return 'Authentication required 😠', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}

def nl2br(value):
    # Ensure that we consistently handle different types of newline characters
    value = value.replace('\r\n', '\n').replace('\r', '\n')
    # Split the text into lines
    lines = value.split('\n')
    # Add a bullet/emoji only for non-empty lines and join them with <br>
    formatted_text = '<br>\n'.join([f"- {line.strip()}" for line in lines if line.strip()])
    return formatted_text
app.jinja_env.filters['nl2br'] = nl2br

# arreglar la fecha
def parse_creationtime(creationtime_str):
    try:
        # Try to parse as Unix timestamp (milliseconds)
        timestamp = int(creationtime_str) / 1000
        return datetime.datetime.fromtimestamp(timestamp)
    except ValueError:
        # If that fails, try to parse as ISO 8601 date string
        return parser.isoparse(creationtime_str)

# Configuración de la conexión a la base de datos
def get_db():
    return mariadb.connect(
        user='facundo',
        password='myPassword',
        host='vps-tandem.facundoitest.space',
        database='VeeamReports'
    )

# actualizar los contadores de las tarjetas
def update_client_status():
    db = get_db()
    cursor = db.cursor()

    # Obtener todos los clientes
    cursor.execute("SELECT nombre FROM clientes")
    clients = cursor.fetchall()

    for client in clients:
        client_name = client[0]

        # Obtener todos los hostnames asociados a este cliente
        cursor.execute("SELECT host_name FROM client_hosts WHERE client_name = %s", (client_name,))
        hostnames = cursor.fetchall()

        # Inicializar las variables para contadores de Backup Jobs
        success_count_backup = 0
        warn_count_backup = 0
        fail_count_backup = 0

        # Inicializar las variables para contadores de Tiering Jobs
        success_count_tiering = 0
        warn_count_tiering = 0
        fail_count_tiering = 0

        # Variable to store the latest datetime value
        last_seen = None

        # Inicializar mensaje para "VeeamConfigurationBackup"
        config_backup_status = None

        # Recorrer cada hostname y consultar sus resultados
        for host in hostnames:
            host_name = host[0]

            # Acumular para BackupJob y Backup
            cursor.execute(f"""
                SELECT
                    SUM(CASE WHEN result IN ('Success', 'ok', 'Completed') AND type LIKE '%Backup%' THEN 1 ELSE 0 END) AS success_count_backup,
                    SUM(CASE WHEN result = 'Warn' AND type LIKE '%Backup%' THEN 1 ELSE 0 END) AS warn_count_backup,
                    SUM(CASE WHEN result = 'Fail' AND type LIKE '%Backup%' THEN 1 ELSE 0 END) AS fail_count_backup,
                    MAX(datetime) AS last_seen_backup  -- Get the latest datetime for this host
                FROM `{host_name}`
            """)
            result_backup = cursor.fetchone()
            success_count_backup += result_backup[0]
            warn_count_backup += result_backup[1]
            fail_count_backup += result_backup[2]

            # Update last_seen if last_seen_backup is more recent
            if result_backup[3]:  # and (last_seen is None or result_backup[3] > last_seen):
                last_seen = result_backup[3]

            # Acumular para TieringJob
            cursor.execute(f"""
                SELECT
                    SUM(CASE WHEN result IN ('Success', 'ok', 'Completed') AND type = 'TieringJob' THEN 1 ELSE 0 END) AS success_count_tiering,
                    SUM(CASE WHEN result = 'Warn' AND type = 'TieringJob' THEN 1 ELSE 0 END) AS warn_count_tiering,
                    SUM(CASE WHEN result = 'Fail' AND type = 'TieringJob' THEN 1 ELSE 0 END) AS fail_count_tiering,
                    MAX(datetime) AS last_seen_tiering  -- Get the latest datetime for this host
                FROM `{host_name}`
            """)
            result_tiering = cursor.fetchone()
            success_count_tiering += result_tiering[0]
            warn_count_tiering += result_tiering[1]
            fail_count_tiering += result_tiering[2]

            # Update last_seen if last_seen_tiering is more recent
            if result_tiering[3]:  # and (last_seen is None or result_tiering[3] > last_seen):
                last_seen = result_tiering[3]

            # Obtener estado de VeeamConfigurationBackup
            cursor.execute(f"""
                SELECT result
                FROM `{host_name}`
                WHERE type = 'VeeamConfigurationBackup'
                ORDER BY datetime DESC
                LIMIT 1
            """)
            result_config_backup = cursor.fetchone()
            if result_config_backup:
                config_backup_status = result_config_backup[0]  # Guardar el último estado encontrado

        # Actualizar el estado del cliente basado en los resultados para BackupJob y Backup
        if fail_count_backup > 0:
            estado = 'fail'
            statusMsg1 = f'{fail_count_backup} job(s) failed in the last 24 hours'
        elif warn_count_backup > 0:
            estado = 'warn'
            statusMsg1 = f'{warn_count_backup} Warning(s) in the last 24 hours'
        else:
            estado = 'ok'
            statusMsg1 = f'{success_count_backup} jobs were successful in the last 24 hours'

        # Configurar el mensaje para TieringJob
        if fail_count_tiering > 0:
            statusMsg2 = f'{fail_count_tiering} offload(s) failed in the last 24 hours'
            # si los backups concluyeron bien pero fallaron los offloads, marcar estado warn
            if estado == 'ok':
                estado = 'warn'
        elif warn_count_tiering > 0:
            statusMsg2 = f'{warn_count_tiering} warning(s) in the last 24 hours'
        elif success_count_tiering > 0:
            statusMsg2 = f'{success_count_tiering} offload(s) were successful in the last 24 hours'
        else:
            statusMsg2 = 'N/A'

        # Guardar el mensaje y el estado en la tabla clientes
        cursor.execute("""
            UPDATE clientes 
            SET estado = %s, msgA = %s, msgB = %s, msgC = %s, last_seen = %s
            WHERE nombre = %s
        """, (estado, statusMsg1, statusMsg2, config_backup_status, last_seen, client_name))

        db.commit()

@app.route('/')
def index():
    update_client_status()  # Actualizar el estado de los clientes antes de cargar el dashboard
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT nombre, estado, msgA, msgB, last_seen, msgC FROM clientes")
    data = cursor.fetchall()
    return render_template('index.html', data=data)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    auth = request.authorization

    if failed_login():
        return 'Too many failed attempts. Try again later.', 403

    if not auth or not check_auth(auth.username, auth.password):
        failed_login()
        return authenticate()

    # Reset failed login attempts on successful login
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

@app.route('/admin/add_client', methods=['POST'])
def add_client():
    client_name = request.form['new_client_name']
    db = get_db()
    cursor = db.cursor()

    cursor.execute("INSERT INTO clientes (nombre) VALUES (%s)", (client_name,))
    db.commit()

    return redirect(url_for('admin'))

@app.route('/admin/delete_client', methods=['POST'])
def delete_client():
    client_name = request.form['delete_client_name']
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM clientes WHERE nombre = %s", (client_name,))
    db.commit()

    return redirect(url_for('admin'))

@app.route('/status/<client_name>')
def client_status(client_name):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT host_name FROM client_hosts WHERE client_name = %s", (client_name,))
    host_names = cursor.fetchall()

    results = []
    for host_name in host_names:
        cursor.execute(f"SELECT datetime, vmname, type, result, detail FROM `{host_name[0]}`")
        host_results = cursor.fetchall()

    # Obtener resultados de las tablas asociadas a los hostnames
    results = []
    history_data = []
    for host_name in host_names:
        cursor.execute(f"SELECT datetime, vmname, type, result, detail FROM `{host_name[0]}`")
        host_results = cursor.fetchall()

        for result in host_results:
            results.append((result[0], result[1], result[2], result[3], result[4]))

        cursor.execute("""
            SELECT datetime, descriptor, value
            FROM history
            WHERE hostname = %s AND datetime >= NOW() - INTERVAL 7 DAY
            ORDER BY datetime ASC
        """, (host_name[0],))
        history_results = cursor.fetchall()

        for row in history_results:
            # Si la fecha ya es un objeto datetime, solo la formateamos. Si no, usamos el valor tal cual.
            date = row[0] if isinstance(row[0], datetime) else datetime.fromisoformat(row[0])

            history_data.append({
                'datetime': date.strftime('%Y-%m-%d'),  # Solo la fecha (sin hora)
                'descriptor': row[1],
                'value': row[2],
                'hostname': host_name[0]
            })

        # Log para ver cómo quedaron los datos
        logger.debug(history_data)

        return render_template('client_status.html', client_name=client_name, results=results, history_data=history_data)

@app.route('/unsuccessful_tasks')
def unsuccessful_tasks():
    db = get_db()
    cursor = db.cursor()

    # Query the doomed_tasks table for unsuccessful tasks
    cursor.execute("SELECT hostname, datetime, vmname, type, result, detail FROM doomed_tasks ORDER BY datetime desc")
    data = cursor.fetchall()

    results = []
    for row in data:
        results.append((row[0], row[1], row[2], row[3], row[4], row[5]))

    return render_template('unsuccessful_tasks.html', results=results)


if __name__ == "__main__":
    app.run(debug=True, port=5050, host='0.0.0.0')

