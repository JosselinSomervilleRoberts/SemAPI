import sys
import os
from tqdm import tqdm
sys.path.append(os.path.abspath('../'))
from connexion import DbConnexion
from dotenv import load_dotenv
from ortho import Ortho
from scipy.spatial import distance
import bisect

load_dotenv()
db = DbConnexion()
db.connect()

orthos = Ortho.load_all(db)

continuer = True
while continuer:
    word = input("Mot? ")
    if word == "STOP":
        continuer = False
    else:
        ortho = None
        try:
            ortho = Ortho()
            ortho.load_from_word(db, word)
        except:
            print("Mot non trouvé.")

        if ortho is not None:
            sorted_orthos = []
            for ortho2 in tqdm(orthos):
                ortho2.ref_score = 1 - distance.cosine(ortho.vector, ortho2.vector)
                bisect.insort(sorted_orthos, ortho2)
            sorted_orthos.reverse()

            for i in range(20):
                print(sorted_orthos[i].ref_score, "-", sorted_orthos[i].ortho)
