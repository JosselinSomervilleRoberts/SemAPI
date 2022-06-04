/* This script uses tables declared in users.sql */

/* This table stores every request on the API */
CREATE TABLE IF NOT EXISTS requests (
	request_id serial PRIMARY KEY,
	method VARCHAR(5) DEFAULT 'GET' NOT NULL,
	route VARCHAR (25) NOT NULL,
	params VARCHAR (100),
	user_id serial NOT NULL,
	status SMALLINT DEFAULT 500 NOT NULL,
	utc_date_ms bigserial,

	CONSTRAINT fk_users
      		FOREIGN KEY(user_id)
	  		REFERENCES users(user_id )
				ON DELETE CASCADE
);