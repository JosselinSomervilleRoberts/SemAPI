import numpy as np
from word_utils import remove_accents

class Lemma:

    def __init__(self):
        self.id = None
        self.lemma = None
        self.lemma_na = None
        self.type = None
        self.freq = 0
        self.vector = None

    def load_from_db_res(self, db):
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("Could not load Lemma")
        self.id = res[0]
        self.lemma = res[1]
        self.lemma_na = res[2]
        self.type = res[3]
        self.freq = float(res[4])
        self.vector = np.array(res[5])

    def load_from_id(self, db, id):
        if id is None:
            raise Exception("Cannot load Lemma from id if the id is not set. (id: %d)" % (id))
        db.cursor.execute("""SELECT lemma_id, lemma, lemma_na, type, freq, vector
                            FROM public.lemmas 
                            WHERE lemma_id = %s""",
                            (id,))
        self.load_from_db_res(db)
        
    def load_from_word(self, db, word):
        word_na = remove_accents(word)
        if word is None:
            raise Exception("Cannot load Lemma from word if word is not set. (word: %s)" % (word))
        db.cursor.execute("""SELECT lemma_id, lemma, lemma_na, type, freq, vector
                            FROM public.lemmas 
                            WHERE lemma_na = %s""",
                            (word_na,))
        self.load_from_db_res(db)

    def load_like_word(self, db, word):
        word_na = remove_accents(word)
        if word is None:
            raise Exception("Cannot load Lemma like word if word is not set. (word: %s)" % (word))
        db.cursor.execute("""SELECT lemma_id, lemma, lemma_na, type, freq, vector
                            FROM public.lemmas 
                            WHERE lemma_na LIKE = %s
                            ORDER BY freq  DESC LIMIT 1""",
                            ("%" + word_na + "%",))
        self.load_from_db_res(db)
        
    def __eq__(self, other):
        if not isinstance(other, Lemma):
            raise Exception("Lemma are only comparable to Lemma, not to {0}".format(type(other)))
        else:
            return self.id.__eq__(other.id)

    def __str__(self):
        return str(self.lemma)

    def __repr__(self):
        return str(self)