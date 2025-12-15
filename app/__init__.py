from flask import Flask, g
import pymysql
# Monkey patch MySQLdb to allow using pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
from config import Config

class MySQL:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        # Store config for connection
        self.host = app.config.get('MYSQL_HOST', 'localhost')
        self.user = app.config.get('MYSQL_USER')
        self.password = app.config.get('MYSQL_PASSWORD')
        self.db = app.config.get('MYSQL_DB')
        self.cursor_class = app.config.get('MYSQL_CURSORCLASS', 'DictCursor')

    @property
    def connection(self):
        # Open a new connection if one doesn't exist for this request
        if 'db_conn' not in g:
            g.db_conn = MySQLdb.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db,
                cursorclass=getattr(MySQLdb.cursors, self.cursor_class, MySQLdb.cursors.DictCursor)
            )
        return g.db_conn

mysql = MySQL()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize shim
    mysql.init_app(app)

    # Add teardown to close connection
    @app.teardown_appcontext
    def close_db(error):
        db = g.pop('db_conn', None)
        if db is not None:
            db.close()

    from app import routes
    app.register_blueprint(routes.bp)

    return app
