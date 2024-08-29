#  Copyright (c) 2024. L.J.Afres, All rights reserved.

def gettype(identify) -> str:
    idtype = str(type(identify)).split("'")[1]
    return idtype
