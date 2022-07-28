from flask import Flask
from config import Config
from database import DbConnexion

def create_app(config: Config):
    app = Flask(__name__)
    app.debug = config.DEBUG
    db = DbConnexion(config)
    return app