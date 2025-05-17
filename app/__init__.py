from flask import Flask
import cx_Oracle
import traceback
from config import ORACLE_USERNAME, ORACLE_PASSWORD, ORACLE_DSN, SECRET_KEY

def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    try:
        connection = cx_Oracle.connect(
            ORACLE_USERNAME,
            ORACLE_PASSWORD,
            ORACLE_DSN
        )
        app.config['DB_CONN'] = connection
    except cx_Oracle.Error as error:
        print("❌ Failed to connect to Oracle DB:")
        traceback.print_exc()

    from .routes import main
    app.register_blueprint(main)

    return app
