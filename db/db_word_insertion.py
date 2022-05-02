import csv
import sys
import os
from tqdm import tqdm
sys.path.append(os.path.abspath('../'))
from connexion import DbConnexion
from word_utils import remove_accents, gensim_get_vector, load_gensim

# Connect to db
db = DbConnexion()
db.connect()

# Open dataset
tsv_file = open("../data/Lexique383.tsv", "r", encoding="utf-8")
print("Counting lines... ", end='')
row_count = sum(1 for row in tsv_file)  # fileObject is your csv.reader
print(row_count)
tsv_file.seek(0)
read_tsv = csv.reader(tsv_file, delimiter="\t")
load_gensim(test=False)


def valid_word(word, min_len=2):
    if len(word) < min_len or len(word) >= 20:
        return False
    if " " in word or "\'" in word:
        return False
    return word.isalpha()

header = None
def get(row, col_name):
    try:
        return row[header.index(col_name)]
    except:
        raise Exception("Column %s not in header." % col_name)

with tqdm(total=row_count) as pbar:
    # Looping through dataset
    index = 0
    for row in read_tsv:
        pbar.update(1)
        if index == 0:
            header = row
        else:
            # Get word and lemma's infos
            ortho = get(row, 'ortho')
            ortho_na = remove_accents(ortho)
            lemma = get(row, 'lemme')
            lemma_na = remove_accents(lemma)
            type_lemma = get(row, 'cgram')
            genre = get(row, 'genre')
            number = get(row, 'nombre')
            freq_lemma = float(get(row, 'freqlemfilms2'))
            freq = float(get(row, 'freqfilms2'))
            nb_syll = int(get(row, 'nbsyll'))
            nb_letters = int(get(row, 'nblettres'))

            if valid_word(ortho) and valid_word(lemma):
                # Get the lemma's vector
                vec_lemma_str = None
                lemma_known = True
                try:
                    vec_lemma = gensim_get_vector(lemma)
                    vec_lemma_str = "[" + ", ".join([str(x) for x in vec_lemma]) + "]"
                except Exception as e:
                    lemma_known = False
                    print("Lemma %s not known by gensim." % lemma, e)
                
                # Get the Lemma ID and insert it if necessary
                if lemma_known:
                    lemma_id = None
                    db.cursor.execute("SELECT lemma_id FROM lemmas WHERE lemma = \'%s\'" % lemma)
                    res = db.cursor.fetchone() 
                    if res is None:
                        try:
                            db.cursor.execute("INSERT INTO lemmas(lemma, lemma_na, freq, type, vector) VALUES(\'%s\', \'%s\', %f, \'%s\', ARRAY%s)" % (lemma, lemma_na, freq_lemma, type_lemma, vec_lemma_str))
                            db.connexion.commit()
                            db.cursor.execute("SELECT lemma_id FROM lemmas WHERE lemma = \'%s\'" % lemma)
                            res = db.cursor.fetchone()
                            if res is None:
                                raise Exception("The lemma %s was not properly added." % lemma)
                        except Exception as e:
                            db.connexion.commit()
                            print("Exception Insertion lemma %s" % lemma, e)
                            lemma_known = False

                if lemma_known:
                    lemma_id = int(res[0])

                    # Insert the word
                    vec_ortho_str = None
                    try:
                        vec_ortho = gensim_get_vector(ortho)
                        vec_ortho_str = "[" + ", ".join([str(x) for x in vec_ortho]) + "]"
                    except Exception as e:
                        vec_ortho_str = vec_lemma_str
                        print("Ortho %s not known by gensim - Using vector of its lemma %s" % (ortho, lemma), e)
                    try:
                        db.cursor.execute("INSERT INTO orthos(lemma_id, ortho, ortho_na, genre, number, freq, nb_syll, nb_letters, vector) VALUES(%d, \'%s\', \'%s\', \'%s\', \'%s\', %f, %d, %d, ARRAY%s)" % (lemma_id, ortho, ortho_na, genre, number, freq, nb_syll, nb_letters, vec_ortho_str))
                        db.connexion.commit()
                    except Exception as e:
                        try:
                            db.connexion.commit()
                            db.cursor.execute("SELECT ortho_id, freq FROM orthos WHERE ortho = \'%s\'" % ortho)
                            res = db.cursor.fetchone()
                            if freq > int(res[1]):
                                db.cursor.execute("UPDATE orthos SET lemma_id = %d, genre = \'%s\', number =  \'%s\', freq = %d WHERE ortho_id = %d" % (lemma_id, genre, number, freq, res[0]))
                        except Exception as e:        
                            db.connexion.commit()
                            print("Exception Insertion orth %s" % ortho, e)
                else:
                    print('\t-Ignoring word %s' % ortho)
            else:
                print('Non valid word %s' % ortho)

        index += 1

db.disconnect()