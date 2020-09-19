def sigStatus():
    print("default handler for SIG_STATUS")

def sigBuy():
    print("default handler for SIG_BUY")

def sigCard():
    print("default handler for SIG_CARD")

def sigJailFree():
    print("default handler for SIG_CARD")


SIG_HANDLERS = (sigStatus, sigBuy, sigCard, sigJailFree)