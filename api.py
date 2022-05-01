# -*- coding: utf-8 -*-
import flask
from flask import request, jsonify
from data_manager import DataManager
from connexion import DbConnexion
from word import Word
from datetime import datetime
import random

app = flask.Flask(__name__)
#app.config["DEBUG"] = True

dm = DataManager()
db = DbConnexion()
db.connect()

def current_session_id(lang = 'fr'):
    global db, dm
    current_utc = int(datetime.now().timestamp())
    return dm.get_session_id(db, current_utc, lang)
    

@app.route('/session-id', methods=['GET'])
def session_id():
    session_id = None
    try:
        session_id = current_session_id()
    except Exception as e:
        return 'Internal error: could not get session id. %s' % e, 500
    res = {}
    res['session_id'] = session_id
    return jsonify(res), 200
    
    
@app.route('/score', methods=['GET'])
def score():
    global db, dm

    lang = 'fr'
    correction = True
    user_id = None
    session_id = None
    word = ''
    
    # Get params
    if 'word' in request.args:
        word = str(request.args['word'])
    else:
        return "Missing parameter: word.", 400
    if 'user_id' in request.args:
        user_id = int(request.args['user_id'])
    if 'session_id' in request.args:
        session_id = int(request.args['session_id'])
    if 'correction' in request.args:
        correction = bool(request.args['correction'])
    if 'lang' in request.args:
        lang = str(request.args['lang'])

    # Find the baseline
    if session_id is None:
        try:
            session_id = current_session_id(lang)
        except Exception as e:
            return 'Internal error: could not get session id. %s' %e, 500
    baseline = None
    try:
        baseline = dm.get_session_infos(db, session_id)['word']
    except Exception as e:
        return 'Internal error: baseline not found. %s' %e, 500
        
    # Load the word
    word_object = Word(word = word, lang = lang)
    try:
        word_object.load_from_word(db)
    except: # This means that the word was not found or there was an error
        # So we try to correct it
        try:
            corrected = word_object.get_corrected(db)
            if not corrected is None:
                score = corrected.compute_rectified_score(baseline)
                return jsonify({"user_id": user_id, "session_id": session_id, "error": "404", "word": word, "suggested": corrected.word, "score_suggested": score}), 200
            else:
                return jsonify({"user_id": user_id, "session_id": session_id, "error": "404", "word": word}), 200
        except:
            return jsonify({"user_id": user_id, "session_id": session_id, "error": "404", "word": word}), 200

    # Everything was fetched properly, let's compute the score
    res_score = word_object.compute_rectified_score_corrected(db, baseline)
    res = {}
    res['user_id'] = user_id
    res['session_id'] = session_id
    res['word'] = word
    res['score'] = res_score['score']
    if correction:
        if 'suggested' in res_score:
            res['suggested'] = res_score['suggested']
        if 'score_suggested' in res_score:
            res['score_suggested'] = res_score['score_suggested']
    return jsonify(res), 200


@app.route('/hint', methods=['GET'])
def hint():
    global db, dm

    lang = 'fr'
    user_id = None
    session_id = None
    value = 0
    
    # Get params
    if 'value' in request.args:
        value = float(request.args['value'])
    else:
        return "Missing parameter: value.", 400
    if 'user_id' in request.args:
        user_id = int(request.args['user_id'])
    if 'session_id' in request.args:
        session_id = int(request.args['session_id'])
    else:
        return "Missing parameter: session_id.", 400
    if 'lang' in request.args:
        lang = str(request.args['lang'])

    # Check that the user does not ask for the solution
    if value > 0.9:
        return jsonify({"user_id": user_id, "session_id": session_id, "error": "No clues available after 0.9."}), 200

    # Find the hints
    hints = None
    try:
        hints = dm.get_session_infos(db, session_id)['hints']
    except Exception as e:
        return 'Internal error: hints not found. %s' %e, 500

    # Return the closest hint
    for score in hints.keys():
        if 1 > score >= value:
            hint = random.choice(hints[score])
            return jsonify({"user_id": user_id, "session_id": session_id, "word": hint.word, "score": score}), 200

    # No hint was found, this is not normal
    return "Internal error: No clue found.", 500

app.run()