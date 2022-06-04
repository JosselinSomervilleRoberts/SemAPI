import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_PATH, '../'))

from db.connexion import DbConnexion
from game.session import Session


class DataManager:

    def __init__(self):
        self.sessions = {}

    def get_session(self, db: DbConnexion, session_id: int) -> Session:
        if session_id in self.sessions:
            return self.sessions[session_id]
        return self.load_session(db, session_id)

    def load_sessions(self, db):
        self.sessions = {}
        db.cursor.execute("SELECT session_id FROM public.fr_sessions ORDER BY session_id ASC")
        res = db.cursor.fetchall()
        if res is None:
            raise Exception("No sessions were found in db.", 500)
        for row in res:
            session_id = int(row[0])
            self.load_session(db, session_id)

    def get_session_id(self, db, utc):
        print("utc", utc)
        db.cursor.execute("SELECT session_id FROM public.fr_sessions WHERE utc_start <= %d AND utc_stop >= %d ORDER BY session_id ASC" % (utc, utc))
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("No session was found for utc: %d" % (utc), 500)
        return res[0]

    def load_session(self, db: DbConnexion, session_id: int) -> Session:
        session = Session(db)
        session.LoadFromSessionId(session_id)
        self.sessions[session_id] = session
        return self.sessions[session_id]