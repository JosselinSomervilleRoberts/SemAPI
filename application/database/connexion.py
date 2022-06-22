# -*- coding: utf-8 -*-
import psycopg2
from config import Config

class DbConnexion:

    def __init__(self, config: Config):
        self.HOST = config.DB_HOST
        self.USER = config.DB_USER
        self.PASSWORD = config.DB_PASSWORD
        self.DATABASE = "word2vec"
        self.connexion = None
        self.cursor = None
        self.lang = "fr"

    def execute(self, request: str, args = None):
        request.replace("fr_", self.lang + "_")
        self.cursor.execute(request, args)

    def connect(self):
        self.connexion = psycopg2.connect("host=%s dbname=%s user=%s password=%s" % (self.HOST, self.DATABASE, self.USER, self.PASSWORD))
        self.cursor = self.connexion.cursor()

    def disconnect(self):
        self.connexion.commit()
        self.connexion.close()

    def rollback(self):
        self.cursor.execute("ROLLBACK")
        self.connexion.commit()

    