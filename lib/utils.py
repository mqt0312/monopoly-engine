from data.price import BUILDING_STAGE_VALUE
from common.flags import *
from common.game_signals import *
from handlers import handlers

def incomeTax(player):
    total = player.getBalance()
    for prop in player.getOwned():
        total += prop.getPrice() if not prop.isMortgage() else (prop.getPrice() // 2)
        if not (prop.isType(SLOT_PROP_RAIL) and prop.isType(SLOT_PROP_UTIL)):
            total += BUILDING_STAGE_VALUE[prop.getBlock()][prop.getStage()]
    return min(200, round(total / 10))

def pay(p1, amount, p2):
    if p1:
        p1.adjustBalance(-amount)
    if p2:
        p2.adjustBalance(amount)
    signal(SIG_PAY, (p1.getName() if p1 else "Bank",
                     amount,
                     p2.getName() if p2 else "Bank"))

def purchase(player, property):
    if not property.isOwned():
        pay(player, property.price, property.getOwner())
        player.own(property)
        property.setOwner(player)

def signal(signo, args=()):
    return handlers(signo, args)
