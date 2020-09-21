# Board slot types:
SLOT_PROP = 0b1
SLOT_PROP_RAIL = 0b1 << 1
SLOT_PROP_UTIL = 0b1 << 2
SLOT_CARD      = 0b1 << 3
SLOT_GOTOJAIL  = 0b1 << 4
SLOT_JAIL      = 0b1 << 5
SLOT_CHARGE    = 0b1 << 6

STATE_BEGIN = 0
STATE_CHECK = 1
STATE_BUY   = 2
STATE_SWITCHPLAYER = 3
STATE_CARD  = 4

PROP_FLAGS = (SLOT_PROP, SLOT_PROP|SLOT_PROP_RAIL, SLOT_PROP|SLOT_PROP_UTIL)

"""
Intent flags
"""
# Maximum "option" for an intent.
# Options are for special cases of an intent that doesn't warrant a separate intent on its own
MAX_OPTION = 4
# Move intent
MOVE  = 0b1 << MAX_OPTION + 1
# Move options
NEAREST_RAIL = 0b1
NEAREST_UTIL = 0b1 << 1
BACK = 0b1 << 2
JAIL = 0b1 << 3
###

# Check intent
CHECK = 0b1 << MAX_OPTION + 2
# Check options
ROLL = 0b1
###

# Pay intent
PAY   = 0b1 << MAX_OPTION + 3
# Pay options
OTHERS = 0b1
SELF = 0b1 << 1
PROP = 0b1 << 2
###



