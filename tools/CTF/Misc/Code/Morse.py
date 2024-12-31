#  Copyright (c) 2024. L.J.Afres, All rights reserved.
import librosa
import librosa.display
import matplotlib.pyplot as plt

morse_code = (
    "-.-.--", ".--.-.", ".-...", "-.--.", "-.--.-",
    "T", ".-.-.", "-...-", "-----", ".----",
    "..---", "...--", "....-", ".....", "-....",
    "--...", "---..", "----.", ".-", "-...",
    "-.-.", "-..", ".", "..-.", "--.",
    "....", "..", ".---", "-.-", ".-..",
    "--", "-.", "---", ".--.", "--.-",
    ".-.", "...", "-", "..-", "...-",
    ".--", "-..-", "-.--", "--..", "---...",
    ".-..-.", ".----.", "--..--", "E",
    "-..-.", "..--..", "\\"
)

alphabet_code = (
    "!", "@", "&", "(", ")",
    "-", "+", "=", "0", "1"
    "2", "3", "4", "5", "6",
    "7", "8", "9", "A", "B",
    "C", "D", "E", "F", "G",
    "H", "I", "J", "K", "L",
    "M", "N", "O", "P", "Q",
    "R", "S", "T", "U", "V",
    "W", "X", "Y", "Z", ":",
    "\"", "\'", ".", ",", ".",
    "/", "?", " "
)

morsedict = dict(zip(alphabet_code, morse_code))
alphadict = dict(zip(morse_code, alphabet_code))


class MorseAudio:
    def __init__(self, audio_file):
        self.audio_file = audio_file
        self.y, self.sr = librosa.load(self.audio_file)

    def plot(self):
        plt.figure(figsize=(14, 5))
        librosa.display.waveshow(self.y, sr=self.sr)
        plt.title('Waveform')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.show()


def morse_encode(text: str):
    alphas = [alpha.upper() for alpha in text]
    result = '\\'.join([morsedict[alpha] for alpha in alphas])
    return result


def morse_decode(text: str):
    msg = [morse.split("\\") for morse in text.split("\\\\\\")]
    text = ""
    for morse in msg:
        for letter in morse:
            text += alphadict[letter]
        text += " "
    return text

# print(morse_encode("hello! my name is LinJiang"))
# print(morse_decode(r"--.\-..\-.-\-.-\-.\-.-.--\\\.-..\-..-\\\--\----.\.-..\-..\\\....\.-.\\\-.-\....\--\..\....\----.\--\..-."))
