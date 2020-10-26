import lib.monopoly as monopoly
from os import system
from config import AUTO
from pprint import pprint


def clrscr():
    system("clear")


def main():
    """
    Main game loop

    This loop will act as a "game master". You can utilize the Monopoly object, which will contains the
    populated Board object along with any Player you create.

    A normal game turn can be one of 3 routine: MOVE, BUILD and TRADE.

    == MOVE ==
    MOVE consist of a dice roll and a check. The following steps is minimum for a MOVE routine
     - Monopoly.turn(): throw the dice and move the player
     - Monopoly.check(): check the slot the player is currently on and perform necessary action

     Refer to the documentation for the specifics of these methods

    == BUILD ==
    Monopoly.build() will send SIG_BUILD to your handlers along with a list of eligible properties.
    The handler must return the exact name of the property that the player wants build on.

    == TRADE ==
    TBD

    """
    shell = monopoly.init(["Foo", "Bar"])
    while 1:
        shell("INPUT", "abcd")
        shell("INPUT", "efgh")
        print(shell("SITREP"))
        shell("QUIT")
        break







if __name__ == "__main__":
    main()


