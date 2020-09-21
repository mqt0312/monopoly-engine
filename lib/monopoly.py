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

    ## Description ##

    This game engine is designed to interact with an implementation. The following design principle will be follow:

    1) The engine trusts that the implementation is smart, but will always verify.

    The design choice to "modularize" the gameplay (4 methods instead of just 1) is to make the engine more adaptive,
    but by allowing an external party to manage the game flow, it is possible to compromise the game if the
    implementation misbehaves. Although it is unlikely that an illegal action goes unnoticed or unhandled by the
    engine, the implementation is responsible for making sure the game is played correctly between the players. The
    signaling system will query for user's input when necessary.

    2) The engine is not explicit with its states

    This means that the engine will never communicate its states to the implementation unprompted. The implementation
    must either keep track of the engine's states with its own methods, or simply infer the states as the game is
    played. To make life easier, querying methods are available to provide the implementation with appropriate data to
    determine the current states of the engine. The signaling system is also used to communicate with the
    implementation about certain in-game events.

    TL;DR: if the implementation knows what it is doing, the engine will be happy.

    For those who prefers bullet points like me:

    What this engine will do:
     - Perform appropriate action determined by an implementation
     - Send signals when appropriates
     - Preventing illegal move, up to some extends.
     - Allow the implementation to see its states
    What this engine will NOT do:
     - Interact with player; the engine interact with and ONLY with the implementation
     - Communicate with the implementation unless it communicate with the engine first.
     
    ## Methods Summary ##

    # Gameplay #
    Monopoly.turn(): Execute a move if not in jail, or ask for user's input when in jail
    Monopoly.check(): Check the current slot and execute appropriate action
    Monopoly.switchPlayer(): Switch to the next player, if appropriate
    Monopoly.build(): Ask the user for a property to build on, then build it if legal

    # Query #
    Monopoly.whoNext(): Return the next player's name (a single String)
    Monopoly.getCurrentPlayerData(): Return current player's data. An "extended" whoNext(), if you will.
    Monopoly.getAllPlayerData(): Similar to status(), but return the data for all players.

    TODO: Implement auction
    TODO: Implement trade

    """
    def __init__(self, pnames):
        """
        :param pnames: An Array. Name of the players as Strings
        """
        self.__board = Board(self)
        self.__players = tuple([Player(pn, self.__board, self) for pn in pnames])
        self.__plookup = {p.getId():p for p in self.__players}
        self.__lastRoll = None
        self.__p = None
        self.__getFirstPlayer()
        self.__state = 0

    def __getFirstPlayer(self):
        """
        Set the current player index if not already

        """
        if not self.__p:
            self.__p = rd.randrange(0, len(self.__players))

    def __getCurPlayer(self):
        """
        Get current player's object method

        Return the current player's Player object based on the current player index (self.p)

        :return: A Player object. The current player
        """
        return self.__players[self.__p]

    def __roll(self):
        """
        Dice roll method

        Roll a double dice, and return the result

        :return: A Tuple contains the sum of the dice and a subtuple containing the value of two dices
        """
        d1 = rd.randint(1, 6)
        d2 = rd.randint(1, 6)
        self.__lastRoll = d1 + d2
        signal(SIG_ROLL, (d1 + d2, (d1, d2)))
        return d1 + d2, (d1, d2)

    def __getBoard(self):
        """
        Get board method

        Return the board associated with the game

        :return: a Board object
        """
        return self.__board

    def __setState(self, new_state):
        """
        Set game state method

        Set the game state to new_state

        :param new_state: An Integer. The new state value to be set as the game's state
        """
        self.__state = new_state

    def __isState(self, test):
        """
        Check game state method

        Return True if the current state is equal to test, False if otherwise

        :param test: An Integer. The state value to be compared with the game's state
        :return: A Boolean value
        """
        return self.__state == test

    def __move(self, x, index=False):
        """
        "Smart" move method

        This method takes in either a step, index or Slot object as x and move the current player to the appropriate
        slot.

        :param x: An Integer or Slot object
        :param index: A Boolean value. True if x: Integer is an index value, False if a step value. Unused if x is a
        Slot object
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

    def __updateNextPlayer(self):
        """
        Player switching method

        Update the next player on the list as the current player.
        """
        self.__p = (self.__p + 1) % self.getPlayerCount()

    def __sendToJail(self):
        """
        Send to jail method

        Send the current player to Jail, and set the status as "in jail".
        """
        player = self.__getCurPlayer()
        signal(SIG_GOTOJAIL, (player.hasJFC(),))
        self.__board.moveTo(player, self.__board.getJail())
        if not player.hasJFC():
            player.setInJail(True)
            player.resetJTL()
        else:
            player.popJFC()

    def __cardExec(self, card):
        """
        Card action execute method

        Execute a card based on its intents. Intents are set flags bit in accordance to the intent flags in flags.py
        Once an intent has been establish, it will execute appropriate functions.

        Is this the best way to process cards? Probably not
        Does it work? Yes!

        :param card: A Card object. The card to be executed
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
                    self.__sendToJail()
                else:
                    self.__move(board[param])
            elif CHECK & intent:
                if ROLL & intent:
                    self.__roll() # TODO: Optimize. This is redundant if util is owned by current player.
                self.check(param)
            elif PAY & intent:
                if OTHERS & intent:
                    for payee in self.__players:
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

    # Gameplay method

    def turn(self, key=None): # TODO: Implement authorization
        """
        Turn method

        If a new turn begins, execute a dice roll and move the current player to the next slot.
        If the current player is in Jail, query for player's choice of either throw dice or pay bail.

        :param key: Not Implemented
        :return: An Integer. Return code. 1 if successful, 0 if otherwise
        """
        if not self.__isState(STATE_BEGIN):
            return 0
        player = self.__getCurPlayer()
        if player.isInJail():
            if signal(SIG_INJAIL, (player.getJTL(), )):
                pay(player, BAIL, BANK)
                player.setInJail(False)
                signal(SIG_OUTOFJAIL)
                res, dice = self.__roll()
            else:
                res, dices = self.__roll()
                d1, d2 = dices
                if d1 == d2:
                    player.setInJail(False)
                    signal(SIG_OUTOFJAIL)
                else:
                    player.decrJTL()
                    if player.getJTL():
                        return 1
                    else:
                        pay(player, BAIL, BANK)
                        player.setInJail(False)
                        signal(SIG_OUTOFJAIL)
        else:
            res, dice = self.__roll()
        self.__move(res)
        self.__setState(STATE_CHECK)
        return 1

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
        if not (self.__isState(STATE_CARD) or self.__isState(STATE_CHECK)):
            return 1
        # Probably a naive way to prevent multiple calls
        player = self.__getCurPlayer()
        slot = player.getSlot()
        signal(SIG_LAND, (slot.getData(),))
        if slot.isType(SLOT_PROP):
            if slot.isOwned() and not slot.isMortgage():
                owner = slot.getOwner()
                if slot.isType(SLOT_PROP_UTIL):
                    rent = self.__lastRoll * slot.getMultiplier() if not mult > 1 else self.__lastRoll
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
                signal(SIG_CARD, (card.getDesc(),))
                self.__setState(STATE_CARD)
                self.__cardExec(card)
                self.__setState(STATE_CHECK)
            else:
                signal(SIG_JAILFREE)
        elif slot.isType(SLOT_CHARGE):
            amount = slot.getAmount(player)
            pay(player, amount, BANK)
        elif slot.isType(SLOT_GOTOJAIL):
            self.__sendToJail()

        self.__setState(STATE_SWITCHPLAYER)
        return 0

    def switchPlayer(self):
        """
        "Safe" player switching method

        Switch to next player if the game finished a move and completed the check.
        :return:
        """
        if self.__isState(STATE_SWITCHPLAYER):
            self.__updateNextPlayer()
            self.__setState(STATE_BEGIN)

    def build(self):
        """
        Build on property method

        This method will send SIG_BUILD with all buildable property the current player has and expect a String
        containing the exact name of the property that the player wishes to build a house/hotel on.

        Redundant checking is deemed necessary because, unlike the binary-answer inquiries in other methods,
        the user input in this one can be arbitrary. It is up to the implementation of the handlers to return the
        correct strings (see Principle #1). It is also worth noting that the redundant checking will NOT provide any
        information should the user's input fails the verification.

        :return: An Integer. Return code. 0 if build was successful, 1 if otherwise
        """

        board = self.__getBoard()
        player = self.__getCurPlayer()
        ownedList = player.getOwnedList()
        if not ownedList:
            signal(SIG_NOBUYABLE)
            return 1
        buyableList = []
        for prop in ownedList:
            if not prop.isType(SLOT_PROP_UTIL | SLOT_PROP_RAIL) and prop.isSibOwned() and prop.isLeastDeveloped():
                buyableList.append(prop.getName())
        propName = signal(SIG_BUILD, (buyableList, ))
        if not propName:
            signal(SIG_NOBUYABLE)
            return 1
        # NOTE: propName is arbitrary since it is user's return
        # The following checks ARE redundant assuming the handler is properly implemented
        slot = board[propName]
        if not slot.isType(SLOT_PROP):
            raise GameError("cannot build on non property")
        if slot.isType(SLOT_PROP_UTIL | SLOT_PROP_RAIL):
            raise GameError("cannot build on railroad or utility")
        owner = slot.getOwner()
        if owner == player and slot.isSibOwned() and slot.isLeastDeveloped():
            board.build(propName)
            return 0
        return 1 # Should NEVER have to hit this line if handler is correctly implemented.

    # Query method

    def whoNext(self):
        """
        Get current player's name method

        Return the current player's name.

        :return: A String. The current player's name
        """
        return self.__getCurPlayer().getName()

    def getPlayerCount(self):
        """
        Get number of player method

        Return the number of players in the game

        :return: An Integer. The number of players
        """
        return len(self.__players)

    def getState(self):
        """
        Get game's state method

        Return the current state of the game

        :return: An Integer. The current state of the game
        """
        return self.__state

    def getCurrentPlayerData(self):
        """
        Get data of the current player method

        Return the data of the current player

        :return: A dict object. The data of the current player
        """

        player = self.__getCurPlayer()
        return player.getData()

    def getAllPlayerData(self, by_uuid=False):
        """
        Get data of all players method

        Return the data of all players

        :param by_uuid: A Boolean value. If True, the key of the return dict object will be the player's UUID
        :return: A dict object. The data of all player. Key will be the names of players by default
        """
        ret = {}
        for p in self.__players:
            next_p = p.getData()
            if by_uuid:
                ret[next_p["id"]] = next_p
            else:
                ret[next_p["name"]] = next_p
        return ret
