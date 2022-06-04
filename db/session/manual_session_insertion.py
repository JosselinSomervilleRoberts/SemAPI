import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_PATH, '../../'))

from db.connexion import DbConnexion
from dotenv import load_dotenv
from game.lemma import Lemma
from game.session import Session
from utils.interface_utils import RepeatUntilCallbackReturnsFalse, RepeatUntilUserWantToStop, ShowScoreOfOrtho, AskForOrthoUntilValid
from typing import Dict


# Ask the user for a word and lets the user perform
# actions to try the session and eventually save it.
def manually_add_session(args: Dict = None):
    # Get the args
    db = args['db']
    lemmas = args['lemmas']

    # Ask for the word to guess
    ortho = AskForOrthoUntilValid(db, "Mot du jour")
    session = Session(db)
    session.CreateSession(ortho, lemmas)

    # Callback to save the session
    def save_session():
        print("===== Saving", ortho, "=====")
        session.SaveToDb()
        print("===== DONE =====")
    
    # Callback to delete the partially saved session
    def abort_session():
        print("===== Deleting", ortho, "=====")
        session.RemoveFromDb()
        print("===== DONE =====")

    # Callback to add a rectification to the session
    def add_rectif():
        rectif = AskForOrthoUntilValid(db, "Mot a rectifier",
                                            ['nothing', 'remove'])
        if type(rectif) == str:
            if rectif == 'nothing': pass
            if rectif == 'remove': session.RemoveLastRectification()
        else:
            ShowScoreOfOrtho(add_rectif, session, "Score actuel: ")
            score_rectification = float(input("Nouveau score? "))
            similarity_min = float(input("Similarité minimum? "))
            session.AddRectification(rectif.lemma, score_rectification, similarity_min)

    # Callback to test a word or call other callbacks
    def ask_test():
        # Show best lemmas
        best_lemmas = session.GetBestLemmas(1 + 20)
        for i in range(len(best_lemmas)):
            print("\t-", best_lemmas[i].lemma, ":", session.GetScoreFromLemma(best_lemmas[i]))
            
        # Ask for an action
        test = AskForOrthoUntilValid(db, "Tester un mot",
                                    ["rectif", "save", "abort", "nothing"])
            
        # Process the action
        if type(test) == str:
            if test == "nothing": pass
            if test == "rectif": add_rectif()
            if test == "save":
                save_session()
                return False
            if test == "abort":
                abort_session()
                return False
        else:
            ShowScoreOfOrtho(test)

    # Repeat indefinitely the ask_test callback
    RepeatUntilCallbackReturnsFalse(ask_test)



if __name__ == "__main__":
    load_dotenv()
    db = DbConnexion()
    db.connect()
    lemmas = Lemma.load_all(db)

    # Add sessions until the user wants to stop
    RepeatUntilUserWantToStop(manually_add_session,
                                "Ajouter un autre mot",
                                {"db": db, "lemmas": lemmas})