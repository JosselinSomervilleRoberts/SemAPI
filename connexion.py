# -*- coding: utf-8 -*-
import psycopg2
import numpy as np

class DbConnexion:

    def __init__(self):
        self.HOST = "localhost"
        self.USER = "postgres"
        self.PASSWORD = "admin"
        self.DATABASE = "word2vec"
        self.connexion = None
        self.cursor = None

    def connect(self):
        self.connexion = psycopg2.connect("host=%s dbname=%s user=%s password=%s" % (self.HOST, self.DATABASE, self.USER, self.PASSWORD))
        self.cursor = self.connexion.cursor()

    def disconnect(self):
        self.connexion.commit()
        self.connexion.close()

    