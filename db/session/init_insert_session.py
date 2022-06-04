import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_PATH, '../../'))

from utils.time_utils import start_current_utc_s
from db.connexion import DbConnexion
from dotenv import load_dotenv
from game.session import Session
from game.lemma import Lemma


if __name__ == "__main__":
    load_dotenv()
    db = DbConnexion()
    db.connect()
    lemmas = Lemma.load_all(db)

    # Get UTC of tomorrow
    start_utc = start_current_utc_s()
    yesterday_start_utc = start_utc - 3600 * 24

    # Save two session
    session = Session.GetRandomSession(db, lemmas)
    session.SaveToDb(yesterday_start_utc)
    session2 = Session.GetRandomSession(db, lemmas)
    session2.SaveToDb(start_utc)