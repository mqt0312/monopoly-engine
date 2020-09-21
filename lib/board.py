from lib.board_slots import BoardSlot, PropertySlot, RailroadSlot, UtilitySlot, ChargeSlot, CardSlot, GoToJailSlot
from lib.card import CardDeck
from lib.utils import *
from common.errors import BoardError
from data.slots import *

# Number of slots on board
BOARD_SIZE = 40

class Board:
    def __init__(self, game):
        self.slots = [None for _ in range(BOARD_SIZE)]
        self.slots[0] = BoardSlot("GO")
        self.lookup = {"GO":self.slots}

        self.chance_deck = CardDeck(0)
        self.community_deck = CardDeck(1)
        # #Add normal property
        for group in PROPERTY:
            self.genProp(group, PropertySlot)

        self.genProp(RAILROAD, RailroadSlot)
        self.genProp(UTILITY, UtilitySlot)

        for index in CHANCE_IDX:
            self.slots[index] = CardSlot("Chance!", self.chance_deck)
        for index in COMMUNITY_IDX:
            self.slots[index] = CardSlot("Community Chest", self.community_deck)

        # TODO: Dynamically populate these slots. Generalize the types of slot.
        self.slots[FREE_PARKING_IDX] = BoardSlot("Free Parking")
        self.slots[INCOME_TAX_IDX] = ChargeSlot("Income Tax", incomeTax)
        self.slots[JAIL_IDX] = BoardSlot("Jail")
        self.slots[LUXURY_TAX_IDX] = ChargeSlot("Luxury Tax", 75)
        self.slots[GTJ_IDX] = GoToJailSlot("Go To Jail")

        # Check to see if there is any empty slot.
        if None in self.slots:
            raise BoardError("board not fully populated")

        # Lock the slots down before connecting all slots to board.
        self.slots = tuple(self.slots)
        for slot in self.slots:
            if slot:
                self.lookup[slot.getName()] = slot
                slot.connectBoard(self)

    def __len__(self):
        return len(self.slots)

    def __getitem__(self, item):
        if type(item) == int:
            try:
                return self.slots[item]
            except IndexError:
                raise BoardError("index of " + str(item) + " is out of bound")
        elif type(item) == str:
            try:
                return self.lookup[item]
            except KeyError:
                raise BoardError(item + " is not a slot in this board")
        else:
            raise BoardError("must be an Interger (index of slot) or a String (name of slot)")

    def getSlots(self):
        return self.slots

    def getJail(self):
        return self.slots[JAIL_IDX]

    def moveToIndex(self, player, index):
        return self.moveTo(player, self.slots[index])

    def moveTo(self, player, newSlot):
        curSlot = player.getSlot()
        curIndex = curSlot.getIndex()
        curSlot.unputPlayer(player)
        newSlot.putPlayer(player)
        newIndex = self.slots.index(newSlot)
        player.setSlot(newSlot)
        return newIndex, curIndex

    def move(self, player, step):
        curSlot = player.getSlot()
        curIndex = curSlot.getIndex()
        curSlot.unputPlayer(player)
        nextIndex = (curIndex + step) % len(self)
        self.slots[nextIndex].putPlayer(player)
        player.setSlot(self.slots[nextIndex])
        return nextIndex, curIndex

    def genProp(self, params, SlotObject):
        temp = []
        for p in params:
            temp.append((SlotObject(*p[:-1]), p[-1]))
        for prop, idx in temp:
            prop.addSibs([t[0] for t in temp if t != prop])
            self.slots[idx] = prop

    def build(self, propName):
        self[propName].incrStage()



