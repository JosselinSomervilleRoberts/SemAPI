from connexion import DbConnexion
from ortho import Ortho
from lemma import Lemma
from score import Score
from scipy.spatial import distance
import bisect
from typing import List


class Rectification:

    def __init__(self, db: DbConnexion, lemma_ref_: Lemma, lemma_: Lemma, new_score_: int):
        self.lemma = lemma_
        self.coefficient = 0
        self.affected_lemmas = {}
        self.LoadClosestLemmas(db)
        self.LoadCoefficient(lemma_ref_, new_score_)

    def LoadClosestLemmas(self, db: DbConnexion) -> None:
        THRESHOLD_SIMILARITY = 0.5
        db.cursor.execute("""SELECT lemma_id2, score FROM closest_lemmas
                                    WHERE lemma_id1 = %s AND score > %s
                                    ORDER BY rank ASC""",
                                    (self.id, THRESHOLD_SIMILARITY))
        self.affected_lemmas = {}
        res = db.cursor.fetchall()
        for row in res:
            lemma_id = int(row[0])
            similarity = float(row[1])
            self.affected_lemmas[lemma_id] = similarity

    def LoadCoefficient(self, lemma_ref: Lemma, new_score: float) -> None:
        self.coefficient = new_score - distance.cosine(self.lemma.vector, lemma_ref.vector)


class Session:

    def __init__(self, db_: DbConnexion):
        self.id = None
        self.word = None
        self.rectifications = []
        self.cached_score = {}
        self.rectifications = []
        self.db = db_


    def LoadFromSessionId(self, session_id_:int, db: DbConnexion) -> None:
        self.id = session_id_

        # Find the session
        db.cursor.execute("SELECT ortho_id FROM public.sessions WHERE session_id = %d" % self.id)
        res = db.cursor.fetchone()
        if res is None:
            raise Exception("Cannot load session with id: %d, because the sessions was not found." % self.id)
        baseline_id = int(res[0])

        # Find the word
        self.word = Ortho().load_from_id(db, baseline_id)


    def CacheScore(self, lemma: Lemma, score: Score) -> None:
        self.cached_score[lemma.id] = score


    def SearchScoreFromLemma(self, lemma: Lemma) -> Score:
        try:
            self.db.cursor.execute("""SELECT score, rank FROM scores_computed
                                WHERE session_id = %s AND lemma_id = %s""",
                                (self.id, lemma.id))
            res = self.db.cursor.fetchone()
            if res is None:
                return Score(-1, "Non trouvé") # Not found
            score = float(res[0])
            rank = int(res[1])
            return Score.GetFromValueAndRank(score, rank)
        except Exception as e:
            return Score(-1, "Erreur: " + str(e))


    def GetScoreFromLemma(self, lemma: Lemma) -> Score:
        if lemma.id in self.cached_score:
            return self.cached_score[lemma.id]
        score = self.SearchScoreFromLemma(lemma)
        self.cached_score[lemma.id] = score
        return score


    def AddRectification(self, lemma: Lemma, new_score: float) -> None:
        self.rectifications.append(Rectification(self.db, self.word.lemma, lemma, new_score))
    

    def ComputeAllScores(self, lemmas: List[Lemma]) -> None:
        lemmas_temp = Lemma.load_all(self.db)
        lemmas = []
        for lemma in lemmas_temp:
            score = Score.ComputeRectifiedValueFromLemma(self, lemma)
            lemma.comparator = score
            bisect.insort(lemmas, lemma)

        # Save scores
        for index, lemma in enumerate(lemmas[::-1]):
            self.db.cursor.execute("""INSERT INTO scores_computed(session_id, lemma_id, rank, score)
                                        VALUES(%s, %s, %s, %s)""",
                                        (self.id, lemma.id, index, lemma.comparator))
            self.db.connexion.commit()
