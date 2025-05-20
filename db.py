import mariadb
import os

def get_db():
    return mariadb.connect(
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME']
    )
