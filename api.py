# -*- coding: utf-8 -*-
import flask
from flask import request, jsonify
from data_manager import DataManager
from connexion import DbConnexion
from ortho import Ortho
from datetime import datetime
import os
from dotenv import load_dotenv
from word_utils import correct
from flask_cors import CORS
import numpy as np
from typing import Dict, List, Callable, Tuple
from werkzeug.datastructures import ImmutableMultiDict
from session import Session

app = flask.Flask(__name__)
CORS(app)
dm = None
db = None


def current_utc_ms():
    return int(1000.0 * datetime.now().timestamp())

def current_time_s():
    return int(datetime.now().timestamp()) + 3600 * 2

def current_session_id():
    global db, dm
    current_t = current_time_s()
    return dm.get_session_id(db, current_t)
    
def yesterday_session_id():
    global db, dm
    yesterday_t = current_time_s() - 3600*24
    return dm.get_session_id(db, yesterday_t)

def LogRequest(user_id, method, route, params, status, user_needed = True):
    global db
    if user_id is None and user_needed:
        raise Exception("User ID not provided in request.", 400)
    try:
        str_params = ",".join([key + "=" + str(params[key]) for key in params])
        db.cursor.execute("""INSERT INTO requests(method, route, params, user_id, status, utc_date_ms) 
                            VALUES(%s, %s, %s, %s, %s, %s)""", 
                            (method, route, str_params, user_id, status, current_utc_ms()))
        db.connexion.commit()
    except Exception as e:
        db.rollback()
        raise Exception("User ID not valid: %s. Error: %s" % (user_id,e), 400)

def LogScore(user_id, session_id, ortho_id, score):
    global db
    try:
        db.cursor.execute("""INSERT INTO scores(session_id, user_id, ortho_id, score) 
                            VALUES(%s, %s, %s, %s)""", 
                            (session_id, user_id, ortho_id, score))
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

def GetIsActiveOrSetIt(session_id, user_id):
    global db
    db.cursor.execute("SELECT active FROM activity WHERE session_id = %s AND user_id = %s", (session_id, user_id))
    res = db.cursor.fetchone()
    if res is None:
        try:
            db.cursor.execute("""INSERT INTO activity(session_id, user_id, utc_start_ms, active)
                                VALUES(%s, %s, %s, %s)""",
                                (session_id, user_id, current_utc_ms(), True))
        except:
            db.rollback()
            return False
        return True
    return bool(res[0])


def GetIsStillActive(session_id, user_id):
    global db
    db.cursor.execute("SELECT active FROM activity WHERE session_id = %s AND user_id = %s", (session_id, user_id))
    res = db.cursor.fetchone()
    if res is None:
        return False
    return bool(res[0])


def GetHasPlayedButHasNotWon(session_id, user_id):
    global db
    db.cursor.execute("SELECT active FROM activity WHERE session_id = %s AND user_id = %s", (session_id, user_id))
    res = db.cursor.fetchone()
    if res is None:
        return False
    db.cursor.execute("SELECT has_won FROM final_scores WHERE session_id = %s AND user_id = %s", (session_id, user_id))
    res = db.cursor.fetchone()
    if res is None:
        return False
    return not bool(res[0])

def GetHasPlayedAndHasWon(session_id, user_id):
    global db
    db.cursor.execute("SELECT active FROM activity WHERE session_id = %s AND user_id = %s", (session_id, user_id))
    res = db.cursor.fetchone()
    if res is None:
        return False
    db.cursor.execute("SELECT has_won FROM final_scores WHERE session_id = %s AND user_id = %s", (session_id, user_id))
    res = db.cursor.fetchone()
    if res is None:
        return False
    return bool(res[0])


def GetUserIdFromUser(user: str) -> int:
    user_split = user.split("#")
    user_name, user_tag = None, None
    try:
        user_name = str(user_split[0])
        user_tag = int(user_split[1])
    except Exception as e:
        raise Exception("user not valid: %s. ERROR: %s" % (user, e), 400)
    db.cursor.execute("""SELECT user_id FROM public.users 
                        WHERE name = %s AND tag = %s LIMIT 1""",
                        (user_name, user_tag))
    res = db.cursor.fetchone()
    if res is None:
        raise Exception("user not found in db: %s" % user, 400)
    return int(res[0])


def PreProcessArgs(args: ImmutableMultiDict, session_required: bool = False, required: List[str ]= None) -> Dict:
    global db, dm
    processed_args = {}

    user = args.get('user', default=None, type=str)
    if user is None:
        raise Exception("Missing parameter: user.", 400)
    user_id = GetUserIdFromUser(user)
    processed_args['user_id'] = user_id

    if 'session_id' in args:
        session_id = args.get('session_id', default=None, type=int)
        if session_required and session_id is None:
            raise Exception("Missing parameter: session_id.", 400)
        if session_id is not None:
            session = dm.get_session(db, session_id)
            processed_args['session'] = session

    if required is not None:
        for arg in required:
            value = args.get(arg, default=None, type=str)
        if value is None:
            raise Exception("Missing parameter: %s." % arg, 400)

    for arg in args:
        if arg not in processed_args:
            processed_args[arg] = args[arg]

    return processed_args


def ExecuteRequest(function: Callable, request_method: str,
                    request_route: str, request_args: ImmutableMultiDict, 
                    session_required: bool = False, required: List[str ]= None) -> Tuple[Dict, int]:
    args = None
    try:
        args = PreProcessArgs(request_args, session_required, required)
    except Exception as error:
         return error.args[0], error.args[1]
    
    res, status = function(args)
    print(res, status)
    try:
        LogRequest(args['user_id'], request_method, request_route, request_args, status)
    except Exception as error:
        print(error)
        return error.args[0], error.args[1]
    return res, status

def GetUserFromNameAndTag(user_name: str, user_tag: int) -> str:
    return user_name + "#" + "0" * (4 - len(str(user_tag))) + str(user_tag)

def GetBestScore(session: Session, user_id: int) -> float:
    db.cursor.execute("""SELECT score FROM public.scores
                        WHERE session_id = %s AND user_id = %s""",
                        (session.id, user_id))
    res = db.cursor.fetchone()
    if res is None:
        return 0
    return float(res[0])

def SaveUsedHint(session: Session, user_id: int, hint_type: int, cost: int, value: str):
    try:
        db.cursor.execute("""INSERT INTO public.used_hints(session_id, user_id, hint_type, cost, result)
                          VALUES(%s, %s, %s, %s, %s)""",
                            (session.id, user_id, hint_type, cost, value))
        db.connexion.commit()
    except:
        db.rollback()

def GetHints(session: Session, user_id: int) -> Dict:
    best_score = GetBestScore(session, user_id)
    nb_attempts = GetNbAttempts(session.id, user_id)
    db.cursor.execute("""SELECT hint_type, cost, result
                            FROM public.used_hints
                            WHERE session_id = %s AND user_id = %s
                            ORDER BY hint_id ASC""",
                            (session.id, user_id))
    res = db.cursor.fetchall()
    used_hints = {}
    for row in res:
        used_hints[int(row[0])] = [int(row[1]), str(row[2])]

    hints = []
    for hint_type in [0,1,2,3,80,90]:
        already_used = (hint_type in used_hints)
        obj = {}
        obj["status"] = "unavailable"
        obj["params"] = {}
        if already_used:
            obj["status"] = "used"
            obj["cost"] = int(used_hints[hint_type][0])
            obj["value"] = str(used_hints[hint_type][1])

        if hint_type == 0: # nb letters
            obj['libelle'] = "Nombre de lettres"
            obj['code'] = "/hint/nb-letters"
            if not already_used and nb_attempts > 10:
                obj["status"] = "available"
                obj["cost"] = 5
        elif hint_type == 1: # nb sylabble
            obj['libelle'] = "Nombre de syllabes"
            obj['code'] = "/hint/nb-syllables"
            if not already_used and nb_attempts > 20 and session.word.nb_syll is not None:
                obj["status"] = "available"
                obj["cost"] = 5
        elif hint_type == 2: # type
            obj['libelle'] = "Nature"
            obj['code'] = "/hint/type"
            if not already_used and nb_attempts > 20:
                obj["status"] = "available"
                obj["cost"] = 8
        elif hint_type == 3: # first letter
            obj['libelle'] = "Première lettre"
            obj['code'] = "/hint/first-letter"
            if not already_used and nb_attempts > 30:
                obj["status"] = "available"
                obj["cost"] = 10
        elif hint_type == 80:
            obj['libelle'] = "Mot à %d" % hint_type
            obj['code'] = "/hint"
            obj["params"]["value"] = 0.8
            if not already_used and nb_attempts > 40 and best_score < 0.65:
                obj["status"] = "available"
                obj["cost"] = 20
        elif hint_type == 90:
            obj['libelle'] = "Mot à %d" % hint_type
            obj['code'] = "/hint"
            obj["params"]["value"] = 0.9
            if not already_used and nb_attempts > 70 and best_score < 0.75:
                obj["status"] = "available"
                obj["cost"] = 30
        hints.append(obj)

    return hints

def GetAdditionalCost(session: Session, user_id: int) -> int:
    db.cursor.execute("""SELECT hint_type, cost
                            FROM public.used_hints
                            WHERE session_id = %s AND user_id = %s
                            ORDER BY hint_id ASC""",
                            (session.id, user_id))
    res = db.cursor.fetchall()
    total_cost = 0
    for row in res:
        cost = int(row[1])
        if int(row[0]) > 20:
            cost -= 1
        total_cost += cost
    return total_cost

def GetPlayerScore(session: Session, user_id: int) -> int:
    return GetNbAttempts(session.id, user_id) + GetAdditionalCost(session, user_id)




@app.route('/session-id', methods=['GET'])
def request_sessions_id():
    return ExecuteRequest(session_id, 'GET', '/session-id', request.args, False, None)

def session_id(args):
    user_id = args['user_id']
    session_id = None
    try:
        session_id = current_session_id()
    except Exception as e:
        db.rollback()
        return 'Internal error: could not get session id. %s' % e, 500
    res_request = {}
    res_request['session_id'] = session_id
    yesterday_id = yesterday_session_id()
    if yesterday_id is not None:
        if GetIsStillActive(yesterday_id, user_id):
            res_request["can_continue"] = yesterday_id
        elif GetHasPlayedButHasNotWon(yesterday_id, user_id):
            try:
                db.cursor.execute("""SELECT o.ortho FROM orthos AS o
                                    JOIN fr_sessions AS s
                                    ON s.ortho_id = o.ortho_id
                                    WHERE s.session_id = %s""", (yesterday_id,))
                res = db.cursor.fetchone()
                if res is not None:
                    res_request["yesterday"] = res[0]
            except:
                return "Internal error: could not get yesterday's word.", 500
    return jsonify(res_request), 200



@app.route('/score', methods=['GET'])
def request_score():
    return ExecuteRequest(score, 'GET', '/score', request.args, True, ['word'])

def score(args):
    global db, dm
    
    # Get params
    word = args['word']
    user_id = args['user_id']
    session = args['session']
    correction = True # TODO(change)

    try:
        if not GetIsActiveOrSetIt(session.id, user_id):
            return "Game not active for session_id: %d, user_id: %s." % (session.id, user_id), 400
    except Exception as e:
        return "Interal Error: %s" %e, 500
        
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
                        return jsonify({"user": args['user'], "session_id": session.id, "word": word, "score": -1}), 404
        else:
            try:
                word_object.load_like_word(db, word)
                word_corrected = word_object.ortho
            except:
                db.rollback()
                return jsonify({"user": args['user'], "session_id": session.id, "word": word, "score": -1}), 404

    # Everything was fetched properly, let's compute the score
    score = session.GetScoreFromLemma(word_object.lemma)
    res = {}
    res['user'] = args['user']
    res['session_id'] = session.id
    status = 200

    if word_corrected is None:
        res['word'] = word_object.ortho
        res['score'] = score.value
        res['score_text'] = score.text
        new = LogScore(user_id, session.id, word_object.id, score.value)
        nb_attempts = GetNbAttempts(session.id, user_id)
        res['new'] = new
        res["attempt"] = nb_attempts
        player_score = GetPlayerScore(session, user_id)
        res["player_score"] = player_score
        if new and score.value >= 1:
            db.cursor.execute("""INSERT INTO final_scores(session_id, user_id, score, nb_attempts, has_won, utc_date_ms)
                                VALUES(%s, %s, %s, %s, %s, %s)""",
                                (session.id, user_id, player_score, nb_attempts, True, current_utc_ms()))
            db.cursor.execute("""UPDATE activity
                                SET active = %s, utc_end_ms = %s
                                WHERE session_id = %s AND user_id = %s""",
                                (False, current_utc_ms(), session.id, user_id))
            db.connexion.commit()
    else:
        res['word'] = word
        res['score'] = -1
        res['suggested_word'] = word_object.ortho
        res['suggested_score'] = score.value
        res['suggested_score_text'] = score.text
        res["player_score"] = GetPlayerScore(session, user_id)
        status = 201

    return jsonify(res), status



@app.route('/ranking', methods=['GET'])
def request_ranking():
    return ExecuteRequest(ranking, 'GET', '/ranking', request.args, True)

def ranking(args):
    global db, dm
    session = args['session']
    user_id = args['user_id']

    try:
        if GetIsActiveOrSetIt(session.id, user_id):
            return "Game is still active for session_id: %d, user_id: %s." % (session.id, user_id), 400
    except Exception as e:
        return "Interal Error: %s" %e, 500
    
    try:
        db.cursor.execute("""SELECT u.name, u.tag, s.score, s.nb_attempts, s.has_won, s.utc_date_ms
                            FROM final_scores AS s
                            JOIN users AS u
                            ON s.user_id = u.user_id
                            WHERE s.session_id = %s AND s.user_id = %s
                            LIMIT 1""",
                            (session.id, user_id))
        res_query = db.cursor.fetchone()
        
        if res_query is None:
            return "Internal error: No result found", 500
        user_name = str(res_query[0])
        user_tag = int(res_query[1])
        user = GetUserFromNameAndTag(user_name, user_tag)
        return {"user": user, "score": res_query[2], "nb_attempts": res_query[3], "has_won": res_query[4], "utc": int(res_query[5])}, 200
    except Exception as e:
        db.rollback()
        return 'Internal error: %s' %e, 500



@app.route('/ranking/all', methods=['GET'])
def request_ranking_all():
    return ExecuteRequest(ranking_all, 'GET', '/ranking/all', request.args, True, ['index_start', 'count'])


def ranking_all(args):
    global db, dm
    session = args['session']
    index_start = int(args['index_start'])
    count = int(args['count'])
    
    try:
        db.cursor.execute("""SELECT u.name, u.tag, s.score, s.nb_attempts, s.has_won, s.utc_date_ms
                            FROM final_scores AS s
                            JOIN users AS u
                            ON s.user_id = u.user_id
                            WHERE s.session_id = %s
                            ORDER BY s.score DESC, s.nb_attempts DESC, s.utc_date_ms ASC
                            LIMIT %s OFFSET %s""",
                            (session.id, count, index_start))
        res_query = db.cursor.fetchall()
        
        res = []
        for row in res_query:
            obj = {}
            user_name = str(row[0])
            user_tag = int(row[1])
            user = GetUserFromNameAndTag(user_name, user_tag)
            obj["user"] = user
            obj["score"] = float(row[2])
            obj["player_score"] = int(row[3])
            obj["has_won"] = row[4]
            obj["utc"] = int(row[5])
            res.append(obj)

        n = len(res_query)
        if n < count:
            try:
                db.cursor.execute("""SELECT u.name, u.tag, MAX(s.score) AS maxx, COUNT(s.score)
                            FROM scores AS s
                            JOIN users AS u
                            ON s.user_id = u.user_id
                            WHERE s.session_id = %s
                            GROUP BY u.name, u.tag
                            ORDER BY maxx DESC, COUNT(*) ASC
                            LIMIT %s OFFSET %s""",
                            (session.id, count-n, index_start+n))
                res_query = db.cursor.fetchall()
                for row in res_query:
                    obj = {}
                    user_name = str(row[0])
                    user_tag = int(row[1])
                    user = GetUserFromNameAndTag(user_name, user_tag)
                    obj["user"] = user
                    obj["score"] = float(row[2])
                    obj["nb_attempts"] = int(row[3])
                    obj["has_won"] = False
                    res.append(obj)
            except Exception as e:
                db.rollback()
                return 'Internal error 1: %s' %e, 500 

        return jsonify(res), 200
    except Exception as e:
        db.rollback()
        return 'Internal error 2: %s' %e, 500 




@app.route('/user', methods=['POST'])
def request_create_user():
    res, status = create_user(request.args)
    #try:
    #    LogRequest('POST', '/user', request.args, status, False)
    #except Exception as e:
    #    return e.args[0], e.args[1]
    return res, status

def create_user(args: ImmutableMultiDict):
    global db, dm
    user_name = args.get('user_name', default = None, type = str)
    if user_name is None:
        return "Missing parameter: user_name.", 400
    seed = 0
    for index, letter in enumerate(user_name):
        seed += ord(letter) * (10**index)
    np.random.seed(seed)
    try:
        db.cursor.execute("""SELECT COUNT(*) FROM users
                            WHERE name = %s""",
                            (user_name,))
        res = db.cursor.fetchone()
        count = 0
        if res is not None:
            count = int(res[0])
        user_tag = int(np.random.permutation(10000)[count])
        try:
            db.cursor.execute("""INSERT INTO users(name, tag)
                                VALUES(%s, %s)
                                RETURNING user_id""",
                                (user_name, user_tag,))
            db.connexion.commit()
            res = db.cursor.fetchone()
            if res is None:
                return "Internal Error: Could not insert user", 500
            return {"user": GetUserFromNameAndTag(user_name, user_tag)}, 200
        except Exception as e:
            db.rollback()
            return "Internal error: could not insert user. %s" % e, 500
    except Exception as e:
        db.rollback()
        return "Internal error: could not create user. %s" % e, 500
    


@app.route('/user/session-infos', methods=['GET'])
def request_user_session_infos():
    return ExecuteRequest(user_session_infos, 'GET', '/user/session-infos', request.args, True)

def user_session_infos(args):
    global db, dm
    user_id = args['user_id']
    session = args['session']
    try:
        db.cursor.execute("""SELECT o.ortho, s.score
                            FROM scores AS s
                            JOIN fr_orthos AS o
                            ON o.ortho_id = s.ortho_id
                            WHERE session_id = %s AND user_id = %s
                            ORDER BY score_id ASC""",
                            (session.id, user_id))
        res = db.cursor.fetchall()
        res_request = {"guesses": []}
        for index, row in enumerate(res):
            obj = {}
            obj["attempt"] = int(index +1)
            obj["word"] = str(row[0])
            obj["score"] = float(row[1])
            res_request['guesses'].append(obj)

        db.cursor.execute("""SELECT hint_type, cost, result
                            FROM public.used_hints
                            WHERE session_id = %s AND user_id = %s
                            ORDER BY hint_id ASC""",
                            (session.id, user_id))
        res = db.cursor.fetchall()
        res_request['hints'] = GetHints(session, user_id)
        res_request['player_score'] = GetPlayerScore(session, user_id)
        res_request["active"] = GetIsStillActive(session.id, user_id)
        res_request['has_won'] = GetHasPlayedAndHasWon(session.id, user_id)
        return jsonify(res_request), 200
    except Exception as e:
        db.rollback()
        return "Internal Error: Could not get user session infos. Error: %s" %e, 500


@app.route('/final-score', methods=['POST'])
def request_final_score():
    return ExecuteRequest(final_score, 'POST', '/final-score', request.args, True)

def final_score(args):
    global db, dm
    user_id = args['user_id']
    session = args['session']

    try:
        if not GetIsActiveOrSetIt(session.id, user_id):
            return "Game not active for session_id: %d, user_id: %s." % (session.id, user_id), 400
    except Exception as e:
        return "Interal Error: %s" %e, 500

    db.cursor.execute("SELECT MAX(score) FROM scores WHERE session_id = %s AND user_id = %s", (session.id, user_id))
    res = db.cursor.fetchone()
    if res is None:
        return "Cannot quit without playing once.", 400
    score = float(res[0])

    player_score = GetPlayerScore(session, user_id)
    try:
        db.cursor.execute("""INSERT INTO final_scores(session_id, user_id, score, nb_attempts, has_won, utc_date_ms)
                            VALUES(%s, %s, %s, %s, %s, %s)""",
                            (session.id, user_id, score, player_score, False, current_utc_ms()))
        db.cursor.execute("""UPDATE activity
                                SET active = %s, utc_end_ms = %s
                                WHERE session_id = %s AND user_id = %s""",
                                (False, current_utc_ms(), session.id, user_id))
        db.connexion.commit()
        return "", 200
    except Exception as e:
        db.rollback()
        return "Internal Error: Could not insert final score. Error: %s" %e, 500


@app.route('/hint/available', methods=['GET'])
def request_hint_available():
    return ExecuteRequest(hint_available, 'GET', '/hint/available', request.args, True)

def hint_available(args):
    global db, dm
    user_id = args['user_id']
    session = args['session']
    hints = GetHints(session, user_id)
    return jsonify(hints), 200



@app.route('/hint/nb-letters', methods=['GET'])
def request_hint_nb_letters():
    return ExecuteRequest(hint_nb_letters, 'GET', '/hint/nb-letters', request.args, True)

def hint_nb_letters(args):
    global db, dm
    user_id = args['user_id']
    session = args['session']
    value = str(session.word.nb_letters) + " lettres"
    SaveUsedHint(session, user_id, 0, 5, value)
    return jsonify({"session_id": session.id, "user": args['user'], "value": value, "player_score": GetPlayerScore(session, user_id)}), 200



@app.route('/hint/nb-syllables', methods=['GET'])
def request_hint_nb_syllables():
    return ExecuteRequest(hint_nb_syllables, 'GET', '/hint/nb-syllables', request.args, True)

def hint_nb_syllables(args):
    global db, dm
    user_id = args['user_id']
    session = args['session']
    if session.word.nb_syll is None:
        return jsonify({"session_id": session.id, "user": args['user']}), 404
    else:
        value = str(session.word.nb_syll) + " syllabe"
        if session.word.nb_syll > 1:
            value += "s"
        SaveUsedHint(session, user_id, 1, 5, value)
        return jsonify({"session_id": session.id, "user": args['user'], "value": value, "player_score": GetPlayerScore(session, user_id)}), 200



@app.route('/hint/type', methods=['GET'])
def request_hint_type():
    return ExecuteRequest(hint_type, 'GET', '/hint/type', request.args, True)

def hint_type(args):
    global db, dm
    user_id = args['user_id']
    session = args['session']
    value = session.word.lemma.type
    SaveUsedHint(session, user_id, 2, 8, value)
    return jsonify({"session_id": session.id, "user": args['user'], "value": value, "player_score": GetPlayerScore(session, user_id)}), 200



@app.route('/hint/first-letter', methods=['GET'])
def request_hint_first_letter():
    return ExecuteRequest(hint_first_letter, 'GET', '/hint/first-letter', request.args, True)

def hint_first_letter(args):
    global db, dm
    user_id = args['user_id']
    session = args['session']
    value = str(session.word.ortho[0]).upper()
    SaveUsedHint(session, user_id, 3, 10, value)
    return jsonify({"session_id": session.id, "user": args['user'], "value": value, "player_score": GetPlayerScore(session, user_id)}), 200



@app.route('/hint', methods=['GET'])
def request_hint():
    return ExecuteRequest(hint, 'GET', '/hint', request.args, True, ['value'])

def hint(args):
    global db, dm
    user_id = args['user_id']
    session = args['session']
    value = float(args['value'])

    # Check that the user does not ask for the solution
    if value > 0.95:
        return jsonify({"user": args['user'], "session_id": session.id, "error": "No clue available after 0.95."}), 201

    # Return the closest hint
    try:
        ortho_hint = session.GetHint(value)
        score = session.GetScoreFromLemma(ortho_hint.lemma)
        res = {}
        res['user'] = args['user']
        res['session_id'] = session.id
        res['word'] = ortho_hint.ortho
        res['score'] = score.value
        res['score_text'] = score.text
        new = LogScore(user_id, session.id, ortho_hint.id, score.value)
        nb_attempts = GetNbAttempts(session.id, user_id)
        res['new'] = new
        res["attempt"] = nb_attempts
        val = res['word'] + ' (' + str(int(100 * score.value)) + '%)'
        res["value"] = val
        res["player_score"] = GetPlayerScore(session, user_id)
        SaveUsedHint(session, user_id, int(100*value), int(100*value) - 60, val)
        return jsonify(res), 200
    except Exception as error:
        # No hint was found, this is not normal
        return "Internal error: No clue found. ERROR: %s" % error, 404



if __name__ == "__main__":
    load_dotenv()
    dm = DataManager()
    db = DbConnexion()
    db.connect()
    app.run(port=os.getenv('API_PORT'))
    db.disconnect()