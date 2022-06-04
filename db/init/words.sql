/* A lemma is the "base" of a word.
As an example "manger" and "mangera" have the same lemma: "manger"
- lemma_na corresponds to lemma without accents and spaces
- type represents the Nature of a word. The types are:
    - ADJ       -> adjectif
    - ADJ:dem   -> adjectif demonstratif
    - ADJ:ind   -> adjectif indetermine
    - ADJ:int   
    - ADJ:num
    - ADJ:pos   -> Adjectif possessif
    - ADV       -> Adverbe
    - ART:def   -> Article defini
    - ART:ind   -> Article indefini
    - AUX       -> Auxiliaire (TODO: change to VERB)
    - CON
    - NOM       -> Nom
    - NP:city   -> Nom propre de ville
    - ONO
    - PRE       -> Preposition
    - PRO:dem   
    - PRO:ind   -> Pronom indetermine
    - PRO:int
    - PRO:per
    - VER
- freq represents the frequency in the French language
- vector is the gensim Word2vec embedding of the lemma*/
CREATE TABLE IF NOT EXISTS fr_lemmas (
	lemma_id serial PRIMARY KEY,
	lemma VARCHAR (32) NOT NULL,
	lemma_na VARCHAR (32) NOT NULL,
    type VARCHAR(8),
    UNIQUE(lemma, type),
	freq FLOAT DEFAULT 0,
	vector FLOAT ARRAY[700] NOT NULL
);

/* An ortho is a word or expression that has an associated lemma
Such as a lemma it has an _na and a freq.
In addition it can have a genre and/or number*/
CREATE TABLE IF NOT EXISTS fr_orthos (
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

/* Stores the X lemmas most similar to lemma_id1 */
CREATE TABLE IF NOT EXISTS fr_closest_lemmas (
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
);

/* This table is used to cache spellcheck corrections as it
is quite long to run the spellcheck function. */
CREATE TABLE IF NOT EXISTS corrections (
	correction_id serial PRIMARY KEY,
	ortho_id serial NOT NULL,
	word VARCHAR (32) UNIQUE NOT NULL,

	CONSTRAINT fk_orthos
  	    	FOREIGN KEY(ortho_id)
			REFERENCES fr_orthos(ortho_id )
			ON DELETE CASCADE
);