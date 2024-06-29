def gettype(identify) -> str:
    idtype = str(type(identify)).split("'")[1]
    return idtype
