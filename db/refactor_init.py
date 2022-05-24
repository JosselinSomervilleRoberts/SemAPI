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

lemmas_temp = Ortho.load_all(db)
lemmas = []
for lemma in lemmas_temp:
    if "NP" not in lemma.lemma.type and len(lemma.ortho) > 3:
        lemma.ref_score = lemma.freq
        bisect.insort(lemmas, lemma)
lemmas = lemmas[::-1][:50000]
NB_LEMMAS = 100

for lemma in tqdm(lemmas):
    closest_lemmas = []
    min_comparator = 0
    length = 0

    for lemma2 in lemmas:
        if True:#lemma.id != lemma2.id:
            lemma2.ref_score = 1 - distance.cosine(lemma.vector, lemma2.vector)
            if lemma2.ref_score > min_comparator:
                bisect.insort(closest_lemmas, lemma2)
                length += 1
                if length > NB_LEMMAS:
                    closest_lemmas = closest_lemmas[1:]
                min_comparator = closest_lemmas[0].ref_score
    
    print(lemma)
    closest_lemmas.reverse()
    for lemma in closest_lemmas:
        print(lemma, lemma.ref_score)
    print("\n\n\n")
    
    for index, lemma2 in enumerate(closest_lemmas):
        try:
            db.cursor.execute("""INSERT INTO public.closest_lemmas (lemma_id1, lemma_id2, rank, score) 
                                VALUES(%s, %s, %s, %s)""", 
                                (lemma.id, lemma2.id, NB_LEMMAS - index, lemma2.comparator))         
            db.connexion.commit()
        except Exception as e:
            raise Exception("Could not insert neighbor.", lemma2, e)
