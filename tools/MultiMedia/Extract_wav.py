import os
import sys
from config import ffmpeg_path


def Extract_wav(video, output):
    null = "NUL 2>&1" if sys.platform == "win32" else "/dev/null 2>&1"
    os.system(f'"{ffmpeg_path}" -i {video} -vn {output} -nostdin > {null}')

    return
