from uuid import uuid1

from common.flags import *
from config import *

class Player:
    def __init__(self, name, board, game):
        self.name = name
        self.money = 1500
        self.inJail = False
        self.jailThrowLeft = 0
        self.properties = {tf: [] for tf in PROP_FLAGS}
        self.jailFreeCard = []
        self.curSlot = board.slots[STARTING_SLOT]
        self.board = board
        self.game = game
        self.handlers = lambda x, y: x
        self.id = uuid1()
        board[STARTING_SLOT].putPlayer(self)

    # Monopoly properties methods

    def getOwned(self, typeFlag=None):
        return self.properties[typeFlag] if typeFlag else self.properties[SLOT_PROP]

    def getOwnedList(self):
        ret = []
        for _, props in self.properties.items():
            ret += props
        return ret

    def own(self, prop):
        self.properties[prop.getType()].append(prop)

    def unown(self, prop):
        self.properties[prop.getType()].remove(prop)

    def isOwned(self, prop):
        return prop in self.properties[prop.getTypeFlag()]

    def getCount(self, typeFlag):
        return len(self.properties[SLOT_PROP|typeFlag])

    # Jail methods

    def isInJail(self):
        return self.inJail

    def setInJail(self, val):
        self.inJail = val

    def pushJFC(self, card):
        self.jailFreeCard.append(card)
        return 0

    def popJFC(self):
        return self.jailFreeCard.pop().returnToDeck()

    def hasJFC(self):
        return self.jailFreeCard and True

    def getJTL(self):
        return self.jailThrowLeft

    def resetJTL(self):
        self.jailThrowLeft = 3

    def decrJTL(self):
        self.jailThrowLeft -= 1

    # Misc methods

    def getName(self):
        return self.name

    def getBalance(self):
        return self.money

    def getBoard(self):
        return self.board

    def getId(self):
        return self.id

    def getData(self):
        ret = {
            "name": self.name,
            "id": self.id,
            "balance": self.money,
            "jailfree": len(self.jailFreeCard),
            "inJail": self.inJail,
            "slotName": self.curSlot.getName(),
            "ownedLookup": [s.getName() for s in self.getOwnedList()]
        }

        return ret

    def adjustBalance(self, amount):
        self.money += amount

    def getSlot(self):
        return self.curSlot

    def getSlotIdx(self):
        return self.curSlot.getIndex()

    def setSlot(self, slot):
        self.curSlot = slot

    def getGame(self):
        return self.game

    def getBuildingCount(self):
        house = 0
        hotel = 0
        for prop in self.getOwned():
            hs, ht = BUILDING_COUNT[prop.getStage()]
            house += hs
            hotel += ht
        return house, hotel
