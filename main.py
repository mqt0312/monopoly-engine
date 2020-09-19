from lib.monopoly import Monopoly
from handlers import handlers
from os import system
from config import AUTO


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
     - Monopoly.move(): throw the dice and move the player
     - Monopoly.check(): check the slot the player is currently on and perform necessary action

     Refer to the documentation for the specifics of these methods

    == BUILD ==
    Monopoly.build() will send SIG_BUILD to your handlers. You must return what you want to build on. Simple enough

    == TRADE ==
    TBD

    """
    clrscr()
    if AUTO:
        m = Monopoly(["Foo", "Bar"])
    else:
        players = []
        print("Enter the players' name. Press Enter on empty to start the game")
        while 1:
            playerIn = input("Name: ")
            if not playerIn:
                if len(players) > 1:
                    break
                else:
                    print("At least 2 players are required")
            else:
                players.append(playerIn)
                print("Player", playerIn, "added")
        m = Monopoly(players)
        clrscr()
        print("Welcome to Monopoly v0.1")
        print("by Minh Truong")
        print()
        print("Press Enter to Start")
        input()
    while 1:
        clrscr()
        curPlayerName = m.whoNext()
        print(curPlayerName, "is next")
        print("What would you like to do? (Pressing Enter will select 1)")
        print("(1) Play my turn")
        print("(2) Build on my properties")
        print("(q) Forfeit the game")
        while 1:
            playerIn = input("> ")
            if not playerIn or playerIn == "1":
                m.turn()
                m.check()
                m.status(previous=True)
                break
            elif playerIn == "2":
                if not m.build():
                    print("Success!")
                break
            elif playerIn == "q":
                return
            else:
                print("Invalid option")




if __name__ == "__main__":
    main()


