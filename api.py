# -*- coding: utf-8 -*-
import flask
from flask import request, jsonify
from data_manager import DataManager
from connexion import DbConnexion
from ortho import Ortho
from datetime import datetime
import random
import os
from dotenv import load_dotenv
from word_utils import correct
from flask_cors import CORS

app = flask.Flask(__name__)
CORS(app)
dm = None
db = None

def current_session_id():
    global db, dm
    current_utc = int(datetime.now().timestamp())
    return dm.get_session_id(db, current_utc)
    

@app.route('/session-id', methods=['GET'])
def session_id():
    session_id = None
    try:
        session_id = current_session_id()
    except Exception as e:
        db.rollback()
        return 'Internal error: could not get session id. %s' % e, 500
    res = {}
    res['session_id'] = session_id
    return jsonify(res), 200
    
    
@app.route('/score', methods=['GET'])
def score():
    global db, dm

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
    #if 'correction' in request.args:
    #    correction = not((request.args['correction']).lower() == "false")

    # Find the baseline
    if session_id is None:
        try:
            session_id = current_session_id()
        except Exception as e:
            db.rollback()
            return 'Internal error: could not get session id. %s' %e, 500
    baseline = None
    try:
        baseline = dm.get_session_infos(db, session_id)['word']
    except Exception as e:
        db.rollback()
        return 'Internal error: baseline not found. %s' %e, 500
        
    # Load the word
    word_corrected = None
    word_object = Ortho()
    try:
        word_object.load_from_word(db, word)
    except: # This means that the word was not found or there was an error

        if correction:
            # So we try to correct it
            try:
                word_corrected = correct(word)
                word_object.load_from_word(db, word_corrected)
                word_corrected = word_object.ortho
            except: # No correction available
                db.rollback()
                try:
                    word_object.load_like_word(db, word)
                    word_corrected = word_object.ortho
                except:
                    db.rollback()
                    try:
                        word_object.load_like_word(db, word_corrected)
                        word_corrected = word_object.ortho
                    except:
                        db.rollback()
                        return jsonify({"user_id": user_id, "session_id": session_id, "word": word, "score": -1}), 404
        else:
            try:
                word_object.load_like_word(db, word)
                word_corrected = word_object.ortho
            except:
                db.rollback()
                return jsonify({"user_id": user_id, "session_id": session_id, "word": word, "score": -1}), 404

    # Everything was fetched properly, let's compute the score
    score = word_object.compute_rectified_score(baseline)
    res = {}
    res['user_id'] = user_id
    res['session_id'] = session_id
    status = 200

    if word_corrected is None:
        res['word'] = word_object.ortho
        res['score'] = score
    else:
        res['word'] = word
        res['score'] = -1
        res['suggested_word'] = word_object.ortho
        res['suggested_score'] = score
        status = 201

    return jsonify(res), status


@app.route('/hint', methods=['GET'])
def hint():
    global db, dm

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

    # Check that the user does not ask for the solution
    if value > 0.9:
        return jsonify({"user_id": user_id, "session_id": session_id, "error": "No clue available after 0.9."}), 201

    # Find the hints
    hints = None
    baseline = None
    try:
        res = dm.get_session_infos(db, session_id)
        baseline = res["word"]
        hints = res['hints']
    except Exception as e:
        db.rollback()
        return 'Internal error: baseline not found. %s' %e, 500

    # Return the closest hint
    for score in hints.keys():
        if 1 > score >= value:
            hint = random.choice(hints[score])
            real_score = hint.compute_rectified_score(baseline)
            return jsonify({"user_id": user_id, "session_id": session_id, "word": hint.ortho, "score": real_score}), 200

    # No hint was found, this is not normal
    return "Internal error: No clue found.", 404



if __name__ == "__main__":
    load_dotenv()
    dm = DataManager()
    db = DbConnexion()
    db.connect()
    app.run(port=os.getenv('API_PORT'))
    db.disconnect()