#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

from config import ffmpeg_path
from tools.__built_in__.external import run


def Extract_wav(video, output):
    run([ffmpeg_path, '-i', video, '-vn', output, '-nostdin'], silent=True)
    return
