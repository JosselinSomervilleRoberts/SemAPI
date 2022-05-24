import sys
import os
from tqdm import tqdm
sys.path.append(os.path.abspath('../'))
from connexion import DbConnexion
from dotenv import load_dotenv
from lemma import Lemma
from ortho import Ortho
from scipy.spatial import distance
import bisect

load_dotenv()
db = DbConnexion()
db.connect()

lemmas = Lemma.load_all(db)

continuer = True
while continuer:
    word = input("Mot? ")
    if word == "STOP":
        continuer = False
    else:
        lemma = None
        try:
            ortho = Ortho()
            ortho.load_from_word(db, word)
            lemma = ortho.lemma
            print("Lemma =", lemma)
        except:
            print("Mot non trouvé.")

        if lemma is not None:
            sorted_lemmas = []
            for lemma2 in tqdm(lemmas):
                lemma2.comparator = 1 - distance.cosine(lemma.vector, lemma2.vector)
                bisect.insort(sorted_lemmas, lemma2)
            sorted_lemmas.reverse()

            for i in range(50):
                print(sorted_lemmas[i].comparator, "-", sorted_lemmas[i])
