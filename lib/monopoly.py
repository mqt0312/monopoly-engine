import random as rd
from lib.board import Board
from lib.player import Player
from common.errors import GameError
from common.flags import *
from lib.utils import pay, purchase, signal
from common.game_signals import *
from data.slots import RAILROAD, UTILITY
from config import SALARY, AUTH, BAIL

BANK = None

class Monopoly:
    """
    The Monopoly game engine

    This game engine is a "lazy" engine in that you have to probe it for things to happen.
    What it will do:
     - Perform all necessary action in accordance to the Monopoly game rule when Player landed somewhere on the Board
     - Send you signal when appropriates (signals are handled by YOUR handler in handlers.py)
     - Keep state of the game, preventing illegal move
    What it will NOT do:
     - Communicate with you unless you communicate with it first.
     - Prompt you for an action; you have to maintain the logic that determines what the next action should be.
     - Maintain authentication key

    Player will be chosen at uniform random. Current player will be updated internally

    TODO: Implement auction
    TODO: Implement trade

    """
    def __init__(self, pnames):
        self.board = Board(self)
        self.players = tuple([Player(pn, self.board, self) for pn in pnames])
        self.plookup = {p.getId():p for p in self.players}
        self.lastRoll = None
        self.p = None
        self.__getFirstPlayer()
        self.state = 0

    def __getFirstPlayer(self):
        if not self.p:
            self.p = rd.randrange(0, len(self.players))

    def __getCurPlayer(self):
        return self.players[self.p]

    def __getBoard(self):
        return self.board

    def __setState(self, new_state):
        self.state = new_state

    def __getState(self):
        return self.state

    def __move(self, x, index=False):
        """
        "Smart" move method that takes in either a step, index or Slot object as x
        :param x: An Integer or Slot object
        :param index: A Boolean value. True if x: Integer is an index value, False if a step value. Unused if x is a Slot object
        """
        board = self.__getBoard()
        player = self.__getCurPlayer()
        if type(x) == int:
            if not index:
                newIdx, oldIdx = board.move(player, x)
                if x <= 0:
                    return
            else:
                newIdx, oldIdx = board.moveToIndex(player, x)
        else:
            newIdx, oldIdx = board.moveTo(player, x)
        # Pay salary
        if newIdx < oldIdx:
            pay(BANK, SALARY, player)
    def getAllPlayerData(self, by_uuid=False):
        ret = {}
        for p in self.players:
            next_p = p.getData()
            if by_uuid:
                ret[next_p["id"]] = next_p
            else:
                ret[next_p["name"]] = next_p
        return ret

    def getPlayerCount(self):
        return len(self.players)

    def roll(self):
        d1 = rd.randint(1, 6)
        d2 = rd.randint(1, 6)
        self.lastRoll = d1 + d2
        signal(SIG_ROLL, (d1 + d2, (d1, d2)))
        return d1 + d2, (d1, d2)

    def updateNextPlayer(self):
        if self.state == STATE_BEGIN:
            self.p = (self.p + 1) % self.getPlayerCount()

    def turn(self, key=None): # TODO: Implement authorization
        if self.__getState() == STATE_BEGIN:
            player = self.__getCurPlayer()
            if player.isInJail():
                if signal(SIG_INJAIL, (player.getJTL(), )):
                    pay(player, BAIL, BANK)
                    player.setInJail(False)
                else:
                    if player.getJTL() > 0:
                        _, dices = self.roll()
                        d1, d2 = dices
                        if d1 == d2:
                            player.setInJail(False)
                            # TODO: Send message to player. Reason: successful throw, is out of jail
                        else:
                            player.decrJTL()
                            # # TODO: Send message to player. Reason: unsuccessful throw, stays in jail
                            return 1
                    else:
                        # TODO: Send message to player. Reason: out of jail-free throw
                        pay(player, BAIL, BANK)
                        player.setInJail(False)
            res, dice = self.roll()
            self.__move(res)
            self.__setState(STATE_CHECK)
            return 1
        else:
            return 0

    def sendToJail(self):
        player = self.__getCurPlayer()
        signal(SIG_GOTOJAIL, (player.hasJFC(),))
        self.board.moveTo(player, self.board.getJail())
        if not player.hasJFC():
            player.setInJail(True)
            player.resetJTL()
        else:
            player.popJFC()

    def check(self, mult=1, isTurn=True):
        if (not isTurn) or self.__getState() != STATE_CHECK:
            return 1
        self.__setState(STATE_BEGIN) # Probably a naive way to prevent multiple calls
        player = self.__getCurPlayer()
        slot = player.getSlot()
        signal(SIG_LAND, (slot.getData(),))
        if slot.isType(SLOT_PROP):
            if slot.isOwned() and not slot.isMortgage():
                owner = slot.getOwner()
                if slot.isType(SLOT_PROP_UTIL):
                    rent = self.lastRoll * slot.getMultiplier() if not mult > 1 else self.lastRoll
                else:
                    rent = slot.getRent()
                if owner != player:
                    pay(player, rent*mult, owner)
            else:
                if player.getBalance() >= slot.getPrice():
                    if signal(SIG_BUY, (slot.getData(),)):
                        purchase(player, slot)
        elif slot.isType(SLOT_CARD):
            card = slot.drawCard(player)
            if card:
                signal(SIG_CARD, (card,))
                self.cardExec(card)
            else:
                signal(SIG_JAILFREE)
        elif slot.isType(SLOT_CHARGE):
            amount = slot.getAmount(player)
            pay(player, amount, BANK)
        elif slot.isType(SLOT_GOTOJAIL):
            self.sendToJail()

        if isTurn:
            self.updateNextPlayer()
        return

    def build(self):
        board = self.__getBoard()
        player = self.__getCurPlayer()
        ownedList = player.getOwnedList()
        if not ownedList: return 1 # TODO: Send message to player. Reason: no property owned yet
        buyableList = []
        for prop in ownedList:
            if not prop.isType(SLOT_PROP_UTIL | SLOT_PROP_RAIL) and prop.isSibOwned() and prop.isLeastDeveloped():
                buyableList.append(prop.getName())
        propName = signal(SIG_BUILD, (buyableList, ))
        if not propName: return 1
        # NOTE: propName is arbitrary since it is user's return
        # The following checks ARE redundant assuming the handler is properly implemented
        # In other words: Trust, but verify
        # Q&A:
        # - Why is this part not in board.py instead?
        # > Because this part enforces Monopoly's rule on building. board.py, like other components,
        # are to fully trust monopoly.py in rule enforcement
        slot = board[propName]
        if not slot.isType(SLOT_PROP):
            raise GameError("cannot build on non property")
        if slot.isType(SLOT_PROP_UTIL | SLOT_PROP_RAIL):
            raise GameError("cannot build on railroad or utility")
        owner = slot.getOwner()
        if owner == player and slot.isSibOwned() and slot.isLeastDeveloped():
            board.build(propName)
            return 0
        return 1

    def whoNext(self):
        return self.__getCurPlayer().getName()

    def status(self, previous=False):
        if previous:
            prev_p = (self.p - 1) % self.getPlayerCount()
            player = self.players[prev_p]
        else:
            player = self.__getCurPlayer()
        signal(SIG_STATUS, (player.getData(),))

    def cardExec(self, card):
        """
        Execute a card based on its intents. Intents are set flags bit in accordance to the intent flags in flags.py
        Once an intent has been establish, it will execute appropriate functions.

        Is this the best way to process cards? Probably not
        Does it work? Yes!
        :param card:
        :return:
        """
        tups = card.getAction()
        player = self.__getCurPlayer()
        board = self.__getBoard()
        for t in tups:
            intent, param = t
            if MOVE & intent:
                if NEAREST_RAIL & intent or NEAREST_UTIL & intent:
                    indices = [idx for _, idx in (RAILROAD if NEAREST_RAIL & intent else UTILITY)]
                    indices.sort()
                    curIdx = player.getSlot().getIndex()
                    if curIdx > max(indices):
                        self.__move(indices[0], index=True)
                    else:
                        res = next(i for i in indices if i > curIdx)
                        self.__move(res, index=True)
                elif BACK & intent:
                    self.__move(-3)
                elif JAIL & intent:
                    self.sendToJail()
                else:
                    self.__move(board[param])
            elif CHECK & intent:
                if ROLL & intent:
                    self.roll() # TODO: Optimize. This is redundant if util is owned by current player.
                self.check(param, isTurn=False)
            elif PAY & intent:
                if OTHERS & intent:
                    for payee in self.players:
                        if payee != player:
                            pay(player, param, payee)
                elif SELF & intent:
                    pay(BANK, param, player)
                elif PROP & intent:
                    numHouses, numHotels = player.getBuildingCount()
                    feeHouse, feeHotel = param
                    total = numHouses * feeHouse + numHotels * feeHotel
                    pay(player, total, BANK)
                else:
                    pay(player, param, BANK)