import time
from flask import session

MAX_ATTEMPTS = 10
LOCKOUT_TIME = 1  # seconds

def check_auth(username, password):
    return username == 'admin' and password == "Tandem228"  # se puede mejorar luego con variables

def failed_login():
    if 'lockout_time' in session and time.time() < session['lockout_time']:
        return True
    
    session['failed_logins'] = session.get('failed_logins', 0) + 1

    if session['failed_logins'] >= MAX_ATTEMPTS:
        session['lockout_time'] = time.time() + LOCKOUT_TIME
        session['failed_logins'] = 0
        return True

    return False

def authenticate():
    return 'Authentication required 😠', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}

def nl2br(value):
    value = value.replace('\r\n', '\n').replace('\r', '\n')
    lines = value.split('\n')
    formatted_text = '<br>\n'.join([f"- {line.strip()}" for line in lines if line.strip()])
    return formatted_text
