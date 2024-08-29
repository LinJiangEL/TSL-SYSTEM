#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import random
import base64
import binascii


def baseencrypt(s, n=1, salt=None):
    for i in range(n):
        s = s + salt if salt else s
        s = str(base64.b64encode(s.encode('utf-8'))).split("'")[1]
    return s


def basedecrypt(bs, n):
    for i in range(n):
        if bs[:2] == "b'" and bs[-1] == "'":
            bs = bs.split("'")[1]
        bs = str(base64.b64decode(bs)[:-6].decode('utf-8')).split("'")[0]
    return bs


def generate_salt(num):
    salt = ''
    salt_elements = []
    s = list(chr(s1) for s1 in range(65, 91)) + list(chr(s2) for s2 in range(97, 123)) + list(range(10))

    for i in range(num):
        salt_elements.append(random.choices(s))

    for item in salt_elements:
        salt = salt + str(item[0])
    return salt


def run():
    print('-' * 36)
    print('|     TSL-SYSTEM Passwd Module     |')
    print('-' * 36)

    mode = input('\nPlease input the tool mode [encrypt/decrypt]: ')
    if mode == 'encrypt':
        text = input('Please input the text which you want to encrypt: ')
        n = 3
        x = 9 % (n * 2)
        salt = generate_salt(6)
        passwd1 = baseencrypt(s=text, n=n, salt=salt)
        passwd1 = passwd1.replace('=', salt[4], 1) if passwd1.count('=') == 1 \
            else passwd1.replace('==', salt[5] + salt[3], 1)
        passwd = passwd1[:-x] + f't{n}' + passwd1[-x:] + str(x) + salt
        print(f'Passwd text: {passwd}\nSalt: {salt}\nOffset: {x}')
    elif mode == 'decrypt':
        passwd = input('Please input the passwd which you want to decrypt: ')
        x = int(passwd[-7])
        if len(passwd) >= 9 and 0 <= x <= 3:
            xn = -x - 8
            n = passwd[xn]
            bs = passwd.split('t' + str(n))[0] + passwd.split("t" + str(n))[1][:-7]
            salt = passwd[-6:]
            try:
                text = basedecrypt(bs=bs, n=int(n))
            except binascii.Error:
                bs = (bs[:-9] + bs[-9:].replace(salt[4], '=', 1)) if (passwd[-8] == salt[4]) \
                    else (bs[:-9] + bs[-9:].replace(salt[5] + salt[3], '==', 1)) \
                    if (passwd[-9:-7] == salt[5] + salt[3]) \
                    else 'error'
                print(bs)
                text = basedecrypt(bs=bs, n=int(n))
            print(f'Text: {text}\n')
    else:
        print(f'\033[31mInputError:mode "{mode}" is not defined!\033[0m\n')
