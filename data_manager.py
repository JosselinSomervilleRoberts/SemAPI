from requests import session
from word import Word
import numpy as np

class DataManager:

    def __init__(self):
        self.sessions = {}

    def get_session_infos(self, db, session_id):
        if session_id in self.sessions:
            return self.sessions[session_id]
        return self.load_session(db, session_id)

    def load_sessions(self, db):
        self.sessions = {}
        db.cursor.execute("SELECT session_id FROM public.sessions ORDER BY session_id ASC")
        res = db.cursor.fetchall()
        if res is None:
            raise Exception("No sessions were found in db.")
        for row in res:
            session_id = int(row[0])
            self.load_session(db, session_id)

    def get_session_id(self, db, utc, lang='fr'):
        print("utc", utc)
        db.cursor.execute("SELECT session_id FROM public.sessions WHERE lang = \'%s\' AND utc_start <= %d AND utc_stop >= %d ORDER BY session_id ASC" % (lang, utc, utc))
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("No session was found for utc: %d, in lang: %s" % (utc, lang))
        return res[0]

    def load_session(self, db, session_id):
        baseline = Word()

        # Find the session
        db.cursor.execute("SELECT word_id, lang FROM public.sessions WHERE session_id = %d" % session_id)
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("Cannot load session with id: %d, because the sessions was not found." % session_id)
        baseline.id = int(res[0])
        lang = res[1]

        # Find the word
        db.cursor.execute("SELECT word, word_na, lemma, vector FROM public.words WHERE word_id = \'%s\'" % (baseline.id))
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("Cannot load session with id: %d, because the word was not found, word_id: %d." % (session_id, baseline.id))
        baseline.word = str(res[0])
        baseline.word_na = str(res[1])
        baseline.lemma = str(res[2])
        baseline.vector = np.array(res[3])

        # Find the neighbors
        db.cursor.execute("SELECT w.word_id, score, word, w.word_na, w.lemma, w.vector FROM public.closest_words AS pc JOIN public.words AS w ON w.word_id = pc.word_id WHERE session_id = %d ORDER BY score DESC" % (session_id))
        res = db.cursor.fetchall()
        if res is None:
            raise Exception("Cannot load session with id: %d, because no neighbor where found." % (session_id))
        baseline.neighbors = [] 
        for row in res:
            neighbor = Word(id = row[0], word = row[2], word_na = row[3], lemma = row[4], lang = lang, vector = np.array(row[5]))
            neighbor.ref_score = float(row[1])
            baseline.neighbors.append(neighbor)
        if len(baseline.neighbors) < 2:
            raise Exception("Not even 2 neighbors were found while loading session with id: %d." % session_id)

        # Find the hints
        db.cursor.execute("SELECT w.word_id, rectified_score, word, w.word_na, w.lemma, w.vector FROM public.hints AS h JOIN public.words AS w ON w.word_id = h.word_id WHERE session_id = %d ORDER BY rectified_score ASC" % (session_id))
        res = db.cursor.fetchall()
        if res is None:
            raise Exception("Cannot load session with id: %d, because no neighbor where found." % (session_id))
        hints = {}
        for row in res:
            score = float(row[1])
            word = Word(id = row[0], word = row[2], word_na = row[3], lemma = row[4], lang = lang, vector = np.array(row[5]))
            if not score in hints:
                hints[score] = [word]
            else:
                hints[score].append(word)
        if len(hints.keys()) < 5:
            raise Exception("Not even 5 hints were found while loading session with id: %d." % session_id)

        self.sessions[session_id] = {'word': baseline, 'hints': hints}
        return self.sessions[session_id]