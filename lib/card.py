from random import shuffle
from data.cards import CHANCE_CARD, COMMUNITY_CHEST_CARD

class Card:
    def __init__(self, desc, actionTuple):
        self.desc = desc
        self.action = actionTuple

    def getAction(self):
        return self.action

    def getDesc(self):
        return self.desc

    def isJFC(self):
        return False

class JailFreeCard(Card):
    def __init__(self, deck):
        super().__init__("Get out of Jail Free.", None)
        self.owner = None
        self.deck = deck

    def setOwner(self, player):
        self.owner = player
        player.pushJFC(self)

    def returnToDeck(self):
        self.owner = None
        self.deck.addToUsed(self)

    def isJFC(self):
        return True

class CardDeck():
    def __init__(self, type):
        self.cards = []
        self.used = []
        if type == 0:
            for card in CHANCE_CARD:
                self.cards.append(Card(*card))
        elif type == 1:
            for card in COMMUNITY_CHEST_CARD:
                self.cards.append(Card(*card))
        self.cards.append(JailFreeCard(self))
        shuffle(self.cards)

    def draw(self, player):
        if len(self.cards):
            ret = self.cards.pop()
            if type(ret) == JailFreeCard:
                ret.setOwner(player)
                return 0
            self.used.append(ret)
            return ret
        else:
            self.cards = self.used
            shuffle(self.cards)
            self.used = []
            return self.draw(player)

    def addToUsed(self, card):
        self.used.append(card)