import sys
import os
from torch import ScriptModuleSerializer
from tqdm import tqdm
sys.path.append(os.path.abspath('../'))
from connexion import DbConnexion
from dotenv import load_dotenv
from ortho import Ortho
from lemma import Lemma
from session import Session
from score import Score

load_dotenv()
db = DbConnexion()
db.connect()

session_id = int(input("session id? "))
session = Session(db)
session.LoadFromSessionId(session_id)

word = str(input("Mot? "))
ortho = Ortho()
ortho.load_from_word(db, word)

print(session.GetScoreFromLemma(ortho.lemma))