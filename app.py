from flask import Flask
from routes.index import index_bp
from routes.admin import admin_bp
from routes.status import status_bp
from routes.unsuccessful import unsuccessful_bp
from logger import logger
from auth import nl2br
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'valor-inseguro-default')

app.jinja_env.filters['nl2br'] = nl2br

# Registrar blueprints
app.register_blueprint(index_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(status_bp)
app.register_blueprint(unsuccessful_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5050, host='0.0.0.0')
