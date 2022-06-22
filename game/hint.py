from enum import Enum

class HintStatus(Enum):
    Available = 1
    Unavailable = 2
    Used = 3

class Hint:
    def __init__(self):
        self.status = HintStatus.Unavailable
        self.cost = 0
        self.type = -1
        self.value = ""
        self.code = None
        self.libelle = "Custom"
        self.conditions = []

    def GetValue(self):
        return self.value

    def CheckStatus(self, args):
        if self.status == HintStatus.Used: return
        available = True
        for condition in self.conditions:
            operator = condition[0]
            param = condition[1]
            if operator == "==" and not(args[param] == condition[2]): available = False
            if operator == ">=" and not(args[param] >= condition[2]): available = False
            if operator == "<=" and not(args[param] <= condition[2]): available = False
            if operator == ">"  and not(args[param] >  condition[2]): available = False
            if operator == "<"  and not(args[param] <  condition[2]): available = False
        if available: self.status = HintStatus.Available
        else: self.status = HintStatus.Unavailable


class HintNbLetters(Hint):
    def __init__(self, nb_letters: int):
        Hint.__init__(self)
        self.libelle = "Nombre de lettres"
        self.code = "/hint/nb-letters"
        self.cost = 5
        self.type = 0
        self.value = str(nb_letters) + " lettre"
        if nb_letters > 1: self.value += "s"
        self.conditions = [[">=", "nb_attempts", 10]]

class HintNbSylabbles(Hint):
    def __init__(self, nb_sylabbles: int):
        Hint.__init__(self)
        self.libelle = "Nombre de syllabes"
        self.code = "/hint/nb-syllables"
        self.cost = 5
        self.type = 1
        self.value = str(nb_sylabbles) + " syllabe"
        if nb_sylabbles > 1: self.value += "s"
        self.conditions = [[">=", "nb_attempts", 10]]

class HintType(Hint):
    def __init__(self, type: int):
        Hint.__init__(self)
        self.libelle = "Nature"
        self.code = "/hint/type"
        self.cost = 8
        self.type = 2
        self.value = type
        self.conditions = [[">=", "nb_attempts", 20]]

class HintFirstLetter(Hint):
    def __init__(self, first_letter: int):
        Hint.__init__(self)
        self.libelle = "Première lettre"
        self.code = "/hint/first-letter"
        self.cost = 10
        self.type = 3
        self.value = first_letter.upper()
        self.conditions = [[">=", "nb_attempts", 30]]

class HintWord(Hint):
    def __init__(self, score: int):
        Hint.__init__(self)
        self.libelle = "Mot à %d" % int(100 * score)
        self.code = "/hint"
        self.cost = 10
        self.type = int(100 * score)
        self.value = score
        self.conditions = [[">=", "nb_attempts", min(20, score * 300 - 200)],
                            ["<", "best_score", score - 0.15]]

    def GetValue(self):
        return "Not implemented"