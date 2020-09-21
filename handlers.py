from common.game_signals import *
from config import AUTO, BAIL

def confirm():
    if not AUTO:
        input("Press Enter to continue\n")

def yesno():
    if AUTO:
        return 1
    print("(Y)es / (N)o")
    while 1:
        playerIn = input("> ").lower()
        if playerIn == "y":
            return 1
        elif playerIn == "n":
            return 0
        else:
            print("Invalid answer")


sig_name = {
        SIG_STATUS: "SIG_STATUS",
        SIG_BUY: "SIG_BUY",
        SIG_CARD: "SIG_CARD",
        SIG_JAILFREE: "SIG_JAILFREE",
        SIG_ROLL: "SIG_ROLL",
        SIG_LAND: "SIG_LAND",
        SIG_GOTOJAIL: "SIG_GOTOJAIL",
        SIG_PAY: "SIG_PAY",
        SIG_INJAIL: "SIG_INJAIL"
}

def handlers(signo, arg=()):
    '''
    User-define signal handlers. The Game will send appropriate signals for certain events.
    Some signals will require specific return value. These value will determine action taken in the Game

    Gameplay will NOT be halted unless specified.

    The prototypes are pretty rigid since the Game is hard-coded to send the args when appropriate
    Therefore, while making positional arguments optional is fine, the inverse will break the Game
    The handlers' names can be changed, however, but you must also update the dict below accordingly

    In case if it is not obvious, this is NOT similar to Linux signal system.
    This is only for your interface's convenience. You can safely ignore most signals

    There is no signal masking either since I don't need it, or at least not yet. However, AI players may benefit
    from signal masking to reduce handling of redundant signals. Then again, I am not building AI player for this game
    in the foreseeable future, but knock yourself out if you do.

    Below are the handlers for a simple TUI for this game

    :param signo: The signal number. Defined as macros in game_signals
    :param arg: Argument to be passed to handlers.
    :return:
    '''
    def sigStatus(playerData):

        print(playerData["name"] + "\'s status:")
        print("\tBalance:", playerData["balance"])
        print("\tCurrent Slot:", playerData["slotName"])
        print("\tIn Jail:", playerData["inJail"])
        confirm()

    def sigBuy(slotData, customPrice=None):
        """
        For SIG_BUY, you must return either 0 (not buy) or 1 (do buy)
        """
        print("Would you like to buy", slotData["name"], "for", (customPrice if customPrice else slotData["price"]), "dollars?")  #
        ret = yesno()
        if ret:
            print("Thanks for buying", slotData["name"])
        return ret

    def sigPay(payer, amount, payee):
        print(payer, "paid", amount, "to", (payee if payee else "the Bank"))
        confirm()

    def sigCard(cardDesc):
        print("The card you have drawn says:\n\n\t", end="")
        print(cardDesc + "\n")

    def sigJailFree():
        print("Congrats! You just got a Get Out of Jail Free Card!!")
        confirm()

    def sigGoToJail(hasJFC=False):
        print("Whoops, you landed in jail!")
        if hasJFC:
            print("Luckily, you have a Get Out of Jail Free Card!")
        confirm()

    def sigRoll(res, dices):
        print("You rolled a", res, dices)

    def sigLand(slotData):
        print("You landed on", slotData["name"])

    def sigBuild(buyable):
        if not buyable:
            print("You don't have any eligible property yet")
            confirm()
            return 0
        choice = {i: slot for i, slot in enumerate(buyable)}
        for i, name in choice.items():
            print(i+1, "-", name)
        if AUTO:
            return choice[0]
        while 1:
            playerIn = input("> ")
            try:
                return choice[int(playerIn)-1]
            except KeyError:
                print("Invalid Choice")

    def sigInJail(jtl):
        print("You are currently in jail.")
        print("You have", jtl, "jail throw(s) left.")
        print("What would you like to do?")
        print("(1) Try rolling a double")
        print("(2) Pay", BAIL, "dollars to get out")
        if AUTO:
            return 0
        while 1:
            playerIn = input("> ")
            if playerIn == "1":
                return 0
            elif playerIn == "2":
                return 1
            else:
                print("Invalid answer")

    def sigOutOfJail():
        print("You are now out of jail")

    def sigNoBuyable():
        print("You cannot build yet! You need to own at least 1 full block of properties")

    def sigNoJTL():
        print("You don't have any jail throw left. You must now pay the bail.")

    def default():
        print("default handler for", sig_name[signo])
        return 1

    handlers = {
        SIG_STATUS: sigStatus,
        SIG_BUY: sigBuy,
        SIG_CARD: sigCard,
        SIG_JAILFREE: sigJailFree,
        SIG_ROLL: sigRoll,
        SIG_LAND: sigLand,
        SIG_GOTOJAIL: sigGoToJail,
        SIG_PAY: sigPay,
        SIG_INJAIL: sigInJail,
        SIG_BUILD: sigBuild,
        SIG_OUTOFJAIL: sigOutOfJail,
        SIG_NOJTL: sigNoJTL,
        SIG_NOBUYABLE: sigNoBuyable
    }
    if signo in handlers:
        return handlers[signo](*arg)
    else:
        return default()

def silent(signo=0, args=0):
    return 1