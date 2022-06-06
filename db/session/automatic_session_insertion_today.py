import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_PATH, '../../'))

from utils.time_utils import start_current_utc_s
from db.connexion import DbConnexion
from dotenv import load_dotenv
from game.session import Session


if __name__ == "__main__":
    load_dotenv()
    db = DbConnexion()
    db.connect()

    # Get UTC of today
    start_utc = start_current_utc_s()
 
    # Check if a session already covers the next day
    utc_used = False
    db.cursor.execute("SELECT * FROM public.fr_sessions WHERE utc_start = %s", (start_utc,))
    if db.cursor.fetchone() is not None:
        utc_used = True
    
    # If the UTC is not used, had a session
    if not utc_used:
        session = Session.GetRandomSession(db)
        session.SaveToDb(start_utc)
    else:
        print("No need to add a random session.")