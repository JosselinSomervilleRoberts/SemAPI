# -*- coding: utf-8 -*-
"""
Created on Sat Apr 30 20:09:22 2022

@author: josse
"""

import unicodedata
#import re


ft = None
spell = None
nlp = None

# Embedder
def load_gensim():
    global ft
    import fasttext
    if ft is None:
        print("Loading embeddings... May take a while.")
        ft = fasttext.load_model('C:\\Users\\josse\\Documents\\Cemantix\\SemAPI\\data\\wiki.fr.bin')

# Spellchecker
def load_spellchecker():
    from spellchecker import SpellChecker
    global spell
    if spell is None:
        print("Loading spellchecker...")
        spell = SpellChecker(language='fr')

# Lemmatizer
def load_lemmatizer():
    global nlp
    import spacy
    from spacy_lefff import LefffLemmatizer
    from spacy.language import Language
    if nlp is None:
        print("Loading lemmatizer...")
        try:
            @Language.factory('french_lemmatizer')
            def create_french_lemmatizer(nlp, name):
                return LefffLemmatizer()
        except:
            print("Pipeline already set up.")
        nlp = spacy.load('fr_core_news_sm')
        nlp.add_pipe('french_lemmatizer', name='lefff')

def remove_accents(word):
    nfkd_form = unicodedata.normalize('NFKD', word)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode("utf-8").replace(' ', '').replace('\'', '').replace('-', '').lower()

def lemmatize(word):
    global nlp
    load_lemmatizer()
    return nlp(word)[0].lemma_

def correct(word):
    global spell
    load_spellchecker()
    return spell.correction(word)

def check_if_one_is_in(word, elts):
    for elt in elts:
        if elt in word:
            return True
    return False

def isword(word, min_len=3):
    if len(word) < min_len or len(word) > 15:
        return False
    #if check_if_one_is_in(word, [",", ".", ";", '/', ' ', '<', '>', '?', '!', '#', '\\', '\"', '\'']):
    #    return False
    #search_results = re.findall('(\w+)', word)
    #if len(search_results) < 1 or search_results[0] != word:
    #    return False
    #if not check_if_one_is_in(word, ['a', 'e', 'i', 'o', 'u', 'y']):
    #    return False
    #if check_if_one_is_in(word, ['.', ';', ',', '?', ':', '/', '!', '#', '\"', '\'', '{', '}', ')', '(', '[', ']', '\\', '_', '@', '=', '+', '^', '\`', '$', '%']):
    #    return False
    return word.isalpha()


def words_too_similar(w1, w2):
    return w1.lemma == w2.lemma


def gensim_get_vector(w):
    global ft
    load_gensim()
    return ft.get_word_vector(w)

def gensim_get_similar(w, count = 100):
    global ft
    load_gensim()
    return ft.get_nearest_neighbors(w, count)