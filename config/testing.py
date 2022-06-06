from config import Config
from dotenv import load_dotenv
import os

class TestingConfig(Config):
    load_dotenv(Config.PROJECT_PATH + '.env.testing')

    # API Settings
    API_PORT = os.getenv('API_PORT')
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = False
    TESTING = True

    # SQL Settings
    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')