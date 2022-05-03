import sys
import os
from tqdm import tqdm
sys.path.append(os.path.abspath('../'))
from datetime import datetime
from connexion import DbConnexion
from ortho import Ortho
import os
from dotenv import load_dotenv


def load():
    start_utc = 3600 * 24 * int(datetime.now().timestamp() / (3600 * 24))
    file_name = '../first_words.txt'
    with open(file_name, "r", encoding="utf8") as f:
        
        index = 0
        words = Ortho.load_all(db)
        for line in tqdm(f.readlines()):
            if True:
                word = line.replace('\n', '')
                print("INSERTING %s ..." % word)
                word_object = Ortho()
                word_object.load_from_word(db, word)

                neighbors = word_object.get_neighbors(words, 100)
                hints = word_object.get_hints(words)

                try:
                    db.cursor.execute("""INSERT INTO public.sessions (ortho_id, utc_start, utc_stop) 
                                        VALUES(%s, %s, %s)""", 
                                        (word_object.id, start_utc, start_utc + 3600 * 24 - 1))         
                    db.connexion.commit()
                except Exception as e:
                    raise Exception("Could not insert new session.", e)  

                db.cursor.execute("""SELECT session_id 
                                    FROM public.sessions 
                                    WHERE ortho_id = %s""", 
                                    (word_object.id, ))
                session_id = None
                res = db.cursor.fetchone()
                if res is None:
                    raise Exception("Session id not found.")
                session_id = int(res[0])

                print(word, "->", neighbors)
                for neighbor in neighbors:
                    try:
                        db.cursor.execute("""INSERT INTO public.closest_words (session_id, ortho_id, score) 
                                            VALUES(%s, %s, %s)""", 
                                            (session_id, neighbor.id, neighbor.ref_score))         
                        db.connexion.commit()
                    except Exception as e:
                        raise Exception("Could not insert neighbor.", neighbor, e)

                for hint_value in hints.keys():
                    for hint in hints[hint_value]:
                        try:
                            db.cursor.execute("""INSERT INTO public.hints (session_id, ortho_id, rectified_score) 
                                                VALUES(%s, %s, %s)""", 
                                                (session_id, hint.id, hint_value))         
                            db.connexion.commit()
                        except Exception as e:
                            raise Exception("Could not insert hint.", hint_value, hint, e)   
                    
            index += 1
            start_utc += 3600 * 24





if __name__ == "__main__":
    load_dotenv()
    db = DbConnexion()
    db.connect()
    load()
    db.disconnect()