from flask import Flask
from flask_mysqldb import MySQL
from config import Config

mysql = MySQL()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    mysql.init_app(app)

    from app import routes
    app.register_blueprint(routes.bp)

    return app
