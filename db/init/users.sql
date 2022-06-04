/* Simple representation of a User */
CREATE TABLE IF NOT EXISTS users (
	user_id serial PRIMARY KEY,
	name VARCHAR(32) NOT NULL,
	tag INTEGER NOT NULL,
	UNIQUE(name, tag)
);