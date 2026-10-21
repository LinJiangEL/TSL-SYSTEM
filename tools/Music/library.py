#  Copyright (c) 2025-2026. L.J.Afres, All rights reserved.

"""本地音乐库。

扫描 TSL-SYSTEM 的本地音乐目录，读取音乐文件的基本信息，并为
'execute Music' 中的 search/get/info 指令提供检索、定位与格式化功能。

音乐文件默认存放在 tools/Music/Musics 目录下，可以用环境变量
TSL_MUSIC_DIR 指定其它目录。
"""

import os
import wave
from prettytable import PrettyTable

MUSIC_FORMATS = ('.mp3', '.wav', '.wma', '.flac', '.m4a', '.ogg', '.aac')
MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Musics')

_library = None


class Track:
    """一首本地音乐。"""

    def __init__(self, path, title=None, artist=None, album=None, duration=None):
        self.path = os.path.abspath(path)
        self.format = os.path.splitext(self.path)[1].lower().lstrip('.')
        self.size = os.path.getsize(self.path)
        self.title = title if title else os.path.splitext(os.path.basename(self.path))[0]
        self.artist = artist if artist else 'Unknown'
        self.album = album if album else 'Unknown'
        self.duration = duration

    def as_dict(self):
        """把音乐信息转换为可以写入点歌单的字典。"""
        return {'path': self.path,
                'title': self.title,
                'artist': self.artist,
                'album': self.album,
                'duration': self.duration,
                'format': self.format
                }

    def label(self):
        """返回用于显示的曲目名称。"""
        return f'{self.title} - {self.artist}' if self.artist != 'Unknown' else self.title

    def duration_text(self):
        """把曲目时长格式化为 mm:ss。"""
        return duration_text(self.duration)


def duration_text(duration):
    """把秒数格式化为 mm:ss。"""
    if not duration:
        return '--:--'
    seconds = int(round(duration))
    return '%02d:%02d' % (seconds // 60, seconds % 60)


def size_text(size):
    """把字节数格式化为易读的文件大小。"""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return '%.1f %s' % (size, unit) if unit != 'B' else '%d B' % size
        size /= 1024.0


def read_wav_duration(path):
    """读取 WAV 文件的时长（秒）。"""
    try:
        with wave.open(path, 'rb') as wavfile:
            framerate = wavfile.getframerate()
            if not framerate:
                return None
            return wavfile.getnframes() / float(framerate)
    except (wave.Error, EOFError, OSError):
        return None


def _decode_text(raw, encoding):
    """解码 ID3 文本。"""
    try:
        return raw.decode(encoding, 'ignore').strip('\x00').strip()
    except (LookupError, UnicodeDecodeError):
        return ''


def _id3v2_frames(path):
    """读取 ID3v2 标签中的标题、艺术家与专辑。"""
    tags = {}
    try:
        with open(path, 'rb') as musicfile:
            header = musicfile.read(10)
            if len(header) < 10 or header[0:3] != b'ID3':
                return tags
            size = (header[6] << 21) | (header[7] << 14) | (header[8] << 7) | header[9]
            body = musicfile.read(size)
    except OSError:
        return tags
    index = 0
    while index + 10 <= len(body):
        frame_id = body[index:index + 4]
        if not frame_id.strip(b'\x00'):
            break
        frame_size = int.from_bytes(body[index + 4:index + 8], 'big')
        if frame_size <= 0 or index + 10 + frame_size > len(body):
            break
        frame = body[index + 10:index + 10 + frame_size]
        index += 10 + frame_size
        if frame_id not in (b'TIT2', b'TPE1', b'TALB') or not frame:
            continue
        encoding = frame[0]
        encodings = {0: 'latin-1', 1: 'utf-16', 2: 'utf-16-be', 3: 'utf-8'}
        text = _decode_text(frame[1:], encodings.get(encoding, 'latin-1'))
        if frame_id == b'TIT2':
            tags['title'] = text
        elif frame_id == b'TPE1':
            tags['artist'] = text
        else:
            tags['album'] = text
    return tags


def _id3v1_frames(path):
    """读取 ID3v1 标签。"""
    try:
        with open(path, 'rb') as musicfile:
            musicfile.seek(-128, os.SEEK_END)
            tag = musicfile.read(128)
    except OSError:
        return {}
    if len(tag) < 128 or tag[0:3] != b'TAG':
        return {}
    return {'title': _decode_text(tag[3:33], 'latin-1'),
            'artist': _decode_text(tag[33:63], 'latin-1'),
            'album': _decode_text(tag[63:93], 'latin-1')
            }


def read_tags(path):
    """读取音乐文件的标签，没有标签时返回空字典。"""
    tags = {}
    if os.path.splitext(path)[1].lower() == '.mp3':
        tags = _id3v2_frames(path)
        if not tags:
            tags = _id3v1_frames(path)
    return {key: value for key, value in tags.items() if value}


def read_mp3_duration(path):
    """通过第一个 MPEG 帧估算 MP3 文件的时长（秒，适用于 CBR）。"""
    mpeg1_layer3 = (32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
    mpeg2_layer3 = (8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)
    samplerates = {3: (44100, 48000, 32000),
                   2: (22050, 24000, 16000),
                   0: (11025, 12000, 8000)}
    try:
        size = os.path.getsize(path)
        with open(path, 'rb') as musicfile:
            chunk = musicfile.read(256 * 1024)
    except OSError:
        return None
    start = chunk.find(b'\xff')
    while 0 <= start < len(chunk) - 4:
        header = chunk[start:start + 4]
        if (header[0] & 0xFF) == 0xFF and (header[1] & 0xE0) == 0xE0:
            version = (header[1] >> 3) & 0x03
            layer = (header[1] >> 1) & 0x03
            bitrate_index = (header[2] >> 4) & 0x0F
            samplerate_index = (header[2] >> 2) & 0x03
            bitrates = mpeg1_layer3 if version == 3 else mpeg2_layer3
            if layer == 1 and 1 <= bitrate_index <= 14 and samplerate_index < 3:
                bitrate = bitrates[bitrate_index - 1] * 1000
                return (size - start) * 8.0 / bitrate
        start = chunk.find(b'\xff', start + 1)
    return None


def read_track(path):
    """从音乐文件读取一首曲目的信息。"""
    tags = read_tags(path)
    extension = os.path.splitext(path)[1].lower()
    if extension == '.wav':
        duration = read_wav_duration(path)
    elif extension == '.mp3':
        duration = read_mp3_duration(path)
    else:
        duration = None
    return Track(path,
                 title=tags.get('title'),
                 artist=tags.get('artist'),
                 album=tags.get('album'),
                 duration=duration
                 )


class MusicLibrary:
    """本地音乐库。"""

    def __init__(self, directory=None):
        self.directory = os.path.abspath(directory or os.environ.get('TSL_MUSIC_DIR') or MUSIC_DIR)
        self._tracks = None

    def scan(self, refresh=False):
        """扫描音乐目录，返回按标题排序的曲目列表。"""
        if self._tracks is not None and not refresh:
            return self._tracks
        tracks = []
        if os.path.isdir(self.directory):
            for root, dirs, files in os.walk(self.directory):
                dirs[:] = [dirname for dirname in dirs
                           if not dirname.startswith('.') and dirname != '__pycache__']
                for filename in files:
                    if os.path.splitext(filename)[1].lower() in MUSIC_FORMATS:
                        try:
                            tracks.append(read_track(os.path.join(root, filename)))
                        except OSError:
                            continue
        tracks.sort(key=lambda track: (track.title.lower(), track.artist.lower()))
        self._tracks = tracks
        return tracks

    def search(self, keyword):
        """按标题、艺术家、专辑或文件名检索曲目。"""
        keyword = keyword.strip().lower()
        if not keyword:
            return []
        tracks = self.scan()
        return [track for track in tracks
                if keyword in track.title.lower()
                or keyword in track.artist.lower()
                or keyword in track.album.lower()
                or keyword in os.path.basename(track.path).lower()
                ]

    def resolve(self, identify):
        """把序号或关键字解析为曲目列表。"""
        identify = identify.strip()
        if identify.isdigit():
            tracks = self.scan()
            index = int(identify)
            return [tracks[index - 1]] if 1 <= index <= len(tracks) else []
        return self.search(identify)

    def table(self, tracks, indexes=None, queue=False):
        """把曲目列表格式化为表格。"""
        title = 'Playlist' if queue else 'Library'
        table = PrettyTable(['Index', 'Title', 'Artist', 'Duration', 'Format'])
        for position, track in enumerate(tracks):
            table.add_row([indexes[position] if indexes else position + 1,
                           track['title'] if isinstance(track, dict) else track.title,
                           track['artist'] if isinstance(track, dict) else track.artist,
                           duration_text(track['duration']) if isinstance(track, dict)
                           else track.duration_text(),
                           track['format'] if isinstance(track, dict) else track.format
                           ]
                          )
        table.align = 'l'
        table.title = title
        return str(table)


def get_library():
    """返回全局音乐库单例。"""
    global _library
    if _library is None:
        _library = MusicLibrary()
    return _library
