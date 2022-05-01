# -*- coding: utf-8 -*-
import tqdm
from datetime import datetime
from connexion import DbConnexion
from word import Word

db = DbConnexion()
db.connect()

start_utc = 3600 * 24 * int(datetime.now().timestamp() / (3600 * 24))
file_name = 'first_words.txt'
with open(file_name, "r", encoding="utf8") as f:
    
    index = 0
    for line in tqdm.tqdm(f.readlines()):
        if True:
            word = line.replace('\n', '').replace(' ', '')
            word_object = Word(word = word, lang = 'fr')
            word_object.load_from_word(db)

            neighbors = word_object.get_neighbors(db, 100)
            hints = word_object.get_hints(db)

            sql = "INSERT INTO public.sessions (word_id, utc_start, utc_stop) VALUES(%d, %d, %d)" % (word_object.id, start_utc, start_utc + 3600 * 24 - 1)
            try:
                db.cursor.execute(sql)         
                db.connexion.commit()
            except Exception as e:
                raise Exception("Could not insert new session.", e)  

            db.cursor.execute("SELECT session_id FROM public.sessions WHERE lang = \'fr\' AND word_id = %d" % (word_object.id))
            session_id = None
            res = db.cursor.fetchone()
            if res is None:
                raise Exception("Session id not found.")
            session_id = int(res[0])

            for neighbor in neighbors:
                sql = "INSERT INTO public.closest_words (session_id, word_id, score) VALUES(%d, %d, %f)" % (session_id, neighbor.id, neighbor.ref_score)
                try:
                    db.cursor.execute(sql)         
                    db.connexion.commit()
                except Exception as e:
                    raise Exception("Could not insert neighbor.", neighbor, e)

            for hint_value in hints.keys():
                for hint in hints[hint_value]:
                    sql = "INSERT INTO public.hints (session_id, word_id, rectified_score) VALUES(%d, %d, %f)" % (session_id, hint.id, hint_value)
                    try:
                        db.cursor.execute(sql)         
                        db.connexion.commit()
                    except Exception as e:
                        raise Exception("Could not insert hint.", hint_value, hint, e)   
                
        index += 1
        start_utc += 3600 * 24
            
db.disconnect()