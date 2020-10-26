import random as rd
import threading
import inspect

from lib.board import Board
from lib.player import Player
from common.errors import GameError
from common.flags import *
from lib.utils import pay, purchase, signal
from common.game_signals import *
from data.slots import RAILROAD, UTILITY
from config import SALARY, AUTH, BAIL

BANK = None


class Monopoly():
    def __init__(self, pnames):
        """
        :param pnames: An Array. Name of the players as Strings
        """
        self.board = Board()
        self.players = tuple([Player(pn, self.board, self) for pn in pnames])
        self.plookup = {p.getId(): p for p in self.players}
        self.lastRoll = None
        self.p = None
        self.getFirstPlayer()
        self.state = 0

    def getFirstPlayer(self):
        """
        Set the current player index if not already

        """
        if not self.p:
            self.p = rd.randrange(0, len(self.players))

    def getCurPlayer(self):
        """
        Get current player's object method

        Return the current player's Player object based on the current player index (self.p)

        :return: A Player object. The current player
        """
        return self.players[self.p]

    def roll(self):
        """
        Dice roll method

        Roll a double dice, and return the result

        :return: A Tuple contains the sum of the dice and a subtuple containing the value of two dices
        """
        d1 = rd.randint(1, 6)
        d2 = rd.randint(1, 6)
        self.lastRoll = d1 + d2
        signal(SIG_ROLL, (d1 + d2, (d1, d2)))
        return d1 + d2, (d1, d2)

    def getBoard(self):
        """
        Get board method

        Return the board associated with the game

        :return: a Board object
        """
        return self.board

    def setState(self, new_state):
        """
        Set game state method

        Set the game state to new_state

        :param new_state: An Integer. The new state value to be set as the game's state
        """
        self.state = new_state

    def isState(self, test):
        """
        Check game state method

        Return True if the current state is equal to test, False if otherwise

        :param test: An Integer. The state value to be compared with the game's state
        :return: A Boolean value
        """
        return self.state == test

    def move(self, x, index=False):
        """
        "Smart" move method

        This method takes in either a step, index or Slot object as x and move the current player to the appropriate
        slot.

        :param x: An Integer or Slot object
        :param index: A Boolean value. True if x: Integer is an index value, False if a step value. Unused if x is a
        Slot object
        """
        board = self.getBoard()
        player = self.getCurPlayer()
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

    def updateNextPlayer(self):
        """
        Player switching method

        Update the next player on the list as the current player.
        """
        self.p = (self.p + 1) % self.getPlayerCount()

    def sendToJail(self):
        """
        Send to jail method

        Send the current player to Jail, and set the status as "in jail".
        """
        player = self.getCurPlayer()
        signal(SIG_GOTOJAIL, (player.hasJFC(),))
        self.board.moveTo(player, self.board.getJail())
        if not player.hasJFC():
            player.setInJail(True)
            player.resetJTL()
        else:
            player.popJFC()

    def cardExec(self, card):
        """
        Card action execute method

        Execute a card based on its intents. Intents are set flags bit in accordance to the intent flags in flags.py
        Once an intent has been establish, it will execute appropriate functions.

        Is this the best way to process cards? Probably not
        Does it work? Yes!

        :param card: A Card object. The card to be executed
        """
        tups = card.getAction()
        player = self.getCurPlayer()
        board = self.getBoard()
        for t in tups:
            intent, param = t
            if MOVE & intent:
                if NEAREST_RAIL & intent or NEAREST_UTIL & intent:
                    indices = [idx for _, idx in (RAILROAD if NEAREST_RAIL & intent else UTILITY)]
                    indices.sort()
                    curIdx = player.getSlot().getIndex()
                    if curIdx > max(indices):
                        self.move(indices[0], index=True)
                    else:
                        res = next(i for i in indices if i > curIdx)
                        self.move(res, index=True)
                elif BACK & intent:
                    self.move(-3)
                elif JAIL & intent:
                    self.sendToJail()
                else:
                    self.move(board[param])
            elif CHECK & intent:
                if ROLL & intent:
                    self.roll()  # TODO: Optimize. This is redundant if util is owned by current player.
                self.check(param)
            elif PAY & intent:
                if OTHERS & intent:
                    for payee in self.players:
                        if payee != player:
                            pay(player, param, payee) if not SELF & intent else pay(payee, param, player)
                elif SELF & intent:
                    pay(BANK, param, player)
                elif PROP & intent:
                    numHouses, numHotels = player.getBuildingCount()
                    feeHouse, feeHotel = param
                    total = numHouses * feeHouse + numHotels * feeHotel
                    pay(player, total, BANK)
                else:
                    pay(player, param, BANK)

    def whoNext(self):
        """
        Get current player's name method

        Return the current player's name.

        :return: A String. The current player's name
        """
        return self.getCurPlayer().getName()

    def getPlayerCount(self):
        """
        Get number of player method

        Return the number of players in the game

        :return: An Integer. The number of players
        """
        return len(self.players)

    def getState(self):
        """
        Get game's state method

        Return the current state of the game

        :return: An Integer. The current state of the game
        """
        return self.state

    def getCurrentPlayerData(self):
        """
        Get data of the current player method

        Return a snapshot of the current player's data

        :return: A dict object. The data of the current player
        """

        player = self.getCurPlayer()
        return player.getData()

    def getAllPlayerData(self, by_uuid=False):
        """
        Get data of all players method

        Return snapshots of all players' data

        :param by_uuid: A Boolean value. If True, the key of the return dict object will be the player's UUID
        :return: A dict object. The data of all player. Key will be the names of players by default
        """
        ret = {}
        for p in self.players:
            next_p = p.getData()
            if by_uuid:
                ret[next_p["id"]] = next_p
            else:
                ret[next_p["name"]] = next_p
        return ret

    def getData(self):
        """
        Return a snapshot of the game's data

        :return: A dict object. The data of the board
        """
        ret = self.getBoard().getData()
        ret["players"] = {}
        for p in self.players:
            ret["players"][p.getName()] = p.getData()
        return ret


# class MonopolyShell():
#     def __init__(self, ready):
#         self.buffer = []
#         self.ready = ready
#         self.gameStatus = None
#
#     def flush(self):
#         ret = self.buffer
#         self.buffer = [] # naive flush
#         return ret
#
#     def setGameStatus(self, game):
#         self.gameStatus = game.getData()
#
#     def getGameData(self):
#         return self.gameStatus
#
#     def send(self, *args, **kwargs):
#         for a in args:
#             self.buffer.append(a)
#         self.ready.set()
#         pass

class _MonopolyEngine(threading.Thread):
    def __init__(self, game):
        super().__init__()
        if not game:
            raise GameError("Engine requires a game")
        self.game = game

        self.readInReady = threading.Event()
        self.writeInReady = threading.Event()
        self.readInReady.set()
        self.writeInReady.set()

        self.readOutReady = threading.Event()
        self.writeOutReady = threading.Event()
        self.readOutReady.set()
        self.writeOutReady.set()


        self.ended = False
        self.inBuf = []
        self.outBuf = []

    def getShell(self):
        return self.shell

    def popIn(self, n=1):
        self.writeInReady.wait()
        self.writeInReady.clear()
        self.readInReady.wait()
        self.readInReady.clear()

        print("Popping input...")
        ret = self.outBuf.copy()
        self.outBuf.clear()

        self.readInReady.set()
        self.writeInReady.set()

    def pushIn(self, *args):
        self.readInReady.wait()
        self.readInReady.clear()
        self.writeInReady.wait()
        self.writeInReady.clear()

        print("Pushing input...")
        self.inBuf.extend(args)

        self.writeInReady.set()
        self.readInReady.set()

    def popOut(self, timeout=None, n=1):
        self.writeOutReady.wait()
        self.writeOutReady.clear()
        self.readOutReady.wait()
        self.readOutReady.clear()

        print("Popping output...")
        ret = self.outBuf.copy()
        self.outBuf.clear()

        self.readOutReady.set()
        self.writeOutReady.set()

        return ret

    def pushOut(self, *args):
        self.readOutReady.wait()
        self.readOutReady.clear()
        self.writeOutReady.wait()
        self.writeOutReady.clear()

        print("Pushing output...")
        self.outBuf.extend(args)

        self.writeOutReady.set()
        self.readOutReady.set()


    def shell(self, cmd, *args, **kwargs):
        if cmd == "INPUT":
            self.pushIn(*args)
        elif cmd == "SITREP":
            return self.popOut(kwargs["timeout"] if "timeout" in kwargs else None)
        elif cmd == "QUIT":
            self.kill()

    def getInBuf(self):
        self.readInReady.wait()
        self.readInReady.clear()
        ret = self.inBuf
        self.readInReady.set()
        return ret

    def getOutBuf(self):
        self.readOutReady.wait()
        self.readOutReady.clear()
        ret = self.inBuf
        self.readOutReady.set()
        return ret

    def turn(self, key=None):  # TODO: Implement authorization
        """
        Turn method

        If a new turn begins, execute a dice roll and move the current player to the next slot.
        If the current player is in Jail, query for player's choice of either throw dice or pay bail.

        :param key: Not Implemented
        :return: An Integer. Return code. 0 if nothing illegal happened, 1 if otherwise
        """
        player = self.game.getCurPlayer()
        if player.isInJail():
            userIn = self.popIn()
            if type(userIn) == bool and userIn:
                pay(player, BAIL, BANK)
                player.setInJail(False)
                res, dice = self.game.roll()
            else:
                res, dices = self.game.roll()
                d1, d2 = dices
                if d1 == d2:
                    player.setInJail(False)
                    signal(SIG_OUTOFJAIL)
                else:
                    player.decrJTL()
                    if player.getJTL():
                        return 0
                    else:
                        pay(player, BAIL, BANK)
                        player.setInJail(False)
        else:
            res, dice = self.game.roll()
        self.game.move(res)
        return 0

    def check(self, mult=1):
        """
        Check methods

        If a move is completed, this method will examine the current slot
        - If it's an unowned property slot, it will query the player for whether to buy that property
        - If it's an owned property slot, it will charge the current player and deposit the rent to the owner
        - If it's a card slot, it will draw and execute a card
        - If it's a go to jail slot, it will send the player to jail and set the player's status as "in jail"
        - If it's a charge slot (Income Tax and Luxury Tax) it will charge the current player the appropriate amount
        - Otherwise, it will do nothing

        :param mult: An integer. Multiplier for the rent if appropriate. Note: Will overwrite the utility's multiplier
        :return: An Integer. Return code. 0 if successful, 1 if otherwise
        """
        player = self.game.getCurPlayer()
        slot = player.getSlot()
        signal(SIG_LAND, (slot.getData(),))
        if slot.isType(SLOT_PROP):
            if slot.isOwned() and not slot.isMortgage():
                owner = slot.getOwner()
                if slot.isType(SLOT_PROP_UTIL):
                    rent = self.game.lastRoll * slot.getMultiplier() if not mult > 1 else self.game.lastRoll
                else:
                    rent = slot.getRent()
                if owner != player:
                    pay(player, rent * mult, owner)
            else:
                if player.getBalance() >= slot.getPrice():
                    if signal(SIG_BUY, (slot.getData(),)):
                        purchase(player, slot)
        elif slot.isType(SLOT_CARD):
            card = slot.drawCard(player)
            if card:
                signal(SIG_CARD, (card.getDesc(),))
                self.game.cardExec(card)
            else:
                signal(SIG_JAILFREE)
        elif slot.isType(SLOT_CHARGE):
            amount = slot.getAmount(player)
            pay(player, amount, BANK)
        elif slot.isType(SLOT_GOTOJAIL):
            self.game.sendToJail()

        return 0

    def kill(self):
        self.ended = True

    def run(self):
        while not self.ended:
            # for _ in range(10000000):
            #     pass
            print(self.getInBuf())
            print(self.getOutBuf())
            # print(self.getInput())
        print("Woo Wee, finally ended!!")


def init(pnames):
    e = _MonopolyEngine(Monopoly(pnames))
    e.start()
    return e.getShell()
