from word_utils import lemmatize, isword, correct, remove_accents
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

class Word:

    SCORE_MAX_NEIGHBOR = 0.98
    SCORE_MIN_NEIGHBOR = 0.5
    SIMILIRARITY_MIN = 0.5
    SCORE_ZERO = 0.1

    def db_get_vector(db, word, lang='fr'):
        db.cursor.execute("SELECT vector FROM public.words WHERE lang = \'%s\' AND word = \'%s\'" % (lang, word))
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("No vector associated to word: %s in lang: %s" % (word, lang))
        return np.array(res[0])

    def similar(w1, w2):
        if not w1.word is None and w1.lemma is None:
            w1.lemma = lemmatize(w1.word)
        if not w2.word is None and w2.lemma is None:
            w2.lemma = lemmatize(w2.word)
        return (w1.lemma == w2.lemma)

    def sim_same_lemma(w1, w2):
        return max(0, naive_score_embeddings(w1.vector, w2.vector) - Word.SIMILIRARITY_MIN) / (1.0 - Word.SIMILIRARITY_MIN)

    def rectified_low_score(x):
        if x < 0:
            return Word.SCORE_ZERO * (1 + x)
        return Word.SCORE_MIN_NEIGHBOR * (x/Word.SCORE_MIN_NEIGHBOR)**(1.5)

    def __init__(self, word = None, word_na = None, id = None, lang = 'fr', lemma = None, vector = None, neighbors = []):
        self.word = word
        self.word_na = word_na
        self.id = id
        self.lang = lang
        self.lemma = lemma
        self.vector = vector
        self.neighbors = neighbors
        self.ref_score = 0

    def __gt__(self, other):
        if not isinstance(other, Word):
            raise Exception("Word are only comparable to Word, not to {0}".format(type(other)))
        else:
            return self.ref_score.__gt__(other.ref_score)

    def __lt__(self, other):
        if not isinstance(other, Word):
            raise Exception("Word are only comparable to Word, not to {0}".format(type(other)))
        else:
            return self.ref_score.__lt__(other.ref_score)

    def __str__(self):
        if self.id is None:
            return str(self.word)
        return  "%s - %s (%d): %s" % (self.word, str(self.lemma).upper(), self.id, str(self.ref_score))

    def __repr__(self):
        return str(self)

    def load_from_id(self, db, id = None):
        if id is None:
            id = self.id
        if id is None:
            raise Exception("Cannot load Word from id if the id is not set. (id: %d)" % (id))
        db.cursor.execute("SELECT word, lemma, lang, vector, word_naFROM public.words WHEREAND word_id = %d" % (id))
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("Could not load word with id: %d" % (id))
        self.id = id
        self.word = res[0]
        self.lang = res[2]
        self.vector = np.array(res[3])
        self.lemma = res[1]
        self.word_na = res[4]
        if not self.word is None:
            if self.lemma is None:
                self.lemma = lemmatize(self.word)
            if self.word_na is None:
                self.word_na = remove_accents(self.word)

    def load_from_word(self, db, word = None, lang = None):
        if word is None:
            word = self.word
        if lang is None:
            lang = self.lang
        if word is None or lang is None:
            raise Exception("Cannot load Word from word if not both word and lang are set. (word: %s, lang: %s)" % (word, lang))
        db.cursor.execute("SELECT word_id, lemma, vector, word_na FROM public.words WHERE lang = \'%s\' AND word = \'%s\'" % (lang, word))
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("Could not load Word with word: %s in %s" % (word, lang))
        self.id = res[0]
        self.lang = lang
        self.word = word
        self.vector = np.array(res[2])
        self.lemma = res[1]
        if not self.word is None:
            if self.lemma is None:
                self.lemma = lemmatize(self.word)
            if self.word_na is None:
                self.word_na = remove_accents(self.word)

    def lemmatize(self):
        if not(self.word is None):
            self.lemma = lemmatize(self.word)

    def insert_into_db(self, db, commit = True):
        if self.word is None or self.word_na is None or self.lang is None or self.lemma is None or self.vector is None :
            raise Exception("Cannot insert Word without all of its arguments.")
        sql = "INSERT INTO public.words(word, word_na, lemma, lang, vector) VALUES(\'%s\', \'%s\', \'%s\', \'%s\', ARRAY%s)" % (self.word, self.word_na, self.lemma, self.lang, str(self.vector))
        db.cursor.execute(sql)
        if commit:
            db.connexion.commit()

    def compute_naive_score(self, other_word):
        score = naive_score_embeddings(self.vector, other_word.vector)
        return score

    def get_corrected(self, db):
        word_corrected = correct(self.word)
        if word_corrected == self.word:
            return None
        correction = Word()
        try:
            correction.load_from_word(db, word = word_corrected, lang = self.lang)
            if not correction.word is None:
                if correction.lemma is None:
                    correction.lemma = lemmatize(correction.word)
                if correction.word_na is None:
                    correction.word_na = remove_accents(correction.word)
            return correction
        except:
            return None

    def compute_rectified_score(self, baseline):
        if Word.similar(self, baseline):
            return Word.SCORE_MAX_NEIGHBOR + (1.0 - Word.SCORE_MAX_NEIGHBOR) * Word.sim_same_lemma(self, baseline)
        
        N_neighbors = len(baseline.neighbors)
        min_neighbor = baseline.neighbors[-1].ref_score
        max_neighbor = baseline.neighbors[0].ref_score
        for neighbor in baseline.neighbors:
            if Word.similar(self, neighbor):
                x = neighbor.ref_score - (Word.SCORE_MAX_NEIGHBOR - Word.SCORE_MIN_NEIGHBOR) / float(N_neighbors - 1.0)  * (1 - Word.sim_same_lemma(self, neighbor))
                return Word.SCORE_MIN_NEIGHBOR + (Word.SCORE_MAX_NEIGHBOR - Word.SCORE_MIN_NEIGHBOR) * (x - min_neighbor) / float(max_neighbor - min_neighbor)
        

        score = self.compute_naive_score(baseline)
        if score > min_neighbor:
            return Word.SCORE_MIN_NEIGHBOR + (Word.SCORE_MAX_NEIGHBOR - Word.SCORE_MIN_NEIGHBOR) * (score - min_neighbor) / float(max_neighbor - min_neighbor)
        
        return Word.rectified_low_score(score)


    def compute_rectified_score_corrected(self, db, baseline):
        score = self.compute_rectified_score(baseline)
        corrected = self.get_corrected(db)
        if corrected is None:
            return {'score': score}
        score_corrected = corrected.compute_rectified_score(baseline)
        if score_corrected > score:
            return {'score': score, 'suggested': corrected, 'score_suggested': score_corrected}
        else:
            return {'score': score}

    def add_neighbor_if_not_too_similar(self, db, neighbor, threshold = 0.75):
        score = neighbor.ref_score

        # Split composed word
        if "-" in neighbor.word:
            splitted = neighbor.word.split("-")
            if splitted[0] == "non":
                return
            for word_part in splitted:
                sub_word = Word(word = word_part)
                sub_word.load_from_word(db)
                sub_score = self.compute_naive_score(sub_word)
                if sub_score >= threshold * score:
                    self.add_neighbor_if_not_too_similar(db, sub_word, threshold)
                return

        # Remove non words
        # word = word.lower()
        if not(isword(neighbor.word)):
            return

        # Update existing neighbors
        corrected = neighbor.get_corrected(db)
        if corrected is None:
            corrected = neighbor
        for i in range(len(self.neighbors)):
            if Word.similar(corrected, self.neighbors[i]):
                if score > self.neighbors[i].ref_score:
                    self.neighbors[i].ref_score = score
                return

        # Add new neighbor
        score_lemmatized = 0
        try:
            score_lemmatized = naive_score_embeddings(self.vector, Word.db_get_vector(db, corrected.lemma))
        except Exception as e:
            print(e)
        new_score = max(score, score_lemmatized)
        neighbor.ref_score = new_score
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
            db.cursor.execute("SELECT word_id, word, lemma, vector FROM public.words WHERE word_id > %d ORDER BY word_id ASC LIMIT %s" % (last_id, LIMIT))
            res = db.cursor.fetchall()
        
            for row in res:
                last_id = row[0]
                word = Word(id = row[0], word = row[1], lemma = row[2], vector = np.array(row[3]))
                score = word.compute_naive_score(self)
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
                self.add_neighbor_if_not_too_similar(db, neighbor)
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
            db.cursor.execute("SELECT word_id, word, lemma, vector FROM public.words WHERE word_id > %d ORDER BY word_id ASC LIMIT %s" % (last_id, LIMIT))
            res = db.cursor.fetchall()
        
            for row in res:
                last_id = row[0]
                word = Word(id = row[0], word = row[1], lemma = row[2], vector = np.array(row[3]))
                score = word.compute_rectified_score(self)
                word.ref_score = score

                if math.fmod(score, RES_HINT) < TOLERANCE_HINT:
                    value = int(score / RES_HINT)
                    if not RES_HINT * value in hints:
                        hints[RES_HINT * value] = [word]
                    elif len(hints[RES_HINT * value]) < NB_HINTS_MAX:
                        hints[RES_HINT * value].append(word)
        print("")
        return collections.OrderedDict(sorted(hints.items()))
