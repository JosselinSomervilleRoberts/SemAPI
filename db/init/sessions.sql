/* This script uses tables declared in words.sql */

/* Stores basic infos on a session:
    - When it starts and when it ends
    - The ortho to guess
    - The difficulty (UNUSED) */
CREATE TABLE IF NOT EXISTS fr_sessions (
	session_id serial PRIMARY KEY,
	ortho_id serial UNIQUE NOT NULL,
	utc_start bigserial,
	utc_stop bigserial,
	difficulty smallint DEFAULT 1,
	
	CONSTRAINT fk_orthos
  	    	FOREIGN KEY(ortho_id)
			REFERENCES fr_orthos(ortho_id )
			ON DELETE CASCADE
);

/* This table stores all the precomputed scores for a session
This takes into account rectifications */
CREATE TABLE IF NOT EXISTS fr_scores_computed (
	session_id serial NOT NULL,
	lemma_id serial NOT NULL,
	UNIQUE(session_id, lemma_id),
	similarity FLOAT DEFAULT 0 NOT NULL,
	score FLOAT DEFAULT 0 NOT NULL,

	CONSTRAINT fk_sessions
      		FOREIGN KEY(session_id)
	  		REFERENCES fr_sessions(session_id )
				ON DELETE CASCADE,

    CONSTRAINT fk_lemmas
  	    	FOREIGN KEY(lemma_id)
			REFERENCES fr_lemmas(lemma_id)
			ON DELETE CASCADE
);

/* This is a way of changing the score of a given lemma as well
as the other related lemmas (based on the similarity_min factor) */
CREATE TABLE IF NOT EXISTS fr_rectifications (
	rectification_id serial PRIMARY KEY,
	session_id serial NOT NULL,
	lemma_id serial NOT NULL,
	UNIQUE(session_id, lemma_id),
	old_score FLOAT DEFAULT 0 NOT NULL,
	new_score FLOAT DEFAULT 0 NOT NULL,
	similarity_min FLOAT DEFAULT 0 NOT NULL,

	CONSTRAINT fk_sessions
      		FOREIGN KEY(session_id)
	  		REFERENCES fr_sessions(session_id )
				ON DELETE CASCADE,

    CONSTRAINT fk_lemmas
  	    	FOREIGN KEY(lemma_id)
			REFERENCES fr_lemmas(lemma_id)
			ON DELETE CASCADE
);