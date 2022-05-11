import csv
import sys
import os
from tqdm import tqdm
sys.path.append(os.path.abspath('../'))
from connexion import DbConnexion
from word_utils import remove_accents, gensim_get_vector, load_gensim
from dotenv import load_dotenv


def load():
    VILLE_THRESHOD = 10000
    WORD_MIN_LEN = 2
    WORD_MAX_LEN = 32


    def valid_word(word, min_len = WORD_MIN_LEN):
        if len(word) < min_len or len(word) >= WORD_MAX_LEN:
            return False
        if "/" in word or "\"" in word or "." in word or "," in word:
            return False
        return word.replace('\'', '').replace(' ', '').replace('-', '').isalpha()

    def cleanup(word):
        return word.replace('\'', r'\'').replace('\n', '')

    header = None
    def get(row, col_name):
        try:
            return row[header.index(col_name)]
        except:
            raise Exception("Column %s not in header." % col_name)

    data = {"ortho": [], "ortho_na": [], "lemma": [], "lemma_na": [], "type_lemma": [], "genre": [], "number": [], "freq_lemma": [], "freq": [], "nb_syll": [], "nb_letters": [], "lemma_id": [], "vector": [], "vector_lemma": []}


    # Open dataset people
    tsv_file = open("../data/people.tsv", "r", encoding="utf-8")
    print("Counting lines people... ", end='')
    row_count = sum(1 for row in tsv_file)  # fileObject is your csv.reader
    print(row_count)
    tsv_file.seek(0)
    read_tsv = csv.reader(tsv_file, delimiter="\t")

    with tqdm(total=row_count) as pbar:
        # Looping through dataset
        index = 0
        for row in read_tsv:
            pbar.update(1)
            if index == 0:
                header = row
            else:
                ortho = cleanup(get(row, 'name'))

                if valid_word(ortho):
                    # Get word and lemma's infos
                    data["ortho"].append(ortho)
                    data["ortho_na"].append(remove_accents(ortho))
                    data["lemma"].append(ortho)
                    data["lemma_na"].append(remove_accents(ortho))
                    data["type_lemma"].append("NP:pers")
                    genre = 'f'
                    if get(row, 'gender').lower() == 'male':
                        genre = 'm'
                    data["genre"].append(genre)
                    data["number"].append(None)
                    data["freq_lemma"].append(float(get(row, 'TotalPageViews')))
                    data["freq"].append(float(get(row, 'TotalPageViews')))
                    data["nb_syll"].append(None)
                    data["nb_letters"].append(len(ortho))

                    if " " in ortho:
                        ortho = ortho.split(" ")[0]
                        if valid_word(ortho):
                            # Get word and lemma's infos
                            data["ortho"].append(ortho)
                            data["ortho_na"].append(remove_accents(ortho))
                            data["lemma"].append(ortho)
                            data["lemma_na"].append(remove_accents(ortho))
                            data["type_lemma"].append("NP:pre")
                            data["genre"].append(genre)
                            data["number"].append(None)
                            data["freq_lemma"].append(float(get(row, 'TotalPageViews')))
                            data["freq"].append(float(get(row, 'TotalPageViews')))
                            data["nb_syll"].append(None)
                            data["nb_letters"].append(len(ortho))
            index += 1



    # Open dataset countries
    tsv_file = open("../data/etats_utf8.csv", "r", encoding="utf-8")
    print("Counting lines etats... ", end='')
    row_count = sum(1 for row in tsv_file)  # fileObject is your csv.reader
    print(row_count)
    tsv_file.seek(0)
    read_tsv = csv.reader(tsv_file, delimiter=";")

    with tqdm(total=row_count) as pbar:
        # Looping through dataset
        index = 0
        for row in read_tsv:
            pbar.update(1)
            if index == 0:
                header = row
            else:
                ortho_country = cleanup(get(row, 'NOM_ALPHA'))
                ortho_capital = cleanup(get(row, 'CAPITALE'))

                if valid_word(ortho_country):
                    # Get word and lemma's infos
                    data["ortho"].append(ortho_country)
                    data["ortho_na"].append(remove_accents(ortho_country))
                    data["lemma"].append(ortho_country)
                    data["lemma_na"].append(remove_accents(ortho_country))
                    data["type_lemma"].append("NP:coun")
                    data["genre"].append(None)
                    data["number"].append(None)
                    data["freq_lemma"].append(0)
                    data["freq"].append(0)
                    data["nb_syll"].append(None)
                    data["nb_letters"].append(len(ortho_country))

                if valid_word(ortho_capital):
                    # Get word and lemma's infos
                    data["ortho"].append(ortho_capital)
                    data["ortho_na"].append(remove_accents(ortho_capital))
                    data["lemma"].append(ortho_capital)
                    data["lemma_na"].append(remove_accents(ortho_capital))
                    data["type_lemma"].append("NP:city")
                    data["genre"].append(None)
                    data["number"].append(None)
                    data["freq_lemma"].append(0)
                    data["freq"].append(0)
                    data["nb_syll"].append(None)
                    data["nb_letters"].append(len(ortho_capital))
            index += 1



    # Open dataset cities
    tsv_file = open("../data/villes_france.csv", "r", encoding="utf-8")
    print("Counting lines cities (VILLE_THRESHOD = %d) ... " % VILLE_THRESHOD, end='')
    row_count = sum(1 for row in tsv_file)  # fileObject is your csv.reader
    print(row_count)
    tsv_file.seek(0)
    read_tsv = csv.reader(tsv_file, delimiter=",")

    with tqdm(total=row_count) as pbar:
        # Looping through dataset
        index = 0
        for row in read_tsv:
            pbar.update(1)
            if index == 0:
                header = row
            else:
                ortho = cleanup(row[2].replace('\"', ''))
                nombre = int(row[14].replace('\"', ''))

                if valid_word(ortho) and nombre >= VILLE_THRESHOD:
                    # Get word and lemma's infos
                    data["ortho"].append(ortho)
                    data["ortho_na"].append(remove_accents(ortho))
                    data["lemma"].append(ortho)
                    data["lemma_na"].append(remove_accents(ortho))
                    data["type_lemma"].append("NP:city")
                    data["genre"].append(None)
                    data["number"].append(None)
                    data["freq_lemma"].append(float(nombre) / VILLE_THRESHOD)
                    data["freq"].append(float(nombre) / VILLE_THRESHOD)
                    data["nb_syll"].append(None)
                    data["nb_letters"].append(len(ortho))
            index += 1



    # Open dataset words
    tsv_file = open("../data/Lexique383.tsv", "r", encoding="utf-8")
    print("Counting lines lexique... ", end='')
    row_count = sum(1 for row in tsv_file)  # fileObject is your csv.reader
    print(row_count)
    tsv_file.seek(0)
    read_tsv = csv.reader(tsv_file, delimiter="\t")

    with tqdm(total=row_count) as pbar:
        # Looping through dataset
        index = 0
        for row in read_tsv:
            pbar.update(1)
            if index == 0:
                header = row
            else:
                ortho = cleanup(get(row, 'ortho'))
                lemma = cleanup(get(row, 'lemme'))

                if valid_word(ortho) and valid_word(lemma):
                    # Get word and lemma's infos
                    data["ortho"].append(ortho)
                    data["ortho_na"].append(remove_accents(ortho))
                    data["lemma"].append(lemma)
                    data["lemma_na"].append(remove_accents(lemma))
                    data["type_lemma"].append(get(row, 'cgram'))
                    data["genre"].append(get(row, 'genre'))
                    data["number"].append(get(row, 'nombre'))
                    data["freq_lemma"].append(float(get(row, 'freqlemfilms2')))
                    data["freq"].append(float(get(row, 'freqfilms2')))
                    data["nb_syll"].append(int(get(row, 'nbsyll')))
                    data["nb_letters"].append(int(get(row, 'nblettres')))
            index += 1
    print(len(data["ortho"]))



    # LOAD DB AND GENSIM
    db = DbConnexion()
    db.connect()
    load_gensim("../data/wiki.fr.bin")

    # INSERT INTO DB
    for i in tqdm(range(len(data['ortho']))):
        ortho = data["ortho"][i]
        ortho_na = data["ortho_na"][i]
        lemma = data["lemma"][i]
        lemma_na = data["lemma_na"][i]
        type_lemma = data["type_lemma"][i]
        genre = data["genre"][i]
        number = data["number"][i]
        freq_lemma = data["freq_lemma"][i]
        freq = data["freq"][i]
        nb_syll = data["nb_syll"][i]
        nb_letters = data["nb_letters"][i]

        vec_lemma = None
        try:
            vec_lemma = gensim_get_vector(lemma).tolist()
        except Exception as e:
            print("Lemma %s not known by gensim." % lemma, e)

        if not vec_lemma is None:
            # Get the Lemma ID and insert it if necessary
            lemma_id = None
            db.cursor.execute("""SELECT lemma_id 
                                FROM lemmas WHERE lemma = %s""", 
                                (lemma,))
            res = db.cursor.fetchone() 
            if res is None:
                try:
                    db.cursor.execute("""INSERT INTO lemmas(lemma, lemma_na, freq, type, vector) 
                                        VALUES(%s, %s, %s, %s, %s)""", 
                                        (lemma, lemma_na, freq_lemma, type_lemma, vec_lemma))
                    db.connexion.commit()
                    db.cursor.execute("""SELECT lemma_id 
                                        FROM lemmas WHERE lemma = %s""", 
                                        (lemma,))
                    res = db.cursor.fetchone()
                    if res is None:
                        raise Exception("The lemma %s was not properly added." % (lemma))
                except Exception as e:
                    db.connexion.commit()
                    print("Exception Insertion lemma %s" % lemma, e)
                    vec_lemma = None

            if not vec_lemma is None:
                lemma_id = int(res[0])

                # Insert the word
                vec_ortho = None
                try:
                    vec_ortho = gensim_get_vector(ortho).tolist()
                except Exception as e:
                    vec_ortho = vec_lemma
                    print("Ortho %s not known by gensim - Using vector of its lemma %s" % (ortho, lemma), e)
                try:
                    db.cursor.execute("""INSERT INTO orthos(lemma_id, ortho, ortho_na, genre, number, freq, nb_syll, nb_letters, vector) 
                                        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                                        (lemma_id, ortho, ortho_na, genre, number, freq, nb_syll, nb_letters, vec_ortho))
                    db.connexion.commit()
                except Exception as e:
                    try:
                        db.connexion.commit()
                        db.cursor.execute("""SELECT ortho_id, freq 
                                            FROM orthos 
                                            WHERE ortho = %s""", 
                                            (ortho,))
                        res = db.cursor.fetchone()
                        if freq > int(res[1]):
                            db.cursor.execute("""UPDATE orthos 
                                                SET lemma_id = %s, genre = %s, number =  %s, freq = %s WHERE ortho_id = %s""", 
                                                (lemma_id, genre, number, freq, res[0]))
                    except Exception as e:        
                        db.connexion.commit()
                        print("Exception Insertion orth %s" % ortho, e)
            else:
                print('\t-Ignoring word %s' % ortho)





if __name__ == "__main__":
    load_dotenv()
    db = DbConnexion()
    db.connect()
    load()
    db.disconnect()