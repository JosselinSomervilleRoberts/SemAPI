from __future__ import annotations
from session import Session
from lemma import Lemma

class Score:

    def __init__(self, value_: int, text_: str):
        self.value = value_
        self.text = text_

    def GetFromValueAndRank(value: float, rank: int) -> Score:
        text = "Rien à voir"
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
        return Score(value, rank)

    def ComputeSimpleValueFromDistanceAndRank(distance: float, rank: int) -> float:
        THRESHOLD = 200
        VALUE_THRESHOLD = 0.6
        if rank > THRESHOLD: # Not a close word
            return distance
        rank_frac = (THRESHOLD - rank) / float(THRESHOLD)
        rank_coefficient = 0.3 + 0.7 * rank_frac**2
        distance_coefficient = 1. - rank_coefficient
        rank_score = VALUE_THRESHOLD + rank_frac * (1. - VALUE_THRESHOLD)
        return rank_coefficient * rank_score + distance_coefficient * distance

    def ComputeRectifiedValueFromLemma(session: Session, lemma: Lemma) -> float:
        THRESHOLD_SIMILARITY = 0.5
        base_score = ComputeSimpleValueFromDistanceAndRank(distance, rank)
        rectification_sum = 0
        rectification_divider = 0
        for rectification in session.rectifications:
            if lemma.id in rectification.affected_lemmas:
                rectification_sum += rectification.coefficient * rectification.affected_lemmas[lemma.id]
                rectification_divider += rectification.coefficient
        return (base_score + rectification_sum) / (1. + rectification_divider)
