import sys
import os
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

print("Chargement des lemmes...")
lemmas = Lemma.load_all()

def show_score(word: str, session: Session, prefix: str = "") -> None:
    ortho = Ortho().load_from_word(db, word)
    score = session.GetScoreFromLemma(ortho.lemma)
    print(prefix + ortho.word + " -> " + ortho.lemma.lemma + ": " + score)

 
continuer = True
while continuer:
    word = input("Mot du jour?")
    ortho = Ortho().load_from_word(db, word)
    session = Session(db)
    session.word = ortho

    continuer_rectifications = True
    while continuer_rectifications:
        print("Computing all scores...")
        sorted_lemmas = session.ComputeAllScores(lemmas)
        for i in range(1 + 50):
            print(sorted_lemmas[i].lemma + ": " + sorted_lemmas[i].comparator)
        continuer_test = True
        while continuer_test:
            str_test = str(input("Tester un mot? (STOP pour arreter)"))
            if str_test == "STOP":
                continuer_test = False
            else:
                show_score(str_test, session, "Test: ")
                
            str_rectification = str(input("Mot a rectifier? (STOP pour arreter)"))
            if str_rectification == "STOP":
                continuer_rectifications = False
            else:
                show_score(str_rectification, session, "Score actuel: ")
                score_rectification = float(input("Nouveau score?"))
                session.AddRectification(Ortho().load_from_word(db, word).lemma, score_rectification)

    str_continuer = str(input("Ajouter un autre mot? (Y:N)")).lower()
    continuer = (len(str_continuer) > 0) and (str_continuer[0] == "y")