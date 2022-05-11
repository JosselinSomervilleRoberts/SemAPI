import os
import sys
sys.path.append(os.path.abspath('../'))
from connexion import DbConnexion
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()
    db = DbConnexion()
    db.connect()
    db.cursor.execute("""CREATE TABLE users (
        user_id VARCHAR(15) UNIQUE,
        name VARCHAR(10) NOT NULL,
        tag INTEGER NOT NULL,
        UNIQUE(name, tag)
    );


    CREATE TABLE corrections (
        correction_id serial PRIMARY KEY,
        ortho_id serial NOT NULL,
        word VARCHAR (32) UNIQUE NOT NULL,

        CONSTRAINT fk_orthos
                FOREIGN KEY(ortho_id)
                REFERENCES orthos(ortho_id )
                ON DELETE CASCADE
    );


    CREATE TABLE requests (
        request_id serial PRIMARY KEY,
        method VARCHAR(5) DEFAULT 'GET' NOT NULL,
        route VARCHAR (25) NOT NULL,
        params VARCHAR (100),
        user_id VARCHAR (15),
        status SMALLINT DEFAULT 500 NOT NULL,
        utc_date_ms bigserial,

        CONSTRAINT fk_users
                FOREIGN KEY(user_id)
                REFERENCES users(user_id )
                    ON DELETE CASCADE
    );


    CREATE TABLE scores (
        score_id serial PRIMARY KEY,
        session_id serial NOT NULL,
        user_id VARCHAR (15),
        ortho_id serial NOT NULL,
        score FLOAT DEFAULT 0 NOT NULL,
        UNIQUE(session_id, user_id, ortho_id),

        CONSTRAINT fk_sessions
                FOREIGN KEY(session_id)
                REFERENCES sessions(session_id )
                    ON DELETE CASCADE,

        CONSTRAINT fk_users
                FOREIGN KEY(user_id)
                REFERENCES users(user_id )
                    ON DELETE CASCADE,

        CONSTRAINT fk_orthos
                FOREIGN KEY(ortho_id)
                REFERENCES orthos(ortho_id )
                ON DELETE CASCADE
    );


    CREATE TABLE final_scores (
        id serial PRIMARY KEY,
        session_id serial NOT NULL,
        user_id VARCHAR (15),
        score FLOAT DEFAULT 0 NOT NULL,
        nb_attempts INTEGER DEFAULT 1 NOT NULL,
        has_won BOOLEAN DEFAULT False,
        utc_date_ms bigserial,
        UNIQUE(session_id, user_id),

        CONSTRAINT fk_sessions
                FOREIGN KEY(session_id)
                REFERENCES sessions(session_id )
                    ON DELETE CASCADE,

        CONSTRAINT fk_users
                FOREIGN KEY(user_id)
                REFERENCES users(user_id )
                    ON DELETE CASCADE
    );

    CREATE TABLE activity (
        id serial PRIMARY KEY,
        session_id serial NOT NULL,
        user_id VARCHAR (15),
        UNIQUE(session_id, user_id),
        utc_start_ms bigserial,
        utc_end_ms bigserial DEFAULT 0 NOT NULL,
        active BOOLEAN DEFAULT True,

        CONSTRAINT fk_sessions
                FOREIGN KEY(session_id)
                REFERENCES sessions(session_id )
                    ON DELETE CASCADE,

        CONSTRAINT fk_users
                FOREIGN KEY(user_id)
                REFERENCES users(user_id )
                    ON DELETE CASCADE
    );""")
    db.connexion.commit()
    db.disconnect()
