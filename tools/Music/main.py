#  Copyright (c) 2025-2026. L.J.Afres, All rights reserved.
from tools.__built_in__ import style

"""TSL-SYSTEM Music Module.

点歌台的在线检索与下载：search 爬取网络曲库、get 下载选定的音乐到本地、
info 查看曲目信息；queue/play/pause/stop 与终端的 music 指令共享同一个
后台播放器。
"""

import os
from termcolor import colored
from config import Tools_DIR, PageReader
from sysmgr import TempManager
from tools.__built_in__.helptool import HelpTool
from tools.__built_in__.IOProcessor import read_input
from tools.Music.library import get_library, duration_text, size_text
from tools.Music.crawler import get_crawler, CrawlerError
from tools.Music.player import get_player, PlaybackError

musicdir = os.path.join(Tools_DIR, 'Music')


def _print_tracks(library, tracks, queue=False):
    """打印本地曲目表格。"""
    if not tracks:
        print('MusicNotFoundError:no local music was found.\n')
        return
    if queue:
        print(library.table(tracks, queue=True), '\n')
        return
    all_tracks = library.scan()
    indexes = [all_tracks.index(track) + 1 for track in tracks]
    print(library.table(tracks, indexes=indexes), '\n')


def _print_online(crawler, tracks):
    """打印网络曲目表格。"""
    if not tracks:
        print('MusicNotFoundError:no online music was found.\n')
        return
    print(crawler.table(tracks), '\n')


def _print_info(track):
    """打印一首本地曲目的详细信息。"""
    print(f'Title   : {track.title}\n'
          f'Artist  : {track.artist}\n'
          f'Album   : {track.album}\n'
          f'Format  : {track.format}\n'
          f'Size    : {size_text(track.size)}\n'
          f'Duration: {track.duration_text()}\n'
          f'Path    : {track.path}\n'
          )


def _print_online_info(track):
    """打印一首网络曲目的详细信息。"""
    print(f'Title   : {track.title}\n'
          f'Artist  : {track.artist}\n'
          f'Album   : {track.album}\n'
          f'Duration: {track.duration_text()}\n'
          f'Source  : {track.source}\n'
          f'Fee     : {track.fee if track.fee is not None else "unknown"}\n'
          )


def _resolve_local(library, identify):
    """解析序号或关键字，返回匹配的本地曲目列表。"""
    tracks = library.resolve(identify)
    if not tracks:
        print(f"MusicNotFoundError:no music matched '{identify}'.\n")
    return tracks


def _resolve_online(crawler, identify):
    """解析序号或关键字，返回匹配的网络曲目列表。"""
    try:
        tracks = crawler.resolve(identify)
    except CrawlerError as error:
        print(f'CrawlerError:{error}\n')
        return []
    if not tracks:
        print(f"MusicNotFoundError:no music matched '{identify}'.\n")
    return tracks


def _download(crawler, library, track):
    """下载一首网络曲目，成功时返回文件路径。"""
    try:
        path = crawler.download(track)
    except CrawlerError as error:
        print(f'CrawlerError:{error}\n')
        return None
    print(f'Downloaded: {path}\n')
    library.scan(refresh=True)
    return path


def _queue_downloaded(library, player, path):
    """把刚刚下载的本地音乐加入点歌单。"""
    for track in library.scan():
        if os.path.abspath(track.path) == os.path.abspath(path):
            position = player.add(track.as_dict())
            print(f"Queued: {track.label()} (position {position}).\n")
            return


def run():
    style.banner('TSL-SYSTEM Music Module', width=37)
    print('')

    library = get_library()
    player = get_player()
    crawler = get_crawler()

    while True:
        try:
            command = read_input(style.prompt('(music)'), 'terminal', strip=True)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if command == '':
            continue
        elif command == '@exit':
            print()
            break
        elif command == '@help':
            HelpTool(musicdir, PageReader, 'music')
            continue
        elif command == '@flush':
            TempManager().Flush('Music Module')
            continue

        maincmd = command.split(' ', maxsplit=1)[0]
        argument = command.split(' ', maxsplit=1)[1].strip() if ' ' in command else ''

        if maincmd == 'search':
            if argument == '':
                print("CommandUsageError:incorrectly search usage, please input 'search KEYWORD'.\n")
                continue
            try:
                tracks = crawler.search(argument)
            except CrawlerError as error:
                print(f'CrawlerError:{error}\n')
                continue
            if not tracks:
                print(f"MusicNotFoundError:no online music matched '{argument}'.\n")
                continue
            _print_online(crawler, tracks)
            print("Input 'get INDEX' to download the selected music.\n")

        elif maincmd == 'list':
            _print_tracks(library, library.scan())

        elif maincmd == 'local':
            if argument == '':
                print("CommandUsageError:incorrectly local usage, please input 'local KEYWORD'.\n")
                continue
            _print_tracks(library, library.search(argument))

        elif maincmd == 'get':
            if argument == '':
                print("CommandUsageError:incorrectly get usage, please input 'get INDEX/KEYWORD'.\n")
                continue
            tracks = _resolve_online(crawler, argument)
            if not tracks:
                continue
            if len(tracks) > 1:
                print('Multiple tracks matched, please point out one of them by its index:')
                _print_online(crawler, tracks)
                continue
            path = _download(crawler, library, tracks[0])
            if path:
                _queue_downloaded(library, player, path)
                print("Input 'play' to start playing, or 'music play' in the terminal.\n")

        elif maincmd == 'info':
            if argument == '':
                print("CommandUsageError:incorrectly info usage, please input 'info INDEX/KEYWORD'.\n")
                continue
            tracks = _resolve_online(crawler, argument)
            if not tracks:
                continue
            if len(tracks) > 1:
                print('Multiple tracks matched, please point out one of them by its index:')
                _print_online(crawler, tracks)
                continue
            _print_online_info(tracks[0])

        elif maincmd == 'queue':
            queue = player.queue()
            if not queue:
                print('MusicQueueWarning:the playlist is empty, input \'get INDEX\' to add music.\n')
                continue
            print(library.table(queue, queue=True), '\n')

        elif maincmd == 'drop':
            if argument == '' or not argument.isdigit():
                print("CommandUsageError:incorrectly drop usage, please input 'drop INDEX'.\n")
                continue
            if player.remove(int(argument)):
                print(f'Removed the music at position {argument} from the playlist.\n')
            else:
                print(f'IndexError:the playlist has no music at position {argument}.\n')

        elif maincmd == 'clear':
            player.clear()
            print('The playlist has been cleared.\n')

        elif maincmd == 'dir':
            print(f'Music directory: {library.directory}\n')

        elif maincmd in ['play', 'stop', 'pause']:
            try:
                if maincmd == 'play':
                    if argument:
                        tracks = _resolve_local(library, argument)
                        if not tracks:
                            continue
                        if len(tracks) > 1:
                            print('Multiple tracks matched, please point out one of them by its index:')
                            _print_tracks(library, tracks)
                            continue
                        print(player.play_song(tracks[0]), '\n')
                    else:
                        print(player.play(library.scan()), '\n')
                elif maincmd == 'stop':
                    print(player.stop(), '\n')
                else:
                    print(player.pause(), '\n')
            except PlaybackError as error:
                print(f'PlaybackError:{error}\n')

        else:
            print(f"NameError:command '{maincmd}' is not defined in Music Module.\n")
