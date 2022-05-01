# -*- coding: utf-8 -*-
import tqdm
from word_utils import correct, lemmatize, remove_accents, isword
from word import Word
from connexion import DbConnexion

db = DbConnexion()
db.connect()

file_name = 'wiki.fr.vec'
list_batch = []
with open(file_name, "r", encoding="utf8") as f:
    
    index = 0
    for line in tqdm.tqdm(f.readlines()):
        if index > 0:
            idx = line.find(' ')
            word = line[:idx]
            word_na = remove_accents(word)
            if isword(word_na):
                vec = '[' + line[idx+1:].replace(' \n', '').replace(" ", ", ") + ']'
                #w_correct = correct(word)
                #w_correct_na = correct(word_na)
                w = Word(word = word, word_na = word_na, vector = vec, lang = 'fr')
                w.lemmatize()
                try:
                    w.insert_into_db(db, True)
                except:
                    db.connexion.commit()
                    print("Could not insert", w)

        index += 1
            
db.disconnect()

    