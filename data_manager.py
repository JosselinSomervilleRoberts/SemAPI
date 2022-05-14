from ortho import Ortho
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

    def get_session_id(self, db, utc):
        print("utc", utc)
        db.cursor.execute("SELECT session_id FROM public.sessions WHERE utc_start <= %d AND utc_stop >= %d ORDER BY session_id ASC" % (utc, utc))
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("No session was found for utc: %d" % (utc))
        return res[0]

    def load_session(self, db, session_id):
        baseline = Ortho()

        # Find the session
        db.cursor.execute("SELECT ortho_id FROM public.sessions WHERE session_id = %d" % session_id)
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("Cannot load session with id: %d, because the sessions was not found." % session_id)
        baseline_id = int(res[0])

        # Find the word
        baseline.load_from_id(db, baseline_id)

        # Find the neighbors
        db.cursor.execute("SELECT ortho_id, score FROM public.closest_words WHERE session_id = %d ORDER BY score ASC" % (session_id))
        res = db.cursor.fetchall()
        if res is None:
            raise Exception("Cannot load session with id: %d, because no neighbor where found." % (session_id))
        baseline.neighbors = {}
        for index, row in enumerate(res):
            neighbor = Ortho()
            neighbor.load_from_id(db, int(row[0]))
            neighbor.ref_score = float(row[1])
            neighbor.index = index
            baseline.neighbors[neighbor.lemma.lemma] = neighbor
        if len(baseline.neighbors) < 2:
            raise Exception("Not even 2 neighbors were found while loading session with id: %d." % session_id)
        baseline.neighbor_min_error = float(res[0][1])
        baseline.neighbor_max_error = float(res[-1][1])

        # Find the hints
        db.cursor.execute("SELECT ortho_id, rectified_score FROM public.hints WHERE session_id = %d ORDER BY rectified_score ASC" % (session_id))
        res = db.cursor.fetchall()
        if res is None:
            raise Exception("Cannot load session with id: %d, because no neighbor where found." % (session_id))
        hints = {}
        for row in res:
            word = Ortho()
            word.load_from_id(db, int(row[0]))
            score = float(row[1])
            if not score in hints:
                hints[score] = [word]
            else:
                hints[score].append(word)
        if len(hints.keys()) < 5:
            raise Exception("Not even 5 hints were found while loading session with id: %d." % session_id)

        self.sessions[session_id] = {'word': baseline, 'hints': hints}
        return self.sessions[session_id]