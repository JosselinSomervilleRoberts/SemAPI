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
import numpy as np

app = flask.Flask(__name__)
CORS(app)
dm = None
db = None



def current_session_id():
    global db, dm
    current_utc = int(datetime.now().timestamp())
    return dm.get_session_id(db, current_utc)

def LogRequest(method, route, params):
    global db
    try:
        user_id = params.get('user_id', 'USER#0000', str)
        db.cursor.execute("INSERT INTO requests(method, route, params, user_id) VALUES(%s, %s, %s, %s)", (method, route, str(params), user_id))
        db.connexion.commit()
    except Exception as e:
        db.rollback()
        print("EXCEPTION", e)

def LogScore(user_id, session_id, ortho_id, score):
    global db
    try:
        db.cursor.execute("INSERT INTO scores(session_id, user_id, ortho_id, score) VALUES(%s, %s, %s, %s)", (session_id, user_id, ortho_id, score))
        db.connexion.commit()
        return True
    except:
        db.rollback()
        return False

def GetNbAttempts(session_id, user_id):
    global db
    db.cursor.execute("SELECT COUNT(*) FROM scores WHERE session_id = %s AND user_id = %s", (session_id, user_id))
    res = db.cursor.fetchone()
    if res is None:
        raise Exception("Could not count number of attempts.")
    return res[0]



@app.route('/session-id', methods=['GET'])
def request_sessions_id():
    res, status = session_id(request.args)
    LogRequest('GET', '/session-id', request.args)
    return res, status

def session_id(_):
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
def request_score():
    res, status = score(request.args)
    LogRequest('GET', '/score', request.args)
    return res, status

def score(args):
    global db, dm
    
    # Get params
    word = args.get('word', default=None, type=str)
    user_id = args.get('user_id', default=None, type=str)
    session_id = args.get('session_id', default=None, type=int)
    correction = args.get('correction', default=True, type=bool)
    if word is None:
        return "Missing parameter: word.", 400

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

        if correction: # So we try to correct it
            try:
                word_corrected = correct(word)
                word_object.load_from_word(db, word_corrected)
                word_corrected = word_object.ortho
                try:
                    db.cursor.execute("INSERT INTO corrections(ortho_id, word) VALUES(%s, %s)", (word_object.id, word))
                    db.connexion.commit()
                except:
                    db.rollback()
            except: # No correction available
                db.rollback()
                try: # We search for a word LIKE it
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
        new = LogScore(user_id, session_id, word_object.id, score)
        res['rew'] = new
        if new and score >= 1:
            nb_attempts = GetNbAttempts(session_id, user_id)
            db.cursor.execute("""INSERT INTO final_scores(session_id, user_id, score, nb_attempts, has_won, utc_date_ms)
                                VALUES(%s, %s, %s, %s, %s, %s)""",
                                (session_id, user_id, score, nb_attempts, True, int(1000.0 * datetime.now().timestamp())))
            db.connexion.commit()
    else:
        res['word'] = word
        res['score'] = -1
        res['suggested_word'] = word_object.ortho
        res['suggested_score'] = score
        status = 201

    return jsonify(res), status



@app.route('/ranking', methods=['GET'])
def request_ranking():
    res, status = ranking(request.args)
    LogRequest('GET', '/ranking', request.args)
    return res, status

def ranking(args):
    global db, dm
    index_start = args.get('index_start', default = None, type = int)
    count = args.get('count', default = None, type = int)
    session_id = args.get('session_id', default = None, type = str)
    user_id = args.get('user_id', default = None, type = str)
    if user_id is None:
        return "Missing parameter: user_id.", 400
    if index_start is None:
        return "Missing parameter: index_start.", 400
    if count is None:
        return "Missing parameter: count.", 400
    if session_id is None:
        return "Missing parameter: session_id.", 400
    
    try:
        db.cursor.execute("""SELECT u.name, u.tag, s.score, s.nb_attempts, s.has_won, s.utc_date_ms
                            FROM final_scores AS s
                            JOIN users AS u
                            ON s.user_id = u.user_id
                            WHERE s.session_id = %s AND s.user_id = %s
                            LIMIT 1""",
                            (session_id, count, index_start))
        res = db.cursor.fetchone()
        
        res = {"name": [], "tag": [], "score": [], "nb_attempts": [], "has_won": []}
        if res is None:
            return "Internal error: No result found", 500
        return {"name": res[0], "tag": res[1], "score": res[2], "nb_attempts": res[3], "has_won": res[4]}, 200
    except Exception as e:
        db.rollback()
        return 'Internal error: %s' %e, 500



@app.route('/ranking/all', methods=['GET'])
def request_ranking_all():
    res, status = ranking_all(request.args)
    LogRequest('GET', '/ranking/all', request.args)
    return res, status

def ranking_all(args):
    global db, dm
    index_start = args.get('index_start', default = None, type = int)
    count = args.get('count', default = None, type = int)
    session_id = args.get('session_id', default = None, type = str)
    if index_start is None:
        return "Missing parameter: index_start.", 400
    if count is None:
        return "Missing parameter: count.", 400
    if session_id is None:
        return "Missing parameter: session_id.", 400
    
    try:
        db.cursor.execute("""SELECT u.name, u.tag, s.score, s.nb_attempts, s.has_won, s.utc_date_ms
                            FROM final_scores AS s
                            JOIN users AS u
                            ON s.user_id = u.user_id
                            WHERE s.session_id = %s
                            ORDER BY s.score DESC, s.nb_attempts DESC, s.utc_date ASC
                            LIMIT %s OFFSET %s""",
                            (session_id, count, index_start))
        res_query = db.cursor.fetchall()
        
        res = {"name": [], "tag": [], "score": [], "nb_attempts": [], "has_won": []}
        for row in res_query:
            res["name"].append(row[0])
            res["tag"].append(row[1])
            res["score"].append(row[2])
            res["nb_attempts"].append(row[3])
            res["has_won"].append(row[4])
        return res, 200
    except Exception as e:
        db.rollback()
        return 'Internal error: %s' %e, 500 




@app.route('/user', methods=['GET'])
def request_get_user():
    res, status = get_user(request.args)
    LogRequest('GET', '/user', request.args)
    return res, status

def get_user(args):
    global db, dm
    user_name = args.get('user_name', default = None, type = str)
    user_tag = args.get('user_tag', default = None, type = int)
    if user_tag is None:
        return "Missing parameter: user_tag.", 400
    if user_name is None:
        return "Missing parameter: user_name.", 400
    try:
        db.cursor.execute("""SELECT user_id FROM users 
                            WHERE name = %s AND tag = %s""",
                            (user_name, user_tag))
        res = db.cursor.fetchone()
        if res is None:
            return "Internal error: user not found.", 500
        return {"user_id": res[0], "user_name": user_name, "user_tag": user_tag}, 200
    except:
        db.rollback()
        return "Internal error: could not get user.", 500



@app.route('/user', methods=['POST'])
def request_create_user():
    res, status = create_user(request.args)
    print(res, status)
    return res, status

def create_user(args):
    global db, dm
    user_name = args.get('user_name', default = None, type = str)
    if user_name is None:
        return "Missing parameter: user_name.", 400
    np.random.seed(ord(user_name[0]))
    try:
        db.cursor.execute("""SELECT COUNT(*) FROM users
                            WHERE name = %s""",
                            (user_name,))
        res = db.cursor.fetchone()
        count = 0
        if res is not None:
            count = int(res[0])
        user_tag = int(np.random.permutation(10000)[count])
        user_id = user_name + "#" + "0" * (4-len(str(user_tag))) + str(user_tag)
        try:
            db.cursor.execute("""INSERT INTO users(user_id, name, tag)
                                VALUES(%s, %s, %s)""",
                                (user_id, user_name, user_tag,))
            db.connexion.commit()
            return {"user_id": user_id}, 200
        except Exception as e:
            db.rollback()
            return "Internal error: could not insert user. %s" % e, 500
    except Exception as e:
        db.rollback()
        return "Internal error: could not create user. %s" % e, 500
    


@app.route('/final-score', methods=['POST'])
def request_final_score():
    res, status = final_score(request.args)
    LogRequest('POST', '/final-score', request.args)
    return res, status

def final_score(args):
    global db, dm
    user_id = args.get('user_id', default = None, type = str)
    session_id = args.get('session_id', default = None, type = str)
    score = args.get('score', default = None, type = float)
    if score is None:
        return "Missing parameter: score.", 400
    if user_id is None:
        return "Missing parameter: user_id.", 400
    if session_id is None:
        return "Missing parameter: session_id.", 400
    nb_attemps = GetNbAttempts(session_id, user_id)
    db.cursor.execute("""INSERT INTO final_scores(session_id, user_id, score, nb_attemps, has_won)
                        VALUES(%s, %s, %s, %s, %s)""",
                        (session_id, user_id, score, nb_attemps, False))
    db.connexion.commit()
    return None, 200



@app.route('/hint/nb-letters', methods=['GET'])
def request_hint_nb_letters():
    res, status = hint_nb_letters(request.args)
    LogRequest('GET', '/hint/nb-letters', request.args)
    return res, status

def hint_nb_letters(args):
    global db, dm
    user_id = args.get('user_id', default = None, type = str)
    session_id = args.get('session_id', default = None, type = str)
    if user_id is None:
        return "Missing parameter: user_id.", 400
    if session_id is None:
        return "Missing parameter: session_id.", 400

    # Find the baseline
    baseline = None
    try:
        res = dm.get_session_infos(db, session_id)
        baseline = res["word"]
    except Exception as e:
        db.rollback()
        return 'Internal error: baseline not found. %s' %e, 500

    return jsonify({"session_id": session_id, "user_id": user_id, "nb_letters": baseline.nb_letters}), 200



@app.route('/hint/nb-syllables', methods=['GET'])
def request_hint_nb_syllables():
    res, status = hint_nb_syllables(request.args)
    LogRequest('GET', '/hint/nb-syllables', request.args)
    return res, status

def hint_nb_syllables(args):
    global db, dm
    user_id = args.get('user_id', default = None, type = str)
    session_id = args.get('session_id', default = None, type = str)
    if user_id is None:
        return "Missing parameter: user_id.", 400
    if session_id is None:
        return "Missing parameter: session_id.", 400

    # Find the baseline
    baseline = None
    try:
        res = dm.get_session_infos(db, session_id)
        baseline = res["word"]
    except Exception as e:
        db.rollback()
        return 'Internal error: baseline not found. %s' %e, 500

    if baseline.nb_syll is None:
        return jsonify({"session_id": session_id, "user_id": user_id}), 404
    else:
        return jsonify({"session_id": session_id, "user_id": user_id, "nb_syllables": baseline.nb_syll}), 200




@app.route('/hint/type', methods=['GET'])
def request_hint_type():
    res, status = hint_type(request.args)
    LogRequest('GET', '/hint/type', request.args)
    return res, status

def hint_type(args):
    global db, dm
    user_id = args.get('user_id', default = None, type = str)
    session_id = args.get('session_id', default = None, type = str)
    if user_id is None:
        return "Missing parameter: user_id.", 400
    if session_id is None:
        return "Missing parameter: session_id.", 400

    # Find the baseline
    baseline = None
    try:
        res = dm.get_session_infos(db, session_id)
        baseline = res["word"]
    except Exception as e:
        db.rollback()
        return 'Internal error: baseline not found. %s' %e, 500

    return jsonify({"session_id": session_id, "user_id": user_id, "type": baseline.lemma.type, "gender": baseline.genre, "number": baseline.number}), 200



@app.route('/hint', methods=['GET'])
def request_hint():
    res, status = hint(request.args)
    LogRequest('GET', '/hint', request.args)
    return res, status

def hint(args):
    global db, dm
    user_id = args.get('user_id', default = None, type = str)
    session_id = args.get('session_id', default = None, type = str)
    value = args.get('value', default = None, type = float)
    if user_id is None:
        return "Missing parameter: user_id.", 400
    if session_id is None:
        return "Missing parameter: session_id.", 400
    if value is None:
        return "Missing parameter: value.", 400

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