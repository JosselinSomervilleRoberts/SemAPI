import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_PATH, '../'))

from db.connexion import DbConnexion
from game.ortho import Ortho
from game.lemma import Lemma
from game.score import Score
from game.hint import Hint, HintFirstLetter, HintNbLetters, HintNbSylabbles, HintType, HintWord
from tqdm import tqdm
from typing import List, Dict
from utils.time_utils import start_current_utc_s
import random


class Rectification:

    def __init__(self, lemma_rectified_: Lemma, old_score_:float, new_score_: int, similarity_min_: float):
        self.lemma_rectified = lemma_rectified_
        self.new_score = new_score_
        self.old_score = old_score_
        self.similarity_min = similarity_min_
        self.affected_lemmas = {}
        print("Rectify %s: %f -> %f (r = %f)" % (self.lemma_rectified, self.old_score, self.new_score, self.similarity_min))

    def LoadRectification(self, session) -> List[int]:
        return self.LoadClosestLemmas(session.db)

    def LoadClosestLemmas(self, db: DbConnexion) -> List[int]:
        db.cursor.execute("""SELECT lemma_id2, similarity FROM public.fr_closest_lemmas
                                    WHERE lemma_id1 = %s AND similarity > %s
                                    ORDER BY rank ASC""",
                                    (self.lemma_rectified.id, self.similarity_min))
        self.affected_lemmas = {}
        res = db.cursor.fetchall()
        lemmas = []
        for row in res:
            lemma_id = int(row[0])
            similarity = float(row[1])
            self.affected_lemmas[lemma_id] = (similarity - self.similarity_min) / (1. - self.similarity_min)
            lemmas.append(lemma_id)
        return lemmas


class Session:

    def __init__(self, db_: DbConnexion):
        self.id = None
        self.word = None
        self.rectifications = []
        self.closest_lemmas = {}
        self.cached_score = {}
        self.rectifications = []
        self.ranks = {}
        self.old_ranks = {}
        self.db = db_
        self.hints = []

    def ComputeAndInsertAllScores(self, lemmas: List[Lemma] = None) -> None:
        if lemmas is None:
            lemmas = Lemma.load_all(self.db)

        self.ranks = {}
        for lemma_id in self.closest_lemmas.keys():
            self.ranks[lemma_id] = self.closest_lemmas[lemma_id]

        for lemma in tqdm(lemmas):
            (similarity, score_value) = Score.ComputeSimpleValueAndSimilarityFromSession(lemma, self)
            self.CacheScoreValue(lemma, score_value)
            self.db.cursor.execute("""INSERT INTO public.fr_scores_computed(session_id, lemma_id, similarity, score)
                                    VALUES(%s, %s, %s, %s)""",
                                    (self.id, lemma.id, similarity, score_value))
            self.db.connexion.commit()


    def LoadClosestLemmas(self):
        self.db.cursor.execute("""SELECT lemma_id2, similarity FROM public.fr_closest_lemmas
                                    WHERE lemma_id1 = %s
                                    ORDER BY rank ASC""",
                                    (self.word.lemma.id,))
        self.closest_lemmas = {}
        res = self.db.cursor.fetchall()
        for rank, row in enumerate(res):
            lemma_id = int(row[0])
            self.closest_lemmas[lemma_id] = rank
        self.similarity_first_closest_lemmas = float(res[1][1])
        self.similarity_last_closest_lemmas = float(res[-1][1])

    
    def ComputeRanks(self):
        self.db.cursor.execute("""SELECT l.lemma_id, score, similarity, lemma
                                FROM public.fr_scores_computed AS s 
                                JOIN public.fr_lemmas AS l 
                                ON s.lemma_id = l.lemma_id 
                                WHERE s.session_id = %s 
                                ORDER BY score DESC LIMIT %s""",
                                (self.id, Score.RANK_THRESHOLD_MAX + 1))
        res = self.db.cursor.fetchall()
        self.ranks = {}
        for rank, row in enumerate(res):
            lemma_id = int(row[0])
            self.ranks[lemma_id] = rank

    def GetRank(self, lemma: Lemma) -> int:
        if lemma.id in self.ranks:
            return self.ranks[lemma.id]
        return Score.RANK_THRESHOLD_MAX + 1

    def LoadHints(self):
        self.hints = [
            HintNbLetters(len(self.word.ortho)),
            HintFirstLetter(self.word.ortho[0]),
            HintType(self.word.lemma.type),
            HintWord(0.8),
            HintWord(0.9),
        ]
        if self.word.nb_syll is not None:
            self.hints.append(HintNbSylabbles(self.word.nb_syll))

    def CreateSession(self, word_: Ortho, lemmas: List[Lemma] = None) -> None:
        self.id = None
        self.word = word_
        self.rectifications = []
        self.closest_lemmas = {}
        self.cached_score = {}
        self.ranks = {}
        self.rectifications = []

        # Create a new session
        try:
            self.db.cursor.execute("""INSERT INTO public.fr_sessions (ortho_id) 
                                        VALUES(%s)""", 
                                        (word_.id,))       
            self.db.connexion.commit()
        except Exception as e:
            raise Exception("Could not insert new session.", e)  

        self.db.cursor.execute("""SELECT session_id 
                                    FROM public.fr_sessions 
                                    WHERE ortho_id = %s""", 
                                    (word_.id, ))
        session_id = None
        res = self.db.cursor.fetchone()
        if res is None:
            raise Exception("Session id not found.")
        session_id = int(res[0])
        self.id = session_id

        # Find the closest_lemmas
        self.LoadClosestLemmas()

        # Compute and insert all score
        self.ComputeAndInsertAllScores(lemmas)

        # Compute ranks
        self.ComputeRanks()

        # Load hints
        self.LoadHints()



    def LoadFromSessionId(self, session_id_: int) -> None:
        self.id = session_id_

        # Find the word
        self.db.cursor.execute("SELECT ortho_id FROM public.fr_sessions WHERE session_id = %d" % self.id)
        res = self.db.cursor.fetchone()
        if res is None:
            raise Exception("Cannot load session with id: %d, because the session was not found." % self.id, 400)
        baseline_id = int(res[0])
        self.word = Ortho()
        self.word.load_from_id(self.db, baseline_id)

        # Find the closest_lemmas
        self.LoadClosestLemmas()

        # Load rectifications
        self.db.cursor.execute("""SELECT lemma_id, old_score, new_score, similarity_min FROM public.fr_rectifications
                            WHERE session_id = %s
                            ORDER BY rectification_id ASC""",
                            (self.id,))
        res = self.db.cursor.fetchall()
        for row in res:
            lemma_rectified_id = int(row[0])
            lemma_rectified = Lemma()
            lemma_rectified.load_from_id(self.db, lemma_rectified_id)
            old_score = float(row[1])
            new_score = float(row[2])
            similarity_min = float(row[3])
            rectification = Rectification(lemma_rectified, old_score, new_score, similarity_min)
            rectification.LoadRectification(self)
            self.rectifications.append(rectification)

        # Compute ranks
        self.ComputeRanks()

        # Load hints
        self.LoadHints()


    def CacheScore(self, lemma: Lemma, score: Score) -> None:
        self.cached_score[lemma.id] = score

    def CacheScoreValue(self, lemma: Lemma, score_value: float) -> None:
        rank = self.GetRank(lemma)
        score = Score.GetFromValueAndRank(score_value, rank)
        self.CacheScore(lemma, score)


    def SearchScoreFromLemma(self, lemma: Lemma) -> Score:
        try:
            self.db.cursor.execute("""SELECT score FROM public.fr_scores_computed
                                WHERE session_id = %s AND lemma_id = %s""",
                                (self.id, lemma.id))
            res = self.db.cursor.fetchone()
            score = -1
            rank = self.GetRank(lemma)
            if res is not None:
                score = float(res[0])
            return Score.GetFromValueAndRank(score, rank)
        except Exception as e:
            return Score(-1, "Erreur: " + str(e))


    def GetScoreFromLemma(self, lemma: Lemma) -> Score:
        if lemma.id in self.cached_score:
            return self.cached_score[lemma.id]
        score = self.SearchScoreFromLemma(lemma)
        self.cached_score[lemma.id] = score
        return score


    def AddRectification(self, lemma_rectified: Lemma, new_score: float, similarity_min = 0.35) -> None:
        old_score = Score.ComputeRectifiedValueFromSession(lemma_rectified, self)
        rectification = Rectification(lemma_rectified, old_score, new_score, similarity_min)
        lemmas_id_to_update = rectification.LoadRectification(self)
        self.rectifications.append(rectification)
        self.old_ranks = self.ranks.copy()

        lemmas_to_update = []
        new_scores = []
        for lemma_id in lemmas_id_to_update:
            lemma = Lemma()
            lemma.load_from_id(self.db, lemma_id)
            new_score_value = Score.ComputeRectifiedValueFromSession(lemma, self)
            lemmas_to_update.append(lemma)
            new_scores.append(new_score_value)
            self.db.cursor.execute("""UPDATE public.fr_scores_computed
                                        SET score = %s
                                        WHERE session_id = %s AND lemma_id = %s""",
                                        (new_score_value, self.id, lemma_id))
            self.db.connexion.commit()

        # Compute ranks
        self.ComputeRanks()

        for i in range(len(lemmas_to_update)):
            lemma = lemmas_to_update[i]
            new_score_value = new_scores[i]
            self.CacheScoreValue(lemma, new_score_value)
            print(lemma, new_score_value)

    def RemoveLastRectification(self):
        rectification = self.rectifications.pop()
        self.ranks = self.old_ranks.copy()

        for lemma_id in rectification.affected_lemmas:
            lemma = Lemma()
            lemma.load_from_id(self.db, lemma_id)
            new_score_value = Score.ComputeRectifiedValueFromSession(lemma, self)
            print(lemma, new_score_value)
            self.CacheScoreValue(lemma, new_score_value)
            self.db.cursor.execute("""UPDATE public.fr_scores_computed
                                        SET score = %s
                                        WHERE session_id = %s AND lemma_id = %s""",
                                        (new_score_value, self.id, lemma_id))
            self.db.connexion.commit()

        # Compute ranks
        self.ComputeRanks()

    def SaveRectifications(self):
        for rectification in self.rectifications:
            self.db.cursor.execute("""INSERT INTO public.fr_rectifications(session_id, lemma_id, old_score, new_score, similarity_min)
                                        VALUES(%s, %s, %s, %s, %s)""",
                                        (self.id, rectification.lemma_rectified.id, rectification.old_score, rectification.new_score, rectification.similarity_min))
            self.db.connexion.commit()

    def RemoveFromDb(self):
        self.db.cursor.execute("""DELETE FROM public.fr_sessions WHERE session_id = %s""",
                                (self.id,))
        self.db.connexion.commit()

    def FindNextAvailableUtcStart(self) -> int:
        start_utc = start_current_utc_s() - 3600 * 24
        utc_used = True
        while utc_used:
            utc_used = False
            self.db.cursor.execute("SELECT * FROM public.fr_sessions WHERE utc_start = %s", (start_utc,))
            if self.db.cursor.fetchone() is not None:
                utc_used = True
                start_utc += 3600 * 24
        return start_utc


    def SaveToDb(self, start_utc = None):
        self.SaveRectifications()
        if start_utc is None:
            start_utc = self.FindNextAvailableUtcStart(self)
        self.db.cursor.execute("UPDATE public.fr_sessions SET utc_start = %s, utc_stop = %s WHERE session_id = %s",
                            (start_utc, start_utc + 3600 * 24, self.id))
        self.db.connexion.commit()


    def GetBestLemmas(self, n):
        self.db.cursor.execute("""SELECT l.lemma_id, score, similarity, lemma
                                FROM public.fr_scores_computed AS s 
                                JOIN public.fr_lemmas AS l 
                                ON s.lemma_id = l.lemma_id 
                                WHERE s.session_id = %s 
                                ORDER BY score DESC LIMIT %s""",
                                (self.id, n))
        res = self.db.cursor.fetchall()
        lemmas = []
        for row in res:
            lemma_id = int(row[0])
            lemma = Lemma()
            lemma.load_from_id(self.db, lemma_id)
            lemmas.append(lemma)
        return lemmas


    def GetHint(self, score_min: float) -> Ortho:
        self.db.cursor.execute("""SELECT l.lemma_id, score, similarity, lemma
                                FROM public.fr_scores_computed AS s 
                                JOIN public.fr_lemmas AS l 
                                ON s.lemma_id = l.lemma_id 
                                WHERE s.session_id = %s
                                AND score >= %s
                                AND LEFT(l.type,3) != %s
                                AND LEFT(l.type,3) != %s AND LEFT(l.type,3) != %s
                                AND NOT(l.lemma_na LIKE '%' + %s + '%')
                                AND LENGTH(l.lemma_na) > 3
                                ORDER BY score ASC LIMIT %s""",
                                (self.id, score_min, "PRE", "PRO", "ART", self.word.ortho_na, 10))
        res = self.db.cursor.fetchall()
        if len(res) == 0:
            raise Exception("No clue found.")
        score_min_found = res[0][1]
        row = random.choices(res, weights=[1/(0.01 + lemma[1] - score_min_found)**2 for lemma in res], k=1)[0]
        lemma_id = int(row[0])
        lemma = Lemma()
        lemma.load_from_id(self.db, lemma_id)
        
        if lemma.type == "VER": # if it is a verb, take the infinitive
            self.db.cursor.execute("""SELECT ortho_id FROM public.fr_orthos
                                WHERE ortho = %s
                                ORDER BY freq DESC LIMIT 1""",
                                (lemma.lemma, ))
        else: # otherwise the ortho with the highest frequency
            self.db.cursor.execute("""SELECT ortho_id FROM public.fr_orthos
                                WHERE lemma_id = %s
                                ORDER BY freq DESC LIMIT 1""",
                                (lemma_id, ))

        res = self.db.cursor.fetchone()
        if res is None:
            raise Exception("No ortho found corresponding to lemma: %s." % lemma.lemma)
        ortho = Ortho()
        ortho_id = int(res[0])
        ortho.load_from_id(self.db, ortho_id)
        return ortho


    def GetRandomSession(db: DbConnexion, lemmas: List[Lemma] = None):
        # Get lemmas that are frequent
        db.cursor.execute("""SELECT ortho_id, l.lemma_id FROM fr_orthos AS o
                            JOIN fr_lemmas AS l
                            ON l.lemma_id = o.lemma_id
                            WHERE l.lemma_na = o.ortho_na
                            AND LENGTH(l.lemma_na) > 3
                            AND (l.type IN ('ADV', 'NOM', 'VER')
                            OR LEFT(l.type,3) = 'ADJ')
                            ORDER BY o.freq DESC LIMIT 5000""")
        orthos_available = db.cursor.fetchall()
        random.shuffle(orthos_available)

        # Get all the lemmas already used in previous sessions
        db.cursor.execute("""SELECT o.lemma_id FROM fr_sessions AS s
                            JOIN fr_orthos AS o
                            ON o.ortho_id = s.ortho_id""")
        lemmas_used = set()
        res = db.cursor.fetchall()
        for row in res:
            lemma_id = int(row[0])
            lemmas_used.add(lemma_id)

        # Choose the first ortho not already used
        ortho_id_session = -1
        count = 0
        while ortho_id_session < 0 and count < 5000:
            ortho_id = int(orthos_available[count][0])
            lemma_id = int(orthos_available[count][1])
            if lemma_id not in lemmas_used:
                ortho_id_session = ortho_id
            count += 1

        # Create the session
        ortho = Ortho()
        ortho.load_from_id(db, ortho_id_session)
        session = Session(db)
        session.CreateSession(ortho, lemmas)
        return session