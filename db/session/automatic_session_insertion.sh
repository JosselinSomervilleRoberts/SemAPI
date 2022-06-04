# At 23:30, add a new session if there is not one
crontab -l > mycron
COMMAND="python3 $API_PATH/db/session/automatic_session_insertion.py"
grep "$COMMAND" ./mycron || echo "30 23 * * * $COMMAND" >> mycron
crontab mycron
rm mycron