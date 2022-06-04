import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_PATH, '../'))

import numpy as np
from utils.word_utils import remove_accents
from db.connexion import DbConnexion


class Lemma:

    def __init__(self):
        self.id = None
        self.lemma = None
        self.lemma_na = None
        self.type = None
        self.freq = 0
        self.vector = None
        self.comparator = 0

    def load_from_json(self, data: dict) -> None:
        self.id = data['id']
        self.lemma = data['lemma']
        self.lemma_na = data['lemma_na']
        self.type = data['type']
        self.freq = data['freq']
        self.vector = data['vector']

    def load_all(db: DbConnexion):# -> List[Lemma]:
        LIMIT = 5000
        last_id = -1
        lemmas = []
        res = [None]
        print("Loading all lemmas ", end = "")

        while len(res) > 0:
            print(".", end="")
            db.cursor.execute("""SELECT lemma_id, lemma, lemma_na, type, freq, vector
                                FROM public.fr_lemmas
                                WHERE lemma_id > %s 
                                ORDER BY lemma_id ASC LIMIT %s""",
                                (last_id, LIMIT))
            res = db.cursor.fetchall()
            
            for row in res:
                last_id = int(row[0])
                data = {"id": int(row[0]), "lemma": row[1], "lemma_na": row[2], "type": row[3], "freq": float(row[4]), "vector": np.array(row[5])}
                lemma = Lemma()
                lemma.load_from_json(data)
                lemmas.append(lemma)
        print("")
        return lemmas

    def load_from_db_res(self, db: DbConnexion) -> None:
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("Could not load Lemma")
        self.id = res[0]
        self.lemma = res[1]
        self.lemma_na = res[2]
        self.type = res[3]
        self.freq = float(res[4])
        self.vector = np.array(res[5])

    def load_from_id(self, db: DbConnexion, id: int) -> None:
        if id is None:
            raise Exception("Cannot load Lemma from id if the id is not set. (id: %d)" % (id))
        db.cursor.execute("""SELECT lemma_id, lemma, lemma_na, type, freq, vector
                            FROM public.fr_lemmas 
                            WHERE lemma_id = %s""",
                            (id,))
        self.load_from_db_res(db)
        
    def load_from_word(self, db: DbConnexion, word: str) -> None:
        word_na = remove_accents(word)
        if word is None:
            raise Exception("Cannot load Lemma from word if word is not set. (word: %s)" % (word))
        db.cursor.execute("""SELECT lemma_id, lemma, lemma_na, type, freq, vector
                            FROM public.fr_lemmas 
                            WHERE lemma_na = %s""",
                            (word_na,))
        self.load_from_db_res(db)

    def load_like_word(self, db: DbConnexion, word: str) -> None:
        word_na = remove_accents(word)
        if word is None:
            raise Exception("Cannot load Lemma like word if word is not set. (word: %s)" % (word))
        db.cursor.execute("""SELECT lemma_id, lemma, lemma_na, type, freq, vector
                            FROM public.fr_lemmas 
                            WHERE lemma_na LIKE = %s
                            ORDER BY freq  DESC LIMIT 1""",
                            ("%" + word_na + "%",))
        self.load_from_db_res(db)
        
    def __eq__(self, other) -> bool:
        if not isinstance(other, Lemma):
            raise Exception("Lemma are only comparable to Lemma, not to {0}".format(type(other)))
        else:
            return self.id.__eq__(other.id)

    def __gt__(self, other) -> bool:
        if not isinstance(other, Lemma):
            raise Exception("Lemma are only comparable to Lemma, not to {0}".format(type(other)))
        else:
            return self.comparator.__gt__(other.comparator)

    def __lt__(self, other) -> bool:
        if not isinstance(other, Lemma):
            raise Exception("Lemma are only comparable to Lemma, not to {0}".format(type(other)))
        else:
            return self.comparator.__lt__(other.comparator)

    def __str__(self) -> str:
        return str(self.lemma)

    def __repr__(self) -> str:
        return str(self)