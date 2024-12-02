#  Copyright (c) 2024. L.J.Afres, All rights reserved.
from pydub import AudioSegment

song = AudioSegment.from_mp3("song.mp3")
song.export("song.wav", format="wav")