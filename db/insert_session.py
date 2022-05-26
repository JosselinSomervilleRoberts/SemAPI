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
from datetime import datetime


def start_current_time_s():
    start_utc = 3600 * 24 * int(datetime.now().timestamp() / (3600 * 24))
    return start_utc

def current_time_s():
    return int(datetime.now().timestamp()) + 3600 * 2

load_dotenv()
db = DbConnexion()
db.connect()

lemmas = Lemma.load_all(db)

def show_score(word: str, session: Session, prefix: str = "") -> None:
    ortho = Ortho()
    ortho.load_from_word(db, word)
    score = session.GetScoreFromLemma(ortho.lemma)
    print("\t-", prefix + ortho.ortho, "->", ortho.lemma.lemma, ":", score)
    return score.value >= 0

 
continuer = True
while continuer:
    start_utc = start_current_time_s() - 3600 * 24
    word = None
    ortho = None
    continue_ask = True
    while continue_ask:
        continue_ask = False
        word = input("Mot du jour? ")
        ortho = Ortho()
        try:
            ortho.load_from_word(db, word)
        except Exception as e:
            print(e)
            continue_ask = True

    session = Session(db)
    session.CreateSession(ortho, lemmas)
    save = False

    continuer_rectifications = True
    while continuer_rectifications:
        best_lemmas = session.GetBestLemmas(1 + 20)
        for i in range(len(best_lemmas)):
            print("\t-", best_lemmas[i].lemma, ":", session.GetScoreFromLemma(best_lemmas[i]))
        continuer_test = True
        while continuer_test:
            need_rectify = False
            str_test = str(input("Tester un mot? (RECTIF - SAVE - ABORT - FORGET) ")).lower()
            if str_test == "save":
                continuer_test = False
                continuer_rectifications = False
                save = True
            elif str_test == "abort":
                continuer_test = False
                continuer_rectifications = False
                save = False
            elif str_test == "rectif":
                need_rectify = True
            elif str_test == "forget":
                continuer_test = False
            else:
                try:
                    show_score(str_test, session, "Test: ")
                except Exception as e:
                    print(e)
                
            if need_rectify:
                try_again = True
                while try_again:
                    try_again = False
                    str_rectification = str(input("Mot a rectifier? (REMOVE - SAVE - ABORT - FORGET) ")).lower()
                    if str_rectification == "save":
                        continuer_test = False
                        continuer_rectifications = False
                        save = True
                    elif str_test == "abort":
                        continuer_test = False
                        continuer_rectifications = False
                        save = False
                    elif str_rectification == "remove":
                        session.RemoveLastRectification()
                    elif str_rectification == "forget":
                        pass # Do nothing
                    else:
                        found = show_score(str_rectification, session, "Score actuel: ")
                        if not found:
                            print("Le mot " + str_rectification + " n'existe pas. Essayez a nouveau:")
                            try_again = True
                        else:
                            score_rectification = float(input("Nouveau score? "))
                            similarity_min = float(input("Similarité minimum? "))
                            ortho_to_rectify = Ortho()
                            ortho_to_rectify.load_from_word(db, str_rectification)
                            session.AddRectification(ortho_to_rectify.lemma, score_rectification, similarity_min)
                            continuer_test = False


    if save:
        print("===== Saving", ortho, "=====")
        session.SaveRectifications()

        # Update UTC
        utc_used = True
        while utc_used:
            utc_used = False
            db.cursor.execute("SELECT * FROM public.fr_sessions WHERE utc_start = %s", (start_utc,))
            if db.cursor.fetchone() is not None:
                utc_used = True
                start_utc += 3600 * 24
                print("INCREASE UTC")
        db.cursor.execute("UPDATE public.fr_sessions SET utc_start = %s, utc_stop = %s WHERE session_id = %s",
                            (start_utc, start_utc + 3600 * 24, session.id))
        db.connexion.commit()
        print("===== DONE =====")
    else:
        print("===== Deleting", ortho, "=====")
        session.RemoveFromDb()
        print("===== DONE =====")

    str_continuer = str(input("\n\n\nAjouter un autre mot? (Y/N) ")).lower()
    continuer = (len(str_continuer) > 0) and (str_continuer[0] == "y")