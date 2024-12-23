#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import re


"""
o = ord('a')
for i in range(0,26):
    print(f'{o}  {i}  {chr(o)}')
    o = o + 1

codedict = dict(zip([chr(s) for s in range(97,123)],[bin(v)[2:].rjust(5, '0').replace('0', 'a').replace('1', 'b') for v in range(0,26)]))

"""
codedict = {
    'a': 'aaaaa', 'b': 'aaaab', 'c': 'aaaba', 'd': 'aaabb', 'e': 'aabaa',
    'f': 'aabab', 'g': 'aabba', 'h': 'aabbb', 'i': 'abaaa', 'j': 'abaab',
    'k': 'ababa', 'l': 'ababb', 'm': 'abbaa', 'n': 'abbab', 'o': 'abbba',
    'p': 'abbbb', 'q': 'baaaa', 'r': 'baaab', 's': 'baaba', 't': 'baabb',
    'u': 'babaa', 'v': 'babab', 'w': 'babba', 'x': 'babbb', 'y': 'bbaaa',
    'z': 'bbaab'
}

def becon_decode(initcode:str):
    msg = ""
    initcode = initcode.lower()
    codes = re.findall(r".{5}", initcode)
    for code in codes:
        msg += ' ' if not code else dict(map(lambda x:(x[1], x[0]), codedict.items()))[code]

    return msg

