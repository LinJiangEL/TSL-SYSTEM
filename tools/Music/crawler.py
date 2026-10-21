#  Copyright (c) 2025-2026. L.J.Afres, All rights reserved.

"""网络音乐爬虫。

从公开的网络曲库中检索音乐，并把选定的音乐下载到本地
tools/Music/Musics 目录，供 'execute Music' 的点歌台和终端的 music
指令使用。

目前支持两个来源：
    netease —— 检索网易云音乐的公开曲库，下载免费试听音源；
    kugou   —— 检索酷狗音乐的公开曲库，下载免费音源。
受版权限制，部分歌曲只能检索到翻唱或试听版本，下载失败时会给出提示。
"""

import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from prettytable import PrettyTable
from tools.Music.library import get_library, duration_text

MUSIC_SOURCES = ('netease', 'kugou')
NETEASE_SEARCH_API = 'https://music.163.com/api/search/get/web'
NETEASE_PLAY_API = 'https://music.163.com/song/media/outer/url?id={0}.mp3'
KUGOU_SEARCH_API = 'http://mobilecdn.kugou.com/api/v3/search/song'
KUGOU_TRACKER_API = 'http://trackercdn.kugou.com/i/v2/'
KUGOU_TRACKER_KEY = 'kgcloudv2'
DEFAULT_TIMEOUT = 15
DEFAULT_LIMIT = 10
CHUNK_SIZE = 64 * 1024
MIN_MUSIC_SIZE = 8192
INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')
CONTENT_TYPE_FORMATS = {'audio/mpeg': 'mp3',
                        'audio/mp3': 'mp3',
                        'audio/mp4': 'm4a',
                        'audio/x-m4a': 'm4a',
                        'audio/aac': 'aac',
                        'audio/flac': 'flac',
                        'audio/ogg': 'ogg'
                        }

_crawler = None


class CrawlerError(Exception):
    """网络爬虫抛出的错误，异常信息本身即为错误提示。"""


class OnlineTrack:
    """一首网络音乐。"""

    def __init__(self, source, identify, title, artist='Unknown', album='Unknown',
                 duration=None, fee=None):
        self.source = source
        self.identify = identify
        self.title = title if title else 'Unknown'
        self.artist = artist if artist else 'Unknown'
        self.album = album if album else 'Unknown'
        self.duration = duration
        self.fee = fee

    def label(self):
        """返回用于显示的曲目名称。"""
        return f'{self.title} - {self.artist}' if self.artist != 'Unknown' else self.title

    def duration_text(self):
        """把曲目时长格式化为 mm:ss。"""
        return duration_text(self.duration)


class MusicCrawler:
    """网络音乐爬虫。"""

    def __init__(self, sources=MUSIC_SOURCES, timeout=DEFAULT_TIMEOUT, limit=DEFAULT_LIMIT):
        self.sources = tuple(sources)
        self.timeout = timeout
        self.limit = limit
        self.results = []

    def search(self, keyword, limit=None):
        """检索所有来源，返回去重后的网络曲目列表。"""
        keyword = keyword.strip()
        if not keyword:
            return []
        limit = limit or self.limit
        tracks = []
        errors = []
        for source in self.sources:
            search_method = getattr(self, '_search_' + source, None)
            if search_method is None:
                continue
            try:
                tracks.extend(search_method(keyword, limit))
            except CrawlerError as error:
                errors.append(str(error))
        unique_tracks = []
        seen = set()
        for track in tracks:
            key = (track.title.lower(), track.artist.lower())
            if key in seen:
                continue
            seen.add(key)
            unique_tracks.append(track)
        self.results = unique_tracks
        if not unique_tracks and errors:
            raise CrawlerError(errors[-1])
        return unique_tracks

    def resolve(self, identify):
        """把序号或关键字解析为网络曲目列表。"""
        identify = identify.strip()
        if identify.isdigit():
            index = int(identify)
            return [self.results[index - 1]] if 1 <= index <= len(self.results) else []
        return self.search(identify)

    def table(self, tracks):
        """把网络曲目列表格式化为表格。"""
        table = PrettyTable(['Index', 'Title', 'Artist', 'Album', 'Duration', 'Source'])
        for position, track in enumerate(tracks):
            table.add_row([position + 1,
                           track.title,
                           track.artist,
                           track.album,
                           track.duration_text(),
                           track.source
                           ]
                          )
        table.align = 'l'
        table.title = 'Online Music'
        return str(table)

    def get_url(self, track):
        """解析曲目的音源地址。"""
        if track.source == 'netease':
            return NETEASE_PLAY_API.format(track.identify)
        if track.source == 'kugou':
            key = hashlib.md5((track.identify + KUGOU_TRACKER_KEY).encode('utf-8')).hexdigest()
            query = urllib.parse.urlencode({'key': key,
                                            'hash': track.identify,
                                            'br': 'hq',
                                            'appid': '1005',
                                            'pid': '2',
                                            'cmd': '25',
                                            'behavior': 'play'
                                            }
                                           )
            data = self._load_json(f'{KUGOU_TRACKER_API}?{query}')
            urls = data.get('url')
            if isinstance(urls, str):
                urls = [urls]
            if not urls:
                raise CrawlerError(f"the music is not available in source '{track.source}' "
                                   f"(copyright restriction)."
                                   )
            return urls[0]
        raise CrawlerError(f"unknown music source '{track.source}'.")

    def download(self, track, directory=None):
        """把曲目下载到本地目录，返回下载后的文件路径。"""
        directory = directory or get_library().directory
        os.makedirs(directory, exist_ok=True)
        url = self.get_url(track)
        path = self._unique_path(os.path.join(directory, self._filename(track, url)))
        part_path = path + '.part'
        request = urllib.request.Request(url, headers=self._headers(track))
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                content_type = (response.headers.get('Content-Type') or '').lower()
                if not self._is_audio(content_type):
                    raise CrawlerError('the music server did not return an audio stream '
                                       '(the music may be copyright restricted).'
                                       )
                size = 0
                with open(part_path, 'wb') as musicfile:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        size += len(chunk)
                        musicfile.write(chunk)
                if size < MIN_MUSIC_SIZE:
                    raise CrawlerError('the downloaded music is empty.')
        except CrawlerError:
            if os.path.exists(part_path):
                os.remove(part_path)
            raise
        except urllib.error.HTTPError as error:
            raise CrawlerError(f'the music server returned HTTP {error.code}, '
                               f'the music may be copyright restricted.'
                               )
        except urllib.error.URLError as error:
            raise CrawlerError(f'the music server cannot be reached: {error.reason}.')
        except OSError as error:
            if os.path.exists(part_path):
                os.remove(part_path)
            raise CrawlerError(f'the music cannot be written to the local disk: {error}.')
        else:
            os.replace(part_path, path)
            return path

    def _search_netease(self, keyword, limit):
        """检索网易云音乐的公开曲库。"""
        query = urllib.parse.urlencode({'s': keyword, 'type': 1, 'limit': limit, 'offset': 0})
        data = self._load_json(f'{NETEASE_SEARCH_API}?{query}',
                               {'Referer': 'https://music.163.com/'}
                               )
        songs = (data.get('result') or {}).get('songs') or []
        tracks = []
        for song in songs:
            artists = [artist.get('name', '') for artist in song.get('artists') or []]
            album = (song.get('album') or {}).get('name', 'Unknown')
            duration = song.get('duration')
            tracks.append(OnlineTrack('netease',
                                      str(song.get('id')),
                                      song.get('name', 'Unknown'),
                                      ' / '.join([artist for artist in artists if artist]) or 'Unknown',
                                      album,
                                      duration / 1000.0 if duration else None,
                                      song.get('fee')
                                      )
                          )
        return tracks

    def _search_kugou(self, keyword, limit):
        """检索酷狗音乐的公开曲库。"""
        query = urllib.parse.urlencode({'format': 'json', 'keyword': keyword, 'page': 1, 'pagesize': limit})
        data = self._load_json(f'{KUGOU_SEARCH_API}?{query}')
        songs = (data.get('data') or {}).get('info') or []
        tracks = []
        for song in songs:
            if not song.get('hash'):
                continue
            tracks.append(OnlineTrack('kugou',
                                      song.get('hash'),
                                      song.get('songname', 'Unknown'),
                                      song.get('singername', 'Unknown'),
                                      song.get('album_name', 'Unknown'),
                                      song.get('duration')
                                      )
                          )
        return tracks

    def _load_json(self, url, headers=None):
        """请求并解析音乐服务器返回的 JSON 数据。"""
        request = urllib.request.Request(url, headers=self._headers(None, headers))
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            raise CrawlerError(f'the music server returned HTTP {error.code}.')
        except urllib.error.URLError as error:
            raise CrawlerError(f'the music server cannot be reached: {error.reason}.')
        except OSError as error:
            raise CrawlerError(f'the music server cannot be reached: {error}.')
        try:
            return json.loads(body.decode('utf-8', 'ignore'))
        except ValueError:
            raise CrawlerError('the music server returned invalid data.')

    def _headers(self, track, extra=None):
        """构造请求头，部分音乐服务器需要 Referer。"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        if track is not None and track.source == 'netease':
            headers['Referer'] = 'https://music.163.com/'
        if extra:
            headers.update(extra)
        return headers

    def _filename(self, track, url):
        """根据曲目信息与音源地址生成文件名。"""
        extension = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower().lstrip('.')
        if extension not in ('mp3', 'm4a', 'aac', 'flac', 'ogg', 'wav', 'wma'):
            extension = 'mp3'
        name = track.title if track.artist == 'Unknown' else f'{track.artist} - {track.title}'
        name = INVALID_FILENAME_CHARS.sub('_', name).strip()[:120]
        return f'{name}.{extension}'

    def _unique_path(self, path):
        """避免覆盖同名的本地音乐。"""
        if not os.path.exists(path):
            return path
        root, extension = os.path.splitext(path)
        index = 2
        while os.path.exists(f'{root} ({index}){extension}'):
            index += 1
        return f'{root} ({index}){extension}'

    def _is_audio(self, content_type):
        """判断响应是否为音频流。"""
        return (content_type.startswith('audio/')
                or content_type.startswith('application/octet-stream')
                or 'mpeg' in content_type
                )


def get_crawler():
    """返回全局音乐爬虫单例。"""
    global _crawler
    if _crawler is None:
        _crawler = MusicCrawler()
    return _crawler
