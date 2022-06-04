# Getting API Path
export API_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
export DB_PATH=$API_PATH/db
echo $API_PATH

# Env variables
source $API_PATH/.env

# Python depedencies
pip3 install -r requirements.txt

# Create DB and populate it
sudo service postgresql start
source $API_PATH/db/init/init_main.sh

# Create sessions
COUNT_SESSIONS=`psql -d word2vec -U $DB_USER -AXqtc 'SELECT COUNT(*) FROM fr_sessions'`
if [ $COUNT_SESSIONS == 0 ];
then
    python3 $API_PATH/db/session/init_insert_session.py
else
    echo "Sessions already present in Database."
    echo "There are already $COUNT_SESSIONS sessions."
fi

# Set a CRON to add sessions automatically
source $API_PATH/db/session/automatic_session_insertion.sh