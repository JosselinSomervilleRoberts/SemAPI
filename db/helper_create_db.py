import os
import sys
sys.path.append(os.path.abspath('../'))
from connexion import DbConnexion
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()
    db = DbConnexion()
    db.connect()
    db.cursor.execute("""CREATE TABLE fr_lemmas (
	lemma_id serial PRIMARY KEY,
	lemma VARCHAR (32) NOT NULL,
	lemma_na VARCHAR (32) NOT NULL,
    type VARCHAR(8),
    UNIQUE(lemma, type),
	freq FLOAT DEFAULT 0,
	vector FLOAT ARRAY[700] NOT NULL
);

CREATE TABLE fr_orthos (
    ortho_id serial PRIMARY KEY,
    lemma_id serial NOT NULL,
	ortho VARCHAR (32) UNIQUE NOT NULL,
	ortho_na VARCHAR (32) NOT NULL,
    freq FLOAT DEFAULT 0,
    genre VARCHAR (2) DEFAULT '',
    number VARCHAR (2) DEFAULT '',
    nb_syll SMALLINT,
    nb_letters SMALLINT NOT NULL,

    CONSTRAINT fk_lemmas
  	    	FOREIGN KEY(lemma_id)
			REFERENCES fr_lemmas(lemma_id)
			ON DELETE CASCADE
);

CREATE TABLE fr_closest_lemmas (
	lemma_id1 serial NOT NULL,
	lemma_id2 serial NOT NULL,
	UNIQUE(lemma_id1, lemma_id2),
	rank INTEGER NOT NULL,
	similarity FLOAT DEFAULT 0 NOT NULL,

    CONSTRAINT fk_lemmas1
  	    	FOREIGN KEY(lemma_id1)
			REFERENCES fr_lemmas(lemma_id)
			ON DELETE CASCADE,

    CONSTRAINT fk_lemmas2
  	    	FOREIGN KEY(lemma_id2)
			REFERENCES fr_lemmas(lemma_id)
			ON DELETE CASCADE
);""")
    db.connexion.commit()
    db.disconnect()
