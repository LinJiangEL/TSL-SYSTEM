#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os
from config import null, ffmpeg_path


def Extract_wav(video, output):
    os.system(f'"{ffmpeg_path}" -i {video} -vn {output} -nostdin > {null}')
    return
