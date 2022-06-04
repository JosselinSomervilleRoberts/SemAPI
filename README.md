# Word2Vec API

Josselin Somerville Roberts - All Rights Reserved

## Getting started

### Dependencies
To install the API:
```bash
pip3 install -r requirements.txt
```

### Populating the database
Download the folling dataset and place them in data with the following names:

- *wiki.fr.bin* (as ***data/wiki.fr.bin*** - Download the French *bin + text*) - Encoding of french words: <https://fasttext.cc/docs/en/pretrained-vectors.html>

- *Lexique 3.83* (as ***Lexique383.tsv*** - Use the TSV file from the archive) - French words with lemmas and other useful info: <http://www.lexique.org>

- *Pantheon 1.0* (as ***data/people.tsv*** - Choose the TSV file) - Famous people: <https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/28201/VEG34D&version=1.0>

- French cities (as ***data/villes_france.csv*** - Choose the CSV file) : <https://sql.sh/736-base-donnees-villes-francaises>
   
- Countries and capitals (as ***data/etats_utf8.csv*** - make sure that to encode it as utf-8, as the provided file is not) : <https://www.data.gouv.fr/en/datasets/etats-et-capitales-du-monde/>'


Create a database called **word2vec** and crete the table by pasting the SQL commands provided in ```db/create_db.txt```.

Set up your ```.env``` file, at the root of the project, with the database info and the API desired port. Here is an example:
```text
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=admin
API_PORT=9696
```

Then run the following scripts in this order (it should take 15 minutes for the first one and between 5 and 10 minutes for the second one) :

```bash
cd db
python3 .\db_word_insertion.py
python3 .\db_sessions_insertion.py
```

### Launching the API

Finally you can launch the API from the root folder of the project with :
```bash
python3 .\api.py
```
Here is the expected output:
```bash
 * Serving Flask app 'api' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:9696/ (Press CTRL+C to quit)
```

## Using the API

All routes are described in the **swagger.yaml** file.

If you do not know how to visualize a swagger file, visit https://editor.swagger.io and copy paste the content of the **swagger.yaml** file.

Then from the preview of the swagger you can directly try the routes by first choosing a server (either Local of Philippe's one) and clicking on the *Try it out* button for each route.