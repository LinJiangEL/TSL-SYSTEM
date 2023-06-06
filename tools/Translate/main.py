import os
import sys
import shutil
import json
import time
import urllib
from urllib import request, parse
import requests
import playsound
from fake_useragent import UserAgent
from setuptools.errors import PlatformError

if sys.platform == 'win32':
    os.system("rem TSL-SYSTEM-Translate-Module")

Main_DIR = os.path.dirname(os.path.abspath(__file__))
audiofile = ''
audiofiles = ''

if not os.path.exists(f"{Main_DIR}/dict.txt"):
    with open(f"{Main_DIR}/dict.txt", "w") as f:
        f.write("")
else:
    pass


class Youdao:
    def __init__(self, type=0, word='hello'):
        word = word.lower()
        self._type = type
        self._word = word

        self._dirRoot = os.path.dirname(os.path.abspath(__file__))
        if self._type == 0:
            self._dirSpeech = os.path.join(self._dirRoot, 'Speech_US')
        elif self._type == 1:
            self._dirSpeech = os.path.join(self._dirRoot, 'Speech_EN')

        if not os.path.exists(f'{Main_DIR}/Speech_US'):
            os.makedirs(f'{Main_DIR}/Speech_US')
        if not os.path.exists(f'{Main_DIR}/Speech_EN'):
            os.makedirs(f'{Main_DIR}/Speech_EN')

    def setAccent(self, type=0):
        self._type = type

        if self._type == 0:
            self._dirSpeech = os.path.join(self._dirRoot, 'Speech_US')
        elif self._type == 1:
            self._dirSpeech = os.path.join(self._dirRoot, 'Speech_EN')

    def getAccent(self):
        return self._type

    def download(self, word):
        word = word.lower()
        tmp = self._getWordMp3FilePath(word)
        if tmp is None:
            print("")
            self._getURL()
            print('No exist %s.mp3 file\nURL:\n' % word, self._url, '\nWill download to:\n', self._filePath)
            audiof = requests.get(self._url)
            with open(self._filePath, 'wb') as af:
                af.write(audiof.content)
            print('Successfully download %s.mp3\n' % self._word)
        else:
            print('\nExisted %s.mp3, so ignore response.\n' % self._word)

        return self._filePath

    @staticmethod
    def play(word, audiotype):
        global audiofile, audiofiles
        if audiotype == 'US':
            audiofile = f'{Main_DIR}/Speech_US/' + word + '.mp3'
        elif audiotype == 'EN':
            audiofile = f'{Main_DIR}/Speech_EN/' + word + '.mp3'
        else:
            audiofiles = [f'{Main_DIR}/Speech_US/' + word + '.mp3',
                          f'{Main_DIR}/Speech_EN/' + word + '.mp3']
        if audiotype == 'US_EN':
            print('Playing US Audio ... ', end='')
            playsound.playsound(audiofiles[0])
            print('done.\n')
            time.sleep(1)
            print('Playing EN Audio ... ', end='')
            playsound.playsound(audiofiles[1])
            print('done.\n')
        else:
            print(f'Playing {audiotype} audio ... ', end='')
            playsound.playsound(audiofile)
            print('done.\n')

    def _getURL(self):
        self._url = r'http://dict.youdao.com/dictvoice?type=' + str(self._type) + r'&audio=' + self._word

    def _getWordMp3FilePath(self, word):
        word = word.lower()
        self._word = word
        self._fileName = self._word + '.mp3'
        self._filePath = os.path.join(self._dirSpeech, self._fileName)

        if os.path.exists(self._filePath):
            return self._filePath
        else:
            return None


def translate(word):
    url = 'http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule&smartresult=ugc&sessionFrom=null'

    key = {
        'type': "AUTO",
        'i': word,
        "doctype": "json",
        "version": "2.1",
        "keyfrom": "fanyi.web",
        "ue": "UTF-8",
        "action": "FY_BY_CLICKBUTTON",
        "typoResult": "true"
    }

    response = requests.post(url, data=key)

    if response.status_code == 200:
        return response.text
    else:
        print("Cannot import the Translate API!")
        return None


def get_result(repsonse):
    result = json.loads(repsonse)
    print("")
    print("Input : %s" % result['translateResult'][0][0]['src'])
    print("Result : %s" % result['translateResult'][0][0]['tgt'])
    raf = open(f"{Main_DIR}/dict.txt", "r")
    ra = raf.readlines()
    a = open(f"{Main_DIR}/dict.txt", "a+")
    wordinfo = '{"link":"youdao","' + result['translateResult'][0][0]['src'] + \
               '":"' + result['translateResult'][0][0]['tgt'] + '"}'
    b = []
    for i in ra:
        b.append("".join(i.split('}')[0] + '}'))
    if wordinfo in b:
        print("\033[33mWordResultWarning:word '" +
              result['translateResult'][0][0]['src'] +
              "' is existing！System will ignore response！\033[0m\n"
              )
    elif str(result['translateResult'][0][0]['src']) == str(result['translateResult'][0][0]['tgt']):
        print("\033[33mWordResultWarning:word '" +
              result['translateResult'][0][0]['src'] +
              "' is as the same as its result！System will ignore response！\033[0m\n"
              )
    else:
        a.write(wordinfo)
        a.write("\n")
        a.close()
        print("\033[32mWordResultInfo:word '" +
              result['translateResult'][0][0]['src'] +
              "' has written into dictionary successfully！\033[0m\n"
              )
    raf.close()


def fanyi(keyword):
    base_url = 'https://fanyi.baidu.com/sug'

    data = {
        'kw': keyword
    }

    data = parse.urlencode(data)

    header = {
        "User-Agent": UserAgent().random
    }

    req = request.Request(url=base_url, data=bytes(data, encoding='utf-8'), headers=header)
    res = request.urlopen(req)
    str_json = res.read().decode('utf-8')
    myjson = json.loads(str_json)
    info = myjson['data'][0]['v']
    print("")
    print("Input :", keyword)
    print("Result :", info)
    ra = open(f"{Main_DIR}/dict.txt", "r").readlines()
    a = open(f"{Main_DIR}/dict.txt", "a+")
    wordinfo = '{"' + keyword + '":"' + info + '"}'
    b = []
    for i in ra:
        b.append("".join(i.split('}')[0] + '}'))
    if wordinfo in b:
        print("\033[33mWordResultWarning:word '" + keyword + "' is existing！System will ignore response！\033[0m\n")
    else:
        a.write(wordinfo)
        a.write("\n")
        a.close()
        print("\033[32mWordResultInfo:word '" + keyword + "' has written into dictionary successfully！\033[0m\n")


def main():
    try:
        tran_choice = input("Choice one to continue：[ common/senior/reader ] ")
        print("")
        if tran_choice == "common":
            while True:
                print("Input the word which you want to translate.")
                word = input('Input：')
                if word == "@exit":
                    print("\n\033[33mIterationStopped\033[0m")
                    raise StopIteration
                elif word == "@back":
                    if sys.platform == 'win32':
                        os.system('cls')
                    elif sys.platform == 'linux':
                        os.system('clear')
                    else:
                        raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')
                    print("\n\033[33mIterationReturned\033[0m\n")
                    break
                elif word == "@clean":
                    print('Cleanning ... ', end='', flush=True)
                    shutil.rmtree(f'{Main_DIR}/Speech_US', ignore_errors=True)
                    shutil.rmtree(f'{Main_DIR}/Speech_EN', ignore_errors=True)
                    os.makedirs(f'{Main_DIR}/Speech_US')
                    os.makedirs(f'{Main_DIR}/Speech_EN')
                    with open(f'{Main_DIR}/dict.txt', 'w') as tf:
                        tf.write('')
                    print('done.\n')
                else:
                    list_trans = translate(word)
                    get_result(list_trans)
            main()
        elif tran_choice == "senior":
            while True:
                print("Input the word which you want to translate.")
                word = input('Input：')
                if word == '@exit':
                    print("\n\033[33mIterationStopped\033[0m")
                    raise StopIteration
                elif word == "@back":
                    if sys.platform == 'win32':
                        os.system('cls')
                    elif sys.platform == 'linux':
                        os.system('clear')
                    else:
                        raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')
                    print("\n\033[33mIterationReturned\033[0m\n")
                    break
                elif word == "@clean":
                    print('Cleanning ... ', end='')
                    shutil.rmtree(f'{Main_DIR}/Speech_US', ignore_errors=True)
                    shutil.rmtree(f'{Main_DIR}/Speech_EN', ignore_errors=True)
                    os.makedirs(f'{Main_DIR}/Speech_US')
                    os.makedirs(f'{Main_DIR}/Speech_EN')
                    with open(f'{Main_DIR}/dict.txt', 'w') as tf:
                        tf.write('')
                    print('done.\n')
                else:
                    try:
                        fanyi(word)
                    except IndexError:
                        print(
                            "\n\033[31mWordsNotFoundError:cannot find '{}' from the api "
                            "'https://api.explorerlab.io/development/translate/senior.php'!"
                            " Please check your input-word and try again!\033[0m\n".format(word)
                        )
                    finally:
                        continue
            main()
        elif tran_choice == "reader":
            while True:
                print("Input the word which you want to listen.")
                word = input('Input：')
                if word == '@exit':
                    print("\n\033[33m\nIterationStopped\033[0m")
                    raise StopIteration
                elif word == "@back":
                    if sys.platform == 'win32':
                        os.system('cls')
                    elif sys.platform == 'linux':
                        os.system('clear')
                    else:
                        raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')
                    print("\n\033[33mIterationReturned\033[0m\n")
                    break
                elif word == "@clean":
                    print('Cleanning ... ', end='')
                    shutil.rmtree(f'{Main_DIR}/Speech_US', ignore_errors=True)
                    shutil.rmtree(f'{Main_DIR}/Speech_EN', ignore_errors=True)
                    os.makedirs(f'{Main_DIR}/Speech_US')
                    os.makedirs(f'{Main_DIR}/Speech_EN')
                    print('done.\n')
                else:
                    sp = Youdao()
                    en_us = input("Please input audio standard [ English[en]/American[us]/All[en_us] ]：")
                    if en_us == "us":
                        sp.setAccent(0)
                        audiotype = 'US'
                        try:
                            sp.download(word)
                            sp.play(word, audiotype)
                        except urllib.error.URLError:
                            print(
                                "\033[31mConnectError:cannot connect 225.161.42.73:443! "
                                "Please check your network and try again!\033[0m"
                            )
                            raise StopIteration
                    elif en_us == "en":
                        sp.setAccent(1)
                        audiotype = 'EN'
                        try:
                            sp.download(word)
                            sp.play(word, audiotype)
                        except urllib.error.URLError:
                            print(
                                "\033[31mConnectError:cannot connect 225.161.42.73:443! "
                                "Please check your network and try again!\033[0m"
                            )
                            raise StopIteration
                    elif en_us == "en_us":
                        try:
                            sp.setAccent(0)
                            sp.download(word)
                            sp.setAccent(1)
                            sp.download(word)
                            audiotype = 'US_EN'
                            try:
                                sp.play(word, audiotype)
                            except urllib.error.URLError:
                                print(
                                    "\033[31mConnectError:cannot connect 225.161.42.73:443! "
                                    "Please check your network and try again!\033[0m"
                                )
                                raise StopIteration
                        except urllib.error.URLError:
                            print(
                                "\033[31mConnectError:cannot connect 225.161.42.73:443!"
                                " Please check your network and try again!\033[0m"
                            )
                            raise StopIteration
                        else:
                            continue
                    else:
                        print("\033[31mSoundTypeNotFound:cannot find this sound type from audio sounds!\033[0m\n")
                        continue
            main()
        else:
            print("\033[31mAPINotFoundError:cannot found this TSL-API! "
                  "Please make the name correctly and try again!\033[0m\n"
                  )
    except KeyboardInterrupt:
        print("\n\033[31mUserError:user cancelled this operation!\033[0m")
        raise StopIteration
    except json.decoder.JSONDecodeError:
        print("\n\033[31mValueError:the value '\033[0m\033[7m \033[0m\033[31m' cannot be identified!\033[0m")
        print("\033[31mValueError:please press Enter before you enter a word or a sentence!\033[0m")
        raise StopIteration
    except KeyError:
        print("\n\033[31mValueError:value 'keyword' has no '\033[0m\033[7m \033[0m\033[31m'!\033[0m")
        print("\033[31mValueError:please press Enter before you enter a word or a sentence!\033[0m")
        raise StopIteration
    except requests.exceptions.ConnectionError:
        print(
            "\n\033[31mConnectError:cannot connect the phphost "
            "'https://api.explorerlab.io/development/translate/common.php'! "
            "Please check the network and try again!\033[0m"
        )
        raise StopIteration
    except urllib.error.URLError:
        print(
            "\n\033[31mConnectError:cannot connect the phphost "
            "'https://api.explorerlab.io/development/translate/senior.php'! "
            "Please check the network and try again!\033[0m"
        )
        raise StopIteration
    finally:
        print('')


def run():
    print('-' * 37)
    print('|    TSL-SYSTEM Translate Module    |')
    print('-' * 37, '\n')

    main()
