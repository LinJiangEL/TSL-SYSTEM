#  Copyright (c) 2025-2026. L.J.Afres, All rights reserved.

"""终端后台音乐播放器。

Windows 下使用系统自带的 MCI 接口异步播放，Linux 下使用后台 ffplay
进程播放。播放由驱动或子进程完成，播放指令发出后立即返回，所以不会
阻塞终端；终端只需要通过 play/stop/pause 控制播放状态。

MCI 设备只能由打开它的线程操作，所以播放接口由后台引擎线程统一创建
和调用，点歌、暂停、继续、停止等指令都经引擎线程转发执行。
"""

import os
import sys
import json
import time
import atexit
import queue
import shutil
import signal
import subprocess
import threading
from loguru import logger
from config import SYSTEM_DIR
from tools.Music.library import duration_text

PLAYLIST_FILE = os.path.join(SYSTEM_DIR, 'Temp/MusicPlaylist.json')
MUSIC_STATE_FILE = os.path.join(SYSTEM_DIR, 'Temp/MusicState.json')
MUSIC_CONTROL_FILE = os.path.join(SYSTEM_DIR, 'Temp/MusicControl.json')
MCI_ALIAS = 'tslmusic'


class PlaybackError(Exception):
    """播放失败。"""


def _process_alive(pid):
    """判断一个进程是否仍然存活。"""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if sys.platform == 'win32':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            exitcode = ctypes.c_ulong(0)
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exitcode)):
                return False
            return exitcode.value == 259
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_json(path):
    """读取 JSON 文件，文件不存在或损坏时返回 None。"""
    try:
        with open(path, 'r', encoding='utf-8') as jsonfile:
            return json.load(jsonfile)
    except (OSError, ValueError):
        return None


def _write_json(path, content):
    """原子地写入 JSON 文件。"""
    temppath = '%s.tmp' % path
    try:
        with open(temppath, 'w', encoding='utf-8') as jsonfile:
            json.dump(content, jsonfile, ensure_ascii=False)
        os.replace(temppath, path)
    except OSError as error:
        logger.warning("failed to write the music state file because %s." % error)


def playback_state():
    """返回全局播放状态，已经退出的进程留下的状态会被忽略。"""
    state = _read_json(MUSIC_STATE_FILE)
    if not isinstance(state, dict):
        return None
    if state.get('status') in ('playing', 'paused') and not _process_alive(state.get('pid')):
        return None
    return state


class MusicBackend:
    """播放接口。"""

    name = 'none'

    def play(self, path):
        raise NotImplementedError

    def pause(self):
        raise NotImplementedError

    def resume(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def mode(self):
        """返回 playing、paused 或 stopped。"""
        raise NotImplementedError


class MCIPlayer(MusicBackend):
    """Windows MCI 播放接口。"""

    name = 'mci'

    def __init__(self):
        import ctypes
        self._ctypes = ctypes
        try:
            self._winmm = ctypes.windll.winmm
        except AttributeError as error:
            raise PlaybackError('MCI is unavailable on this platform.') from error
        self._send_string = self._winmm.mciSendStringW
        self._get_error = self._winmm.mciGetErrorStringW
        self._opened = False
        self._paused = False

    def _send(self, command):
        """向 MCI 发送指令并返回结果字符串。"""
        buffer = self._ctypes.create_unicode_buffer(256)
        result = self._send_string(command, buffer, 256, None)
        if result:
            error_text = self._ctypes.create_unicode_buffer(512)
            self._get_error(result, error_text, 512)
            raise PlaybackError('MCI error %s: %s' % (result, error_text.value.strip()))
        return buffer.value

    def _close(self):
        if self._opened:
            try:
                self._send('close %s' % MCI_ALIAS)
            except PlaybackError:
                pass
            self._opened = False
        self._paused = False

    def play(self, path):
        self._close()
        try:
            self._send('open "%s" alias %s' % (path, MCI_ALIAS))
            self._opened = True
            self._send('play %s' % MCI_ALIAS)
        except PlaybackError:
            self._close()
            raise

    def pause(self):
        if self._opened and not self._paused:
            self._send('pause %s' % MCI_ALIAS)
            self._paused = True

    def resume(self):
        if self._opened and self._paused:
            self._send('resume %s' % MCI_ALIAS)
            self._paused = False

    def stop(self):
        self._close()

    def mode(self):
        if not self._opened:
            return 'stopped'
        try:
            return self._send('status %s mode' % MCI_ALIAS)
        except PlaybackError:
            return 'stopped'


class FFplayPlayer(MusicBackend):
    """Linux ffplay 后台播放接口。"""

    name = 'ffplay'

    def __init__(self):
        self._process = None
        self._paused = False
        self._executable = shutil.which('ffplay')

    def play(self, path):
        if not self._executable:
            raise PlaybackError("'ffplay' was not found, please install ffmpeg first.")
        self.stop()
        self._process = subprocess.Popen([self._executable, '-nodisp', '-autoexit', '-loglevel', 'quiet', path],
                                         stdin=subprocess.DEVNULL,
                                         stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL
                                         )
        self._paused = False

    def pause(self):
        if self._process and self._process.poll() is None and not self._paused:
            os.kill(self._process.pid, signal.SIGSTOP)
            self._paused = True

    def resume(self):
        if self._process and self._process.poll() is None and self._paused:
            os.kill(self._process.pid, signal.SIGCONT)
            self._paused = False

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=1)
        self._process = None
        self._paused = False

    def mode(self):
        if self._process is None or self._process.poll() is not None:
            return 'stopped'
        return 'paused' if self._paused else 'playing'


def create_backend():
    """根据当前平台创建播放接口。"""
    if sys.platform == 'win32':
        return MCIPlayer()
    if sys.platform == 'linux':
        return FFplayPlayer()
    raise PlaybackError("the platform '%s' does not support music playback." % sys.platform)


class MusicPlayer:
    """后台音乐播放器，负责点歌单与播放状态。"""

    def __init__(self):
        self._lock = threading.RLock()
        self._backend = None
        self._queue = []
        self._index = 0
        self._current = None
        self._paused = False
        self._started_at = 0
        self._watcher = None
        self._watcher_stop = threading.Event()
        self._engine = None
        self._engine_queue = queue.Queue()
        self._engine_lock = threading.Lock()
        self._last_control_nonce = None
        self._load_playlist()

    def _ensure_engine(self):
        """确保后台引擎线程已经启动，播放接口只在引擎线程中创建和使用。"""
        if self._engine is not None and self._engine.is_alive():
            return
        self._engine = threading.Thread(target=self._engine_loop, name='TSL-Music-Engine', daemon=True)
        self._engine.start()

    def _engine_loop(self):
        """引擎线程：创建播放接口并执行所有播放指令。"""
        while True:
            request = self._engine_queue.get()
            if request is None:
                break
            method, arguments, box, event = request
            try:
                if self._backend is None:
                    self._backend = create_backend()
                box['value'] = getattr(self._backend, method)(*arguments)
            except BaseException as error:
                box['error'] = error
            finally:
                event.set()

    def _backend_call(self, method, *arguments):
        """在引擎线程中调用播放接口，MCI 设备只能由打开它的线程操作。"""
        with self._engine_lock:
            self._ensure_engine()
        event = threading.Event()
        box = {}
        self._engine_queue.put((method, arguments, box, event))
        if not event.wait(10):
            raise PlaybackError('the music backend did not respond in time.')
        if 'error' in box:
            raise box['error']
        return box.get('value')

    def _load_playlist(self):
        """从断点文件恢复点歌单。"""
        if not os.path.exists(PLAYLIST_FILE):
            return
        try:
            with open(PLAYLIST_FILE, 'r', encoding='utf-8') as playlistfile:
                playlist = json.load(playlistfile)
            queue = [track for track in playlist.get('queue', [])
                     if isinstance(track, dict) and os.path.exists(track.get('path', ''))
                     ]
            index = playlist.get('index', 0)
            if isinstance(index, int) and 0 <= index < len(queue):
                self._index = index
            self._queue = queue
        except (OSError, ValueError, TypeError):
            logger.warning("failed to read the music playlist, a new playlist will be used.")
            self._queue = []
            self._index = 0

    def _save_playlist(self):
        """保存点歌单。"""
        try:
            with open(PLAYLIST_FILE, 'w', encoding='utf-8') as playlistfile:
                json.dump({'queue': self._queue, 'index': self._index}, playlistfile, ensure_ascii=False, indent=2)
        except OSError as error:
            logger.warning("failed to save the music playlist because %s." % error)

    def _local_status(self):
        """返回本播放器自身的播放状态。"""
        if self._current is None:
            return 'stopped'
        return 'paused' if self._paused else 'playing'

    def _write_state(self, control_nonce=None, control_result=None):
        """把播放状态写入全局状态文件，供其它终端进程查询与控制。"""
        track = self._current or {}
        _write_json(MUSIC_STATE_FILE, {'pid': os.getpid(),
                                       'status': self._local_status(),
                                       'path': track.get('path', ''),
                                       'title': track.get('title', ''),
                                       'artist': track.get('artist', 'Unknown'),
                                       'duration': track.get('duration'),
                                       'started_at': self._started_at,
                                       'updated_at': time.time(),
                                       'control_nonce': control_nonce,
                                       'control_result': control_result
                                       }
                    )

    def _recover_state(self, state):
        """本进程丢失播放状态时按全局状态文件重新同步。"""
        self._current = {'path': state.get('path', ''),
                         'title': state.get('title', ''),
                         'artist': state.get('artist', 'Unknown'),
                         'duration': state.get('duration')
                         }
        self._paused = state.get('status') == 'paused'
        self._started_at = state.get('started_at', time.time())
        self._start_watcher()

    def _apply_control(self):
        """处理其它终端进程发来的控制指令，只有播放进程会执行。"""
        if self._current is None:
            return
        control = _read_json(MUSIC_CONTROL_FILE)
        if not isinstance(control, dict):
            return
        action = control.get('action')
        nonce = control.get('nonce')
        if not action or nonce == self._last_control_nonce or control.get('issuer') == os.getpid():
            return
        result = 'ignored'
        try:
            if action == 'stop':
                if self._backend is not None:
                    self._backend_call('stop')
                self._current = None
                self._paused = False
                result = 'stopped'
                logger.info("Music stopped by another terminal.")
            elif action == 'pause' and not self._paused:
                self._backend_call('pause')
                self._paused = True
                result = 'paused'
                logger.info("Music paused by another terminal.")
            elif action == 'resume' and self._paused:
                self._backend_call('resume')
                self._paused = False
                result = 'resumed'
                logger.info("Music resumed by another terminal.")
        except PlaybackError as error:
            result = 'failed'
            logger.warning("failed to apply the music control '%s' because %s." % (action, error))
        self._last_control_nonce = nonce
        self._write_state(control_nonce=nonce, control_result=result)

    def _control(self, action):
        """向持有播放状态的进程发送控制指令并等待应答。"""
        nonce = '%.6f' % time.time()
        _write_json(MUSIC_CONTROL_FILE, {'action': action,
                                         'issued_at': time.time(),
                                         'issuer': os.getpid(),
                                         'nonce': nonce
                                         }
                    )
        deadline = time.time() + 3
        while time.time() < deadline:
            state = _read_json(MUSIC_STATE_FILE)
            if isinstance(state, dict) and state.get('control_nonce') == nonce:
                return state
            time.sleep(0.05)
        raise PlaybackError("the process which is playing music did not respond in time.")

    def _remote_pause(self):
        """没有本地播放时，暂停或继续其它进程的播放。"""
        state = playback_state()
        if state is None or state.get('status') not in ('playing', 'paused'):
            raise PlaybackError('no music is playing now.')
        if state.get('pid') == os.getpid():
            self._recover_state(state)
            return self.pause()
        action = 'resume' if state.get('status') == 'paused' else 'pause'
        state = self._control(action)
        prefix = 'Resumed' if action == 'resume' else 'Paused'
        return '%s: %s - %s (%s)' % (prefix, state.get('title', ''), state.get('artist', 'Unknown'),
                                     duration_text(state.get('duration')))

    def queue(self):
        with self._lock:
            return list(self._queue)

    def add(self, track):
        """点歌：把曲目加入点歌单，返回它的位置。"""
        with self._lock:
            for position, queued in enumerate(self._queue):
                if os.path.normcase(queued.get('path', '')) == os.path.normcase(track.get('path', '')):
                    return position + 1
            self._queue.append(track)
            self._save_playlist()
            logger.info("Music added to the playlist. [MUSICINFO:('%s')]" % track.get('path'))
            return len(self._queue)

    def remove(self, position):
        """从点歌单中删除指定位置的曲目。"""
        with self._lock:
            if position < 1 or position > len(self._queue):
                return False
            removed = self._queue.pop(position - 1)
            if position - 1 < self._index:
                self._index -= 1
            if not self._queue:
                self._index = 0
            self._save_playlist()
            logger.info("Music removed from the playlist. [MUSICINFO:('%s')]" % removed.get('path'))
            return True

    def clear(self):
        """清空点歌单。"""
        with self._lock:
            self._queue = []
            self._index = 0
            self._save_playlist()

    def _start_watcher(self):
        if self._watcher is not None and self._watcher.is_alive():
            return
        self._watcher = threading.Thread(target=self._watch, name='TSL-Music-Watcher', daemon=True)
        self._watcher.start()

    def _watch(self):
        """后台监视播放状态，当前曲目结束后自动播放点歌单中的下一首。"""
        while not self._watcher_stop.wait(0.2):
            with self._lock:
                self._apply_control()
                if self._current is None or self._paused:
                    continue
                if self._backend is None:
                    continue
                if time.time() - self._started_at < 2:
                    continue
                if self._backend_call('mode') != 'stopped':
                    continue
                self._play_next()

    def _play_track(self, index):
        """播放点歌单中指定位置的曲目。"""
        track = self._queue[index]
        self._backend_call('play', track['path'])
        self._index = index
        self._current = track
        self._paused = False
        self._started_at = time.time()
        self._start_watcher()
        self._save_playlist()
        self._write_state()
        logger.info("Music started. [MUSICINFO:('%s')]" % track.get('path'))
        return self._now_playing('Now playing')

    def _play_next(self):
        """播放点歌单中的下一首，播放完毕时停止。"""
        if self._index + 1 < len(self._queue):
            return self._play_track(self._index + 1)
        self._finish()
        return 'The playlist has been finished.'

    def _finish(self):
        if self._backend is not None:
            self._backend_call('stop')
        self._current = None
        self._paused = False
        self._save_playlist()
        self._write_state()

    def _now_playing(self, prefix):
        track = self._current
        return '%s: %s - %s (%s)' % (prefix, track.get('title', ''), track.get('artist', 'Unknown'),
                                     duration_text(track.get('duration'))
                                     )

    def play(self, tracks=None):
        """开始或继续播放，tracks 为空点歌单时作为默认播放列表。"""
        with self._lock:
            state = playback_state()
            if state is not None and state.get('pid') != os.getpid() \
                    and state.get('status') in ('playing', 'paused'):
                try:
                    self._control('stop')
                except PlaybackError as error:
                    raise PlaybackError('cannot stop the music played by another TSL-SYSTEM process: %s' % error)
            if self._current is not None and self._paused:
                self._backend_call('resume')
                self._paused = False
                self._write_state()
                logger.info("Music resumed.")
                return self._now_playing('Resumed')
            if self._current is not None:
                if self._backend_call('mode') == 'playing':
                    return self._now_playing('Already playing')
                if time.time() - self._started_at >= 2:
                    return self._play_next()
            if not self._queue and tracks:
                self._queue = [track.as_dict() for track in tracks]
                self._index = 0
                self._save_playlist()
            if not self._queue:
                raise PlaybackError('no local music was found, please put music files into '
                                    'the tools/Music/Musics directory first.')
            if self._current is None and self._index >= len(self._queue):
                self._index = 0
            return self._play_track(self._index)

    def play_song(self, track):
        """点播一首曲目并立即播放。"""
        with self._lock:
            position = self.add(track.as_dict()) - 1
            self._index = position
            return self._play_track(position)

    def pause(self):
        """暂停或继续播放，也可以控制其它终端进程正在播放的音乐。"""
        with self._lock:
            if self._current is None:
                return self._remote_pause()
            if self._paused:
                self._backend_call('resume')
                self._paused = False
                self._write_state()
                logger.info("Music resumed.")
                return self._now_playing('Resumed')
            self._backend_call('pause')
            self._paused = True
            self._write_state()
            logger.info("Music paused.")
            return self._now_playing('Paused')

    def stop(self):
        """停止播放，点歌单保持不变；也可以停止其它终端进程的播放。"""
        with self._lock:
            if self._current is None:
                state = playback_state()
                if state is None or state.get('status') not in ('playing', 'paused'):
                    return 'Playback stopped.'
                if state.get('pid') == os.getpid():
                    self._recover_state(state)
                else:
                    self._control('stop')
                    return 'Playback stopped.'
            if self._backend is not None:
                self._backend_call('stop')
            was_playing = self._current is not None
            self._current = None
            self._paused = False
            self._write_state()
            if was_playing:
                logger.info("Music stopped.")
            return 'Playback stopped.'

    def status(self):
        """返回当前播放状态，包括其它终端进程正在播放的音乐。"""
        with self._lock:
            status = self._local_status()
            if status != 'stopped':
                return status
            state = playback_state()
            if state is not None and state.get('status') in ('playing', 'paused'):
                return state.get('status')
            return 'stopped'


_player = None


def _shutdown():
    """退出系统时停止本进程的后台播放，不影响其它进程播放的音乐。"""
    if _player is not None and _player._current is not None:
        try:
            _player.stop()
        except PlaybackError:
            pass


def get_player():
    """返回全局后台播放器单例。"""
    global _player
    if _player is None:
        _player = MusicPlayer()
        atexit.register(_shutdown)
    return _player
