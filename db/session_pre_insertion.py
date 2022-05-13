import sys
import os
from tqdm import tqdm
sys.path.append(os.path.abspath('../'))
from datetime import datetime
from connexion import DbConnexion
from ortho import Ortho
from dotenv import load_dotenv
from typing import List

def preprocess_neighbors(db: DbConnexion, words: List[Ortho], word: str, n: int):
    word_object = Ortho()
    word_object.load_from_word(db, word)
    neighbors = word_object.get_neighbors(words, n)
    with open('neighbors_' + word + '.txt', 'w', encoding='utf-8') as file:
        for neighbor in neighbors:
            data = [str(neighbor.ortho), str(neighbor.id), str(neighbor.lemma.id), str(neighbor.compute_rectified_score(word_object))]
            file.write(",".join(data) + "\n")
        file.close()

def load(db: DbConnexion, file_name: str):
    with open(file_name, "r", encoding="utf8") as f:
        words = Ortho.load_all(db)
        for line in tqdm(f.readlines()):
            word = line.replace('\n', '')
            preprocess_neighbors(db, words, word, 1000)



if __name__ == "__main__":
    load_dotenv()
    db = DbConnexion()
    db.connect()
    load(db, '../first_words.txt')
    db.disconnect()