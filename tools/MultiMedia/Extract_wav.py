import os
from config import null, ffmpeg_path


def Extract_wav(video, output):
    os.system(f'"{ffmpeg_path}" -i {video} -vn {output} -nostdin > {null}')
    return
