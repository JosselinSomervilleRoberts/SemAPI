# Getting API Path
export API_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Restart postgres
sudo service postgresql start

# Run the API
python3 $API_PATH/api.py