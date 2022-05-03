# -*- coding: utf-8 -*-
import psycopg2
import os
from dotenv import load_dotenv

class DbConnexion:

    def __init__(self):
        self.HOST = os.getenv('DB_HOST')
        self.USER = os.getenv('DB_USER')
        self.PASSWORD = os.getenv('DB_PASSWORD')
        self.DATABASE = "word2vec"
        self.connexion = None
        self.cursor = None

    def connect(self):
        self.connexion = psycopg2.connect("host=%s dbname=%s user=%s password=%s" % (self.HOST, self.DATABASE, self.USER, self.PASSWORD))
        self.cursor = self.connexion.cursor()

    def disconnect(self):
        self.connexion.commit()
        self.connexion.close()

    