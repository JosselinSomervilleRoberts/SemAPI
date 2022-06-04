# Make data dir
mkdir -p $API_PATH/data

# Pantheon
if ! test -f "$API_PATH/data/pantheon.tsv"; then
    echo 'Dowloading pantheon.tsv ...'
    echo "$API_PATH/data/pantheon.tsv"
    wget --no-check-certificate -O pantheon.tsv 'https://drive.google.com/uc?export=download&id=1MbOc7ZXezdIpsMD-Oh0GUweaz4HIlCAD'
else
    echo 'File already present: pantheon.tsv'
fi

# Countries and capitals
if ! test -f "$API_PATH/data/etats_utf8.csv"; then
    echo 'Dowloading etats.csv ...'
    wget -O etats.csv https://www.data.gouv.fr/fr/datasets/r/10bfaf29-2d13-48a3-bf6b-7ea8725c9ff2
    iconv -f ISO-8859-1 -t UTF-8//TRANSLIT etats.csv -o etats_utf8.csv
    rm etats.csv
else
    echo 'File already present: etats.csv'
fi

# French cities
if ! test -f "$API_PATH/data/villes_france.csv"; then
    echo 'Dowloading villes_france.csv ...'
    wget -O villes_france.csv https://sql.sh/ressources/sql-villes-france/villes_france.csv
else
    echo 'File already present: villes_france.csv'
fi

# Lexique 3.83
if ! test -f "$API_PATH/data/Lexique383.tsv"; then
    echo 'Dowloading Lexique383.tsv ...'
    wget -O Lexique.zip http://www.lexique.org/databases/Lexique383/Lexique383.zip
    unzip Lexique.zip -d Lexique
    mv $API_PATH/data/Lexique/Lexique383.tsv $API_PATH/data
    rm -r Lexique
    rm Lexique.zip
else
    echo 'File already present: Lexique383.tsv'
fi


# Word2Vec
if ! test -f "$API_PATH/data/frWac_no_postag_no_phrase_700_skip_cut50.bin"; then
    echo 'Dowloading frWac_no_postag_no_phrase_700_skip_cut50.bin ...'
    wget -O 'frWac_no_postag_no_phrase_700_skip_cut50.bin' https://embeddings.net/embeddings/frWac_no_postag_no_phrase_700_skip_cut50.bin
else
    echo 'File already present: frWac_no_postag_no_phrase_700_skip_cut50.bin'
fi
