import os

class Config():
    # API Settings
    API_PORT = None
    SECRET_KEY = None
    DEBUG = False
    TESTING = False

    # Project Settings
    PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # SQL Settings
    DB_HOST = None
    DB_USER = None
    DB_PASSWORD = None