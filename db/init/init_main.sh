# Create Database
source $API_PATH/db/init/create_database.sh

# Download data
source $API_PATH/db/init/download_data.sh

# Env variables
source $API_PATH/.env

# Insert words into DB
echo "Using DB user:" $DB_USER
export PGPASSWORD=$DB_PASSWORD
COUNT_LEMMAS=`psql -d word2vec -U $DB_USER -AXqtc 'SELECT COUNT(*) FROM fr_lemmas'`
COUNT_ORTHOS=`psql -d word2vec -U $DB_USER -AXqtc 'SELECT COUNT(*) FROM fr_orthos'`
if [ $COUNT_LEMMAS -gt 30000 ] && [ $COUNT_ORTHOS -gt 80000 ];
then
    echo 'Database already populated with' $COUNT_LEMMAS 'lemmas and' $COUNT_ORTHOS 'orthos.'
else
    python3 $API_PATH/db/init/insert_words.py
fi