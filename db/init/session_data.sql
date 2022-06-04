/* This script uses tables declared in words.sql 
and in sessions.sql */

/* Stores the scores of a given user on a given session 
This stores every score for every guess and not just the last one */
CREATE TABLE IF NOT EXISTS scores (
	score_id serial PRIMARY KEY,
	session_id serial NOT NULL,
	user_id serial NOT NULL,
	ortho_id serial NOT NULL,
	score FLOAT DEFAULT 0 NOT NULL,
	UNIQUE(session_id, user_id, ortho_id),

	CONSTRAINT fk_sessions
      		FOREIGN KEY(session_id)
	  		REFERENCES fr_sessions(session_id )
				ON DELETE CASCADE,

	CONSTRAINT fk_users
      		FOREIGN KEY(user_id)
	  		REFERENCES users(user_id )
				ON DELETE CASCADE,

	CONSTRAINT fk_orthos
  	    	FOREIGN KEY(ortho_id)
			REFERENCES fr_orthos(ortho_id )
			ON DELETE CASCADE
);

/* This stores the hints used by an user to keep track of the added
penalties but also provide the answer of a hint at any time */
CREATE TABLE IF NOT EXISTS used_hints (
	hint_id serial PRIMARY KEY,
	session_id serial NOT NULL,
	user_id serial NOT NULL,
	hint_type INTEGER NOT NULL,
	UNIQUE(session_id, user_id, hint_type),
	cost INTEGER NOT NULL,
	result VARCHAR(50),

	CONSTRAINT fk_sessions
      		FOREIGN KEY(session_id)
	  		REFERENCES fr_sessions(session_id )
				ON DELETE CASCADE,

	CONSTRAINT fk_users
      		FOREIGN KEY(user_id)
	  		REFERENCES users(user_id )
				ON DELETE CASCADE
);

/* This stores the final score of a user for a given session.
(so one score per user per session) This is only set if the
user wins the session of surrender. */
CREATE TABLE IF NOT EXISTS final_scores (
	id serial PRIMARY KEY,
	session_id serial NOT NULL,
	user_id serial NOT NULL,
	score FLOAT DEFAULT 0 NOT NULL,
	nb_attempts INTEGER DEFAULT 1 NOT NULL,
	has_won BOOLEAN DEFAULT False,
	utc_date_ms bigserial,
	UNIQUE(session_id, user_id),

	CONSTRAINT fk_sessions
      		FOREIGN KEY(session_id)
	  		REFERENCES fr_sessions(session_id )
				ON DELETE CASCADE,

	CONSTRAINT fk_users
      		FOREIGN KEY(user_id)
	  		REFERENCES users(user_id )
				ON DELETE CASCADE
);

/* This table stores the info of if a user played on a given
session or not, when it started and stopped playing and if
he is still playing. */
CREATE TABLE IF NOT EXISTS activity (
	id serial PRIMARY KEY,
	session_id serial NOT NULL,
	user_id serial NOT NULL,
	UNIQUE(session_id, user_id),
	utc_start_ms bigserial,
	utc_end_ms bigserial,
	active BOOLEAN DEFAULT True,

	CONSTRAINT fk_sessions
      		FOREIGN KEY(session_id)
	  		REFERENCES fr_sessions(session_id )
				ON DELETE CASCADE,

	CONSTRAINT fk_users
      		FOREIGN KEY(user_id)
	  		REFERENCES users(user_id )
				ON DELETE CASCADE
);