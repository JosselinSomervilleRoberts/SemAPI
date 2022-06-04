# Env variables
source $API_PATH/.env

# Creating the database
echo "Using DB user:" $DB_USER
export PGPASSWORD=$DB_PASSWORD
psql -U $DB_USER -c 'CREATE DATABASE word2vec'

# Creating the tables
source $API_PATH/db/init/create_tables.sh