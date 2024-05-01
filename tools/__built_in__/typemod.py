def gettype(identify) -> str:
    typex = str(type(identify)).split("'")[1]
    return typex
