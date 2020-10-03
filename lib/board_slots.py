from common.flags import SLOT_PROP, SLOT_PROP_UTIL, SLOT_PROP_RAIL, SLOT_CHARGE, SLOT_CARD, SLOT_GOTOJAIL
from data.price import TRAIN_PRICE, TRAIN_RENT, UTIL_PRICE


class BoardSlot:
    def __init__(self, name):
        # Slot's parameter
        self.name = name
        self.board = None
        self.players = []
        self.type = 0
        self.index = None

    def getName(self):
        return self.name

    def getType(self):
        return self.type

    def isType(self, type):
        return (self.type & type) and True

    def getIndex(self):
        return self.index

    def getData(self):
        ret = {
            "name": self.getName(),
            "type": self.getType(),
            "index": self.getIndex(),
            "players": [p.getName() for p in self.players]
        }
        return ret

    def putPlayer(self, player):
        self.players.append(player)

    def unputPlayer(self, player):
        self.players.remove(player)

    def connectBoard(self, board):
        self.board = board
        # TODO: Catch ValueError and AttributeError for illegal slot connection
        self.index = self.board.getSlots().index(self)


class PropertySlot(BoardSlot):
    def __init__(self, name, price, block=None, rents=None):
        """
        Initialize a Property slot
        :param name: The name of the property
        :param price: The price of the property
        :param block: The block the property is on (optional for Railroad and Utility)
        :param rents: The list of rent amount according to the property's stage of development
        """
        super().__init__(name)
        self.owner = None
        self.price = price
        self.block = block
        self.type |= SLOT_PROP
        self.stage = 0
        self.rents = rents
        self.mortgaged = False
        self.siblings = []

    # Properties methods

    def getPrice(self):
        """
        Return the price of the property
        """
        return self.price

    def getBlock(self):
        """
        Return the block (side of the board) that
        the property is on
        """
        return self.block

    def getRent(self, *arg):
        """
        Return the rent amount based on the
        property's stage of development
        """
        return self.rents[self.stage]

    def getData(self):
        ret = super().getData()
        ret["price"] = self.getPrice()
        if self.isOwned():
            ret["owner"] = self.getOwner().getName()
        else:
            ret["owner"] = None
        ret["siblings"] = [s.getName() for s in self.getSibs()]
        if self.isType(SLOT_PROP_UTIL):
            ret["multiplier"] = self.getMultiplier()
        else:
            ret["rent"] = self.getRent()

        return ret

    # Ownership and relationship with other properties

    def addSibs(self, sibs):
        """
        Add a sibling property
        :param sibs: The sibling property to be added
        """
        self.siblings += sibs

    def getSibs(self):
        """
        Get all siblings property
        :return: A List of siblings PropertySlots
        """
        return self.siblings

    def isSibOwned(self):
        """
        Check whether all siblings are owned by the same player
        :return: A Boolean value
        """
        ret = True
        for sib in self.getSibs():
            ret &= sib.getOwner() == self.getOwner()
        return ret

    def isLeastDeveloped(self):
        if self.isSibOwned():
            ret = True
            for sib in self.getSibs():
                ret &= sib.getStage() > self.getStage()
            return ret
        return False

    def isOwned(self):
        """
        Check whether this property is owned by one of the player
        :return: A Boolean value
        """
        return self.owner and True

    def getOwner(self):
        """
        Return a Player object of the owner
        """
        return self.owner

    def setOwner(self, new_owner):
        """
        Set the new owner of this property
        :param new_owner: A Player object. The new owner of this property
        """
        self.owner = new_owner

    # Mortgage methods

    def isMortgage(self):
        """
        Check whether the property is mortgaged
        :return: A Boolean value
        """
        return self.mortgaged

    def setMortgage(self, val):
        """
        Set the mortgage status of this property
        :param val: A Boolean value
        """
        self.mortgaged = True

    # Stage methods

    def incrStage(self):
        """
        Increment the development stage of this property.
        """
        self.stage += 1

    def decrStage(self):
        """
        Decrement the development stage of this property
        """
        self.stage -= 1

    def getStage(self):
        """
        Get the development stage of this property
        :return: An Integer representing the development stage of this property
        """
        return self.stage

    def resetStage(self):
        """
        Reset the development stage of this property to 0
        """
        self.stage = 0

    def setStage(self, new_stage):
        """
        Set the development stage of this property
        :param new_stage: The new value of the development stage
        """
        self.stage = new_stage


class RailroadSlot(PropertySlot):
    def __init__(self, name):
        super().__init__(name, TRAIN_PRICE, None, TRAIN_RENT)
        self.type |= SLOT_PROP_RAIL

    def build(self):
        return # disable this method since you don't "build" on railroad slots

    def setOwner(self, new_owner):
        self.owner = new_owner
        self.setStage(self.owner.getCount(SLOT_PROP_RAIL)-1)
        for sib in self.getSibs():
            if sib.getOwner() == new_owner:
                sib.setStage(self.owner.getCount(SLOT_PROP_RAIL)-1)


class UtilitySlot(PropertySlot):
    def __init__(self, name):
        super().__init__(name, UTIL_PRICE)
        self.type |= SLOT_PROP_UTIL

    def build(self):
        return # disable this method since you don't "build" on utility slots

    def getMultiplier(self):
        return (10 if self.isSibOwned() else 4) if self.isOwned() else 0

    def getRent(self, *args):
        multiplier = 10 if self.isSibOwned() else 4
        return args[0] * multiplier


class ChargeSlot(BoardSlot):
    def __init__(self, name, amount, payee=None):
        super().__init__(name)
        self.amount = amount
        self.type |= SLOT_CHARGE

    def getAmount(self, player=None):
        return self.amount(player) if callable(self.amount) else self.amount


class CardSlot(BoardSlot):
    def __init__(self, name, deck=None):
        super().__init__(name)
        self.deck = deck
        self.type |= SLOT_CARD

    def drawCard(self, player):
        if self.deck:
            return self.deck.draw(player)

    def setDeck(self, deck):
        self.deck = deck


class GoToJailSlot(BoardSlot):
    def __init__(self, name):
        super().__init__(name)
        self.type |= SLOT_GOTOJAIL