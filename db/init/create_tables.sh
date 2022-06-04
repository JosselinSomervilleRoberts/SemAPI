# Env variables
source $API_PATH/.env

# Create the database
echo "Using DB user:" $DB_USER
export PGPASSWORD=$DB_PASSWORD
psql -d word2vec -U $DB_USER -f $API_PATH/db/init/users.sql
psql -d word2vec -U $DB_USER -f $API_PATH/db/init/words.sql
psql -d word2vec -U $DB_USER -f $API_PATH/db/init/sessions.sql
psql -d word2vec -U $DB_USER -f $API_PATH/db/init/session_data.sql
psql -d word2vec -U $DB_USER -f $API_PATH/db/init/logging.sql