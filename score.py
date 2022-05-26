#from __future__ import annotations
from typing import Tuple
from lemma import Lemma
from scipy.spatial import distance

class Score:

    RANK_THRESHOLD_MAX = 300

    def __init__(self, value_: int, text_: str):
        self.value = value_
        self.text = text_

    def __eq__(self, other) -> bool:
        if not isinstance(other, Score):
            raise Exception("Score are only comparable to Score, not to {0}".format(type(other)))
        else:
            return self.value.__eq__(self.value)

    def __gt__(self, other) -> bool:
        if not isinstance(other, Score):
            raise Exception("Score are only comparable to Score, not to {0}".format(type(other)))
        else:
            return self.value.__gt__(other.value)

    def __lt__(self, other) -> bool:
        if not isinstance(other, Score):
            raise Exception("Score are only comparable to Score, not to {0}".format(type(other)))
        else:
            return self.value.__lt__(other.value)

    def __str__(self) -> str:
        return  "%f - %s" % (self.value, self.text)

    def __repr__(self) -> str:
        return str(self)

    def GetFromValueAndRank(value: float, rank: int):# -> Score:
        text = "Mot non trouvé"
        if rank <= 10:
            text = "Top 10"
        elif rank <= 100:
            text = "Top 100"
        elif rank <= 200:
            text = "Proche"
        elif value > 0.5:
            text = "Assez proche"
        elif value > 0.35:
            text = "Vague"
        elif value > 0.20:
            text = "Assez loin"
        elif value >= 0:
            text = "Rien à voir"
        return Score(value, text)

    def ComputeSimilarity(lemma: Lemma, session) -> float:
        return 1 - distance.cosine(lemma.vector, session.word.lemma.vector)

    def ComputeSimpleValueFromSimilarityAndRank(session, similarity: float, rank: int) -> float:
        RANK_THRESHOLD = min(Score.RANK_THRESHOLD_MAX, len(session.closest_lemmas))
        RANK_SCORE_MIN = 0.6
        if rank == -1:
            rank = RANK_THRESHOLD + 1

        # This is the correct word
        if rank == 0:
            return 1.0

        # Not a close word
        if rank > RANK_THRESHOLD:
            return similarity

        # This is a close word
        # The score is computed based on two linear interpolations:
        # - the first one is based on the rank
        # - the second one is based on the similarity
        # The two are mixed based on rank_coefficient_mix
        rank_frac = (RANK_THRESHOLD - rank) / float(RANK_THRESHOLD)
        rank_score = RANK_SCORE_MIN + rank_frac * (1. - RANK_SCORE_MIN)
        similarity_frac = (similarity - session.similarity_last_closest_lemmas) / (session.similarity_first_closest_lemmas - session.similarity_last_closest_lemmas)
        similarity_score = RANK_SCORE_MIN + similarity_frac * (1. - RANK_SCORE_MIN)
        rank_coefficient_mix = 0.2 + 0.5 * (1. - rank_frac)**2
        return 0.99 * (rank_score * rank_coefficient_mix + similarity_score * (1 - rank_coefficient_mix))

    def ComputeSimpleValueFromSession(lemma: Lemma, session) -> float:
        similarity = Score.ComputeSimilarity(lemma, session)
        rank = session.GetRank(lemma)
        return Score.ComputeSimpleValueFromSimilarityAndRank(session, similarity, rank)


    def ComputeSimpleValueAndSimilarityFromSession(lemma: Lemma, session) -> Tuple[float, float]:
        similarity = Score.ComputeSimilarity(lemma, session)
        rank = session.GetRank(lemma)
        score_value = Score.ComputeSimpleValueFromSimilarityAndRank(session, similarity, rank)
        return (similarity, score_value)

    def ComputeRectifiedValueFromSession(lemma: Lemma, session) -> float:
        base_score = Score.ComputeSimpleValueFromSession(lemma, session)
        if base_score == 1: # The correct word, then no rectification
            return base_score

        score = base_score
        for rectification in session.rectifications:
            if lemma.id in rectification.affected_lemmas:
                coef = rectification.new_score - rectification.old_score
                if coef > 0:
                    coef *= (1.0 - score) 
                    coef /= (1.0 - rectification.old_score)
                else:
                    coef *= float(score)
                    coef /= float(rectification.old_score)

                score += coef * rectification.affected_lemmas[lemma.id]
                if score > 0.99:
                    return 0.99
        return max(0, score)
