from word_utils import lemmatize, isword, correct, remove_accents
from lemma import Lemma
import numpy as np
import bisect
import math
import collections
from tqdm import tqdm
from scipy.spatial import distance


def distance_embeddings(emb1, emb2):
    return distance.cosine(emb1, emb2)

def naive_score_embeddings(emb1, emb2):
    return max(0, 1 - abs(distance_embeddings(emb1, emb2)))

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
        self.neighbor_min_error = None
        self.neighbor_max_error = None
        self.ref_score = 0
        self.index = None

    def load_from_json(self, data):
        self.id = data['id']
        self.ortho = data['ortho']
        self.ortho_na = data['ortho_na']
        self.freq = data['freq']
        self.number = data['number']
        self.genre = data['genre']
        self.nb_syll = data['nb_syll']
        if not self.nb_syll is None:
            self.nb_syll = int(self.nb_syll)
        self.nb_letters = data['nb_letters']
        self.vector = data['vector']
        self.lemma = Lemma()
        self.lemma.load_from_json(data['lemma'])

    def load_from_db_res(self, db):
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("Could not load Ortho")
        self.id = res[0]
        self.ortho = res[1]
        self.ortho_na = res[2]
        self.freq = float(res[3])
        self.number = res[4]
        self.genre = res[5]
        self.nb_syll = res[6]
        if not self.nb_syll is None:
            self.nb_syll = int(self.nb_syll)
        self.nb_letters = int(res[7])
        self.vector = np.array(res[8])
        self.lemma = Lemma()
        if len(res) > 9:      
            self.lemma.load_from_id(db, res[9])

    def load_from_id(self, db, id):
        if id is None:
            raise Exception("Cannot load Ortho from id if the id is not set. (id: %d)" % (id))
        db.cursor.execute("""SELECT ortho_id, ortho, ortho_na, freq, number, genre, nb_syll, nb_letters, vector, lemma_id
                            FROM public.orthos 
                            WHERE ortho_id = %s""",
                            (id,))
        self.load_from_db_res(db)
        
    def load_from_word(self, db, word):
        word_na = remove_accents(word)
        if word is None:
            raise Exception("Cannot load Ortho from word if word is not set. (word: %s)" % (word))
        db.cursor.execute("""SELECT ortho_id, ortho, ortho_na, freq, number, genre, nb_syll, nb_letters, vector, lemma_id
                            FROM public.orthos 
                            WHERE ortho_na = %s""",
                            (word_na,))
        self.load_from_db_res(db)

    def load_like_word(self, db, word):
        word_na = remove_accents(word)
        if word is None:
            raise Exception("Cannot load Ortho like word if word is not set. (word: %s)" % (word))
        db.cursor.execute("""SELECT ortho_id, ortho, ortho_na, freq, number, genre, nb_syll, nb_letters, vector, lemma_id
                            FROM public.orthos 
                            WHERE ortho_na LIKE = %s
                            ORDER BY freq  DESC LIMIT 1""",
                            ("%" + word_na + "%",))
        self.load_from_db_res(db)

    def load_all(db):
        LIMIT = 5000
        last_id = -1
        words = []
        res = [None]
        print("Loading all orthos ", end = "")

        while len(res) > 0:
            print(".", end="")
            db.cursor.execute("""SELECT ortho_id, ortho, ortho_na, o.freq, number, genre, nb_syll, nb_letters, o.vector, 
                                l.lemma_id, lemma, lemma_na, type, l.freq, l.vector
                                FROM public.orthos AS o
                                JOIN lemmas AS l ON l.lemma_id = o.lemma_id
                                WHERE ortho_id > %s 
                                ORDER BY ortho_id ASC LIMIT %s""",
                                (last_id, LIMIT))
            res = db.cursor.fetchall()
        
            for row in res:
                last_id = int(row[0])
                data = {"id": int(row[0]), "ortho": row[1], "ortho_na": row[2], "freq": float(row[3]), "number": row[4],
                "genre": row[5], "nb_syll": row[6], "nb_letters": int(row[7]), "vector": np.array(row[8]),
                "lemma": {"id": int(row[9]), "lemma": row[10], "lemma_na": row[11], "type": row[12], "freq": float(row[13]), "vector": np.array(row[14])}}
                word = Ortho()
                word.load_from_json(data)
                words.append(word)
        print("")
        return words


    def similar(w1, w2):
        return (not w1.lemma is None) and (w1.lemma == w2.lemma)

    def sim_same_lemma(w1, w2):
        return 0.9 * max(0, naive_score_embeddings(w1.vector, w2.vector) - Ortho.SIMILIRARITY_MIN) / (1.0 - Ortho.SIMILIRARITY_MIN)

    def rectified_low_score(x):
        if x < 0:
            return Ortho.SCORE_ZERO * (1 + x)
        return Ortho.SCORE_MIN_NEIGHBOR * (x/Ortho.SCORE_MIN_NEIGHBOR)**(1.6)

    def mix_linear_proportional(linear, proportional):
        return 0.7 * linear + 0.3 * proportional
        
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
        min_neighbor = baseline.neighbor_min_error
        max_neighbor = baseline.neighbor_max_error
        print(min_neighbor, max_neighbor)
        if self.lemma.lemma in baseline.neighbors:
            neighbor = baseline.neighbors[self.lemma.lemma]
            index = neighbor.index
            dx = (Ortho.SCORE_MAX_NEIGHBOR - Ortho.SCORE_MIN_NEIGHBOR) / float(N_neighbors - 1.0) * (1 - Ortho.sim_same_lemma(self, neighbor))
            rectified_linear = Ortho.SCORE_MIN_NEIGHBOR + (Ortho.SCORE_MAX_NEIGHBOR - Ortho.SCORE_MIN_NEIGHBOR) * index / float(N_neighbors - 1.0)
            rectified_linear -= dx
            x = neighbor.ref_score - dx
            rectified_proportional = Ortho.SCORE_MIN_NEIGHBOR + (Ortho.SCORE_MAX_NEIGHBOR - Ortho.SCORE_MIN_NEIGHBOR) * (x - min_neighbor) / float(max_neighbor - min_neighbor)
            return Ortho.mix_linear_proportional(rectified_linear, rectified_proportional)
        

        score = naive_score_embeddings(self.vector, baseline.vector)
        score = max(score, naive_score_embeddings(self.lemma.vector, baseline.lemma.vector))
        if score > min_neighbor:
            rectified_proportional = Ortho.SCORE_MIN_NEIGHBOR + (Ortho.SCORE_MAX_NEIGHBOR - Ortho.SCORE_MIN_NEIGHBOR) * (score - min_neighbor) / float(max_neighbor - min_neighbor)
            return rectified_proportional
            #for index, neighbor in enumerate(baseline.neighbors):
            #    if score < neighbor.ref_score:
            #        rectified_linear = Ortho.SCORE_MIN_NEIGHBOR + (Ortho.SCORE_MAX_NEIGHBOR - Ortho.SCORE_MIN_NEIGHBOR) * (index - 1) / float(N_neighbors - 1.0)
            #        return Ortho.mix_linear_proportional(rectified_linear, rectified_proportional)
            
        return Ortho.rectified_low_score(score)


    def add_neighbor_if_not_too_similar(self, neighbor):
        # Remove non words
        if not(isword(neighbor.ortho)):
            return

        # Update existing neighbors
        for i in range(len(self.neighbors)):
            if Ortho.similar(neighbor, self.neighbors[i]):
                if neighbor.ref_score > self.neighbors[i].ref_score:
                    self.neighbors[i] = neighbor
                return

        # Add new neighbor
        bisect.insort(self.neighbors, neighbor)


    def get_neighbors(self, words, number = 1000):
        neighbors = [self]
        N_neighbors = 0
        
        for word in tqdm(words):
            score = naive_score_embeddings(self.vector, word.vector)
            word.ref_score = score

            idx = bisect.bisect_left(neighbors, word)
            if (not "NP" in word.lemma.type) and not(Ortho.similar(self, word)) and idx > 0 and neighbors[idx - 1].id != word.id:
                neighbors.insert(idx, word)
                N_neighbors += 1
            if N_neighbors > number:
                neighbors.pop(0)
                N_neighbors -= 1

        neighbors.pop()
        self.neighbors = []
        for neighbor in tqdm(neighbors):
            self.add_neighbor_if_not_too_similar(neighbor)
        dict_neighbor = {}
        for index, neighbor in enumerate(self.neighbors):
            dict_neighbor[neighbor.lemma.lemma] = neighbor
            dict_neighbor[neighbor.lemma.lemma].index = index
        self.neighbor_min_error = self.neighbors[0].ref_score
        self.neighbor_max_error = self.neighbors[-1].ref_score
        self.neighbors = dict_neighbor
        return self.neighbors


    def get_hints(self, words):
        NB_HINTS_MAX = 5
        RES_HINT = 0.05
        TOLERANCE_HINT = 0.005
        hints = {}
        
        for word in tqdm(words):
            score = word.compute_rectified_score(self)

            if (not "NP" in word.lemma.type) and math.fmod(score, RES_HINT) < TOLERANCE_HINT:
                value = int(score / RES_HINT)
                if not RES_HINT * value in hints:
                    hints[RES_HINT * value] = [word]
                elif len(hints[RES_HINT * value]) < NB_HINTS_MAX:
                    hints[RES_HINT * value].append(word)

        return collections.OrderedDict(sorted(hints.items()))
