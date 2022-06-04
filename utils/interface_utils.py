import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_PATH, '../'))

from game.session import Session
from game.ortho import Ortho
from db.connexion import DbConnexion
from typing import List, Dict, Callable


# Prints the score an ortho given a session
def ShowScoreOfOrtho(db: DbConnexion, ortho: Ortho, session: Session, prefix: str = "") -> None:
    score = session.GetScoreFromLemma(ortho.lemma)
    print("\t-", prefix + ortho.ortho, "->", ortho.lemma.lemma, ":", score)
    return score.value >= 0

# Prints the score a string given a session
def ShowScoreOfStr(db: DbConnexion, word: str, session: Session, prefix: str = "") -> None:
    ortho = Ortho()
    ortho.load_from_word(db, word)
    return ShowScoreOfOrtho(db, ortho, session, prefix)
    
# Asks for a wor duntil a valid ortho is ofund or the word
# is a special keyword.
def AskForOrthoUntilValid(db: DbConnexion,
                        question: str = "Mot",
                        keywords: List[str] = []):
    # Construct question
    str_question = question + " ?"
    if len(keywords) > 0:
        str_question += " (KEYWORDS: " + ", ".join(keywords) + ")"
    
    # Ask for the word
    word_is_valid = False
    while not word_is_valid:
        try:
            ortho_str = str(input(str_question))
            if ortho_str.lower() in keywords:
                return ortho_str.lower()
            try:
                ortho = Ortho()
                ortho.load_from_word(db, ortho_str)
                return ortho
            except Exception as error:
                print("Error loading ortho:", error) 
        except Exception as error:
            print("Error:", error)

# Repeats a callback until the user wants to stop
def RepeatUntilUserWantToStop(callback: Callable,
                                question_continue: str,
                                args: Dict = None):
    def callback_with_args():
        if args is None:
            return callback()
        else:
            return callback(args)

    continuer = True
    while continuer:
        can_continue = callback_with_args()
        if can_continue is None: can_continue = True
        if can_continue:
            try:
                valid_answer = False
                while not valid_answer:
                    answer = str(input(question_continue + " ? (Y/N)")).lower()[0]
                    if answer == "y":
                        valid_answer = True
                    elif answer == "n":
                        valid_answer = True
                        continuer = False
                    else:
                        print("Answer not recognized. Try again.")
            except Exception as error:
                print("Error:", error)
        else:
            continuer = False

# Repeats a callback until the callback returns False
def RepeatUntilCallbackReturnsFalse(callback: Callable):
    continuer = True
    while continuer:
        continuer = callback()