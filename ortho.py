from word_utils import lemmatize, isword, correct, remove_accents
from lemma import Lemma
import numpy as np
import bisect
import math
import collections
import tqdm
from scipy.spatial import distance


def distance_embeddings(emb1, emb2):
    return distance.cosine(emb1, emb2)

def naive_score_embeddings(emb1, emb2):
    return 1 - distance_embeddings(emb1, emb2)

class Ortho:

    SCORE_MAX_NEIGHBOR = 0.98
    SCORE_MIN_NEIGHBOR = 0.5
    SIMILIRARITY_MIN = 0.5
    SCORE_ZERO = 0.1

    def __init__(self):
        self.id = None
        self.ortho = None
        self.ortho_na = None
        self.lemma = None
        self.freq = 0
        self.number = None
        self.genre = None
        self.nb_syll = None
        self.nb_letters = None
        self.vector = None
        self.neighbors = None
        self.ref_score = 0

    def load_from_db_res(self, db):
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("Could not load Ortho")
        self.id = res[0]
        self.ortho = res[1]
        self.ortho_na = res[2]
        self.lemma = Lemma()
        self.lemma.load_from_id(res[3])
        self.freq = float(res[4])
        self.number = res[5]
        self.genre = res[6]
        self.nb_syll = int(res[7])
        self.nb_letters = int(res[8])
        self.vector = np.array(res[9])

    def load_from_id(self, db, id):
        if id is None:
            raise Exception("Cannot load Ortho from id if the id is not set. (id: %d)" % (id))
        db.cursor.execute("""SELECT ortho_id, ortho, ortho_na, lemma_id, freq, number, genre, nb_syll, nb_letters, vector
                            FROM public.orthos 
                            WHERE ortho_id = %s""",
                            (id,))
        self.load_from_db_res(db)
        
    def load_from_word(self, db, word):
        word_na = remove_accents(word)
        if word is None:
            raise Exception("Cannot load Ortho from word if word is not set. (word: %s)" % (word))
        db.cursor.execute("""SELECT ortho_id, ortho, ortho_na, lemma_id, freq, number, genre, nb_syll, nb_letters, vector
                            FROM public.orthos 
                            WHERE ortho_na = %s""",
                            (word_na,))
        self.load_from_db_res(db)

    def load_like_word(self, db, word):
        word_na = remove_accents(word)
        if word is None:
            raise Exception("Cannot load Ortho like word if word is not set. (word: %s)" % (word))
        db.cursor.execute("""SELECT ortho_id, ortho, ortho_na, lemma_id, freq, number, genre, nb_syll, nb_letters, vector
                            FROM public.orthos 
                            WHERE ortho_na LIKE = %s
                            ORDER BY freq  DESC LIMIT 1""",
                            ("%" + word_na + "%",))
        self.load_from_db_res(db)

    def similar(w1, w2):
        return (w1.lemma == w2.lemma)

    def sim_same_lemma(w1, w2):
        return 0.9 * max(0, naive_score_embeddings(w1.vector, w2.vector) - Ortho.SIMILIRARITY_MIN) / (1.0 - Ortho.SIMILIRARITY_MIN)

    def rectified_low_score(x):
        if x < 0:
            return Ortho.SCORE_ZERO * (1 + x)
        return Ortho.SCORE_MIN_NEIGHBOR * (x/Ortho.SCORE_MIN_NEIGHBOR)**(1.5)
        
    def __eq__(self, other):
        if not isinstance(other, Ortho):
            raise Exception("Ortho are only comparable to Ortho, not to {0}".format(type(other)))
        else:
            return self.id.__eq__(self.id)

    def __gt__(self, other):
        if not isinstance(other, Ortho):
            raise Exception("Ortho are only comparable to Ortho, not to {0}".format(type(other)))
        else:
            return self.ref_score.__gt__(other.ref_score)

    def __lt__(self, other):
        if not isinstance(other, Ortho):
            raise Exception("Ortho are only comparable to Ortho, not to {0}".format(type(other)))
        else:
            return self.ref_score.__lt__(other.ref_score)

    def __str__(self):
        if self.id is None:
            return str(self.ortho)
        return  "%s - %s (%d): %s" % (self.ortho, str(self.lemma).upper(), self.id, str(self.ref_score))

    def __repr__(self):
        return str(self)

    def compute_naive_score(self, other_word):
        score = naive_score_embeddings(self.vector, other_word.vector)
        return score

    def get_corrected(self, db):
        word_corrected = correct(self.ortho)
        if word_corrected == self.ortho:
            return None
        correction = Ortho()
        try:
            correction.load_from_word(db, word_corrected)
            return correction
        except:
            return None

    def compute_rectified_score(self, baseline):
        if self.id == baseline.id: # Found the right word
            return 1
        if Ortho.similar(self, baseline): # The right word is in the same family
            return Ortho.SCORE_MAX_NEIGHBOR + (1.0 - Ortho.SCORE_MAX_NEIGHBOR) * Ortho.sim_same_lemma(self, baseline)
        
        N_neighbors = len(baseline.neighbors)
        min_neighbor = baseline.neighbors[-1].ref_score
        max_neighbor = baseline.neighbors[0].ref_score
        for neighbor in baseline.neighbors:
            if Ortho.similar(self, neighbor):
                x = neighbor.ref_score - (Ortho.SCORE_MAX_NEIGHBOR - Ortho.SCORE_MIN_NEIGHBOR) / float(N_neighbors - 1.0)  * (1 - Ortho.sim_same_lemma(self, neighbor))
                return Ortho.SCORE_MIN_NEIGHBOR + (Ortho.SCORE_MAX_NEIGHBOR - Ortho.SCORE_MIN_NEIGHBOR) * (x - min_neighbor) / float(max_neighbor - min_neighbor)
        

        score = naive_score_embeddings(self.vector, baseline.vector)
        score = max(score, naive_score_embeddings(self.lemma.vector, baseline.lemma.vector))
        if score > min_neighbor:
            return Ortho.SCORE_MIN_NEIGHBOR + (Ortho.SCORE_MAX_NEIGHBOR - Ortho.SCORE_MIN_NEIGHBOR) * (score - min_neighbor) / float(max_neighbor - min_neighbor)
        
        return Ortho.rectified_low_score(score)


    def add_neighbor_if_not_too_similar(self, neighbor):
        score = neighbor.ref_score

        # Remove non words
        # word = word.lower()
        if not(isword(neighbor.word)):
            return

        # Update existing neighbors
        for i in range(len(self.neighbors)):
            if Ortho.similar(neighbor, self.neighbors[i]):
                if score > self.neighbors[i].ref_score:
                    self.neighbors[i] = neighbor
                return

        # Add new neighbor
        bisect.insort(self.neighbors, neighbor)


    def get_neighbors(self, db, number = 100, clean = True):
        LIMIT = 10000

        last_id = -1
        neighbors = [self]
        N_neighbors = 0
        res = [None]

        print(self.word, "get_neighbors ", end = "")
        while len(res) > 0:
            print(".", end="")
            db.cursor.execute("""SELECT ortho_id 
                                FROM public.orthos 
                                WHERE word_id > %s 
                                ORDER BY word_id ASC LIMIT %s""",
                                (last_id, LIMIT))
            res = db.cursor.fetchall()
        
            for row in res:
                last_id = row[0]
                word = Ortho()
                word.load_from_id(last_id)
                score = naive_score_embeddings(self.vector, word.vector)
                word.ref_score = score

                idx = bisect.bisect_left(neighbors, word)
                if idx > 0 and neighbors[idx - 1].id != word.id:
                    neighbors.insert(idx, word)
                    N_neighbors += 1
                if N_neighbors > number:
                    neighbors.pop(0)
                    N_neighbors -= 1
        print("")
        neighbors.pop()
        if clean:
            for neighbor in tqdm.tqdm(neighbors):
                self.add_neighbor_if_not_too_similar(neighbor)
        else:
            self.neighbors = neighbors
        return self.neighbors


    def get_hints(self, db):
        LIMIT = 10000
        NB_HINTS_MAX = 5
        RES_HINT = 0.05
        TOLERANCE_HINT = 0.005

        last_id = -1
        hints = {}
        res = [None]

        print(self.word, "get_hints ", end = "")
        while len(res) > 0:
            print(".", end="")
            db.cursor.execute("""SELECT ortho_id 
                                FROM public.orthos 
                                WHERE word_id > %s 
                                ORDER BY word_id ASC LIMIT %s""", 
                                (last_id, LIMIT))
            res = db.cursor.fetchall()
        
            for row in res:
                last_id = row[0]
                word = Ortho()
                word.load_from_id(last_id)
                score = naive_score_embeddings(self.vector, word.vector)
                word.ref_score = score

                if math.fmod(score, RES_HINT) < TOLERANCE_HINT:
                    value = int(score / RES_HINT)
                    if not RES_HINT * value in hints:
                        hints[RES_HINT * value] = [word]
                    elif len(hints[RES_HINT * value]) < NB_HINTS_MAX:
                        hints[RES_HINT * value].append(word)
        print("")
        return collections.OrderedDict(sorted(hints.items()))
