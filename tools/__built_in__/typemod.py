#  Copyright (c) 2024. L.J.Afres, All rights reserved.

def gettype(identity) -> str:
    return type(identity).__name__

def isnum(identity) -> bool:
    try:
        identity = int(identity)
        return isinstance(identity, int)
    except TypeError:
        return False
    except ValueError:
        return False
