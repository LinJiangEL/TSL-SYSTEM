#  Copyright (c) 2026. L.J.Afres, All rights reserved.

"""系统断点保护模块。

在系统运行过程中持续记录断点状态（当前用户、会话、最后一条命令等），
当系统因未捕获异常、键盘中断或意外终止而停止运行时，把详细堆栈写入
Temp/logs/breakpoint.log；系统下一次启动时会把上一次的中断信息报告给用户，
并写入系统日志，便于定位问题。

断点保护分为两层：
  · 终端命令级保护：单条命令抛出的异常会被记录并拦截，终端不会因此退出；
  · 进程级保护：未捕获异常、线程异常、退出钩子和致命信号都会留下断点记录。
"""

import os
import sys
import time
import atexit
import signal
import platform
import threading
import traceback
import faulthandler
from ast import literal_eval
from loguru import logger
from config import SYSTEM_DIR, SYSTEM_LOGPATH

BREAKPOINT_STATE_FILE = os.path.join(SYSTEM_DIR, 'Temp/Breakpoint.state')
BREAKPOINT_RECORD_FILE = os.path.join(SYSTEM_LOGPATH, 'log_breakpoint.log')
BREAKPOINT_FAULT_FILE = os.path.join(SYSTEM_LOGPATH, 'log_fault.log')

# 这些状态表示系统仍然处于运行中，下一次启动时需要报告上一次的中断情况
BREAKPOINT_ALIVE_PHASES = ('boot', 'running', 'interrupted', 'crashed')
BREAKPOINT_SIGNALS = ('SIGTERM', 'SIGBREAK')


class BreakpointFatal(BaseException):
    """终止系统的异常。

    该异常继承自 BaseException，所以终端命令级的保护不会拦截它，
    这样 'throw' 命令仍然可以模拟系统意外终止的情况。
    """


class BreakpointGuard:
    """断点保护。"""

    def __init__(self):
        self.pid = os.getpid()
        self.username = None
        self.mode = None
        self.session_start = None
        self.updated_at = None
        self.command_count = 0
        self.last_command = ''
        self.phase = 'boot'
        self.armed = False
        self.installed = False
        self.previous_state = None
        self._fault_file = None
        self._emergency_fd = None
        self._signals = []
        self._old_excepthook = None
        self._old_threading_excepthook = None

    def _now(self):
        """返回当前的格式化时间。"""
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    def _describe(self):
        """描述当前会话的断点信息。"""
        return ('time         : %s\n'
                'python       : %s (%s)\n'
                'platform     : %s\n'
                'working dir  : %s\n'
                'pid          : %s\n'
                'user         : %s (mode: %s)\n'
                'session start: %s\n'
                'commands     : %s\n'
                'last command : %s\n'
                'phase        : %s\n'
                'record file  : %s\n'
                'state file   : %s\n'
                % (self.updated_at, platform.python_version(), sys.executable, platform.platform(),
                   os.getcwd(), self.pid, self.username, self.mode, self.session_start,
                   self.command_count, self.last_command, self.phase,
                   BREAKPOINT_RECORD_FILE, BREAKPOINT_STATE_FILE)
                )

    def _describe_state(self, state):
        """描述保存在文件中的断点状态。"""
        return ('user         : %s\n'
                'mode         : %s\n'
                'pid          : %s\n'
                'session start: %s\n'
                'updated at   : %s\n'
                'phase        : %s\n'
                'commands     : %s\n'
                'last command : %s\n'
                'record file  : %s\n'
                % (state.get('username'), state.get('mode'), state.get('pid'),
                   state.get('session_start'), state.get('updated_at'), state.get('phase'),
                   state.get('command_count'), state.get('last_command'),
                   state.get('record_file') or BREAKPOINT_RECORD_FILE)
                )

    def _thread_stacks(self):
        """收集当前所有线程的调用栈。"""
        lines = []
        frames = sys._current_frames()
        for thread in threading.enumerate():
            frame = frames.get(thread.ident)
            if frame is None:
                continue
            lines.append("--- thread '%s' (id=%s) ---" % (thread.name, thread.ident))
            lines.extend(traceback.format_stack(frame))
        return ''.join(lines).rstrip() if lines else '(no thread frames)'

    def _read_state(self):
        """读取上一次的断点状态。"""
        if not os.path.exists(BREAKPOINT_STATE_FILE):
            return None
        try:
            with open(BREAKPOINT_STATE_FILE, 'r', encoding='utf-8') as statefile:
                state = literal_eval(statefile.read())
        except (OSError, ValueError, SyntaxError) as error:
            logger.error(f"BreakpointStateError:cannot read the breakpoint state. [{error}]")
            return None
        return state if isinstance(state, dict) else None

    def _write_state(self):
        """写入断点状态，并立即同步到磁盘，防止断电丢失。"""
        state = {'version': 1, 'pid': self.pid, 'username': self.username, 'mode': self.mode,
                 'session_start': self.session_start, 'updated_at': self.updated_at,
                 'command_count': self.command_count, 'last_command': self.last_command,
                 'phase': self.phase, 'armed': self.armed,
                 'record_file': BREAKPOINT_RECORD_FILE
                 }
        try:
            with open(BREAKPOINT_STATE_FILE, 'w', encoding='utf-8') as statefile:
                statefile.write(repr(state))
                statefile.flush()
                os.fsync(statefile.fileno())
        except OSError as error:
            logger.error(f"BreakpointStateError:cannot write the breakpoint state. [{error}]")

    def _append_record(self, title, detail):
        """追加一条断点记录，并立即同步到磁盘。"""
        record = "[BREAKPOINT] %s %s\n%s\n" % (self._now(), title, detail)
        try:
            with open(BREAKPOINT_RECORD_FILE, 'a+', encoding='utf-8') as recordfile:
                recordfile.write(record)
                recordfile.flush()
                os.fsync(recordfile.fileno())
        except OSError as error:
            logger.error(f"BreakpointRecordError:cannot write the breakpoint record. [{error}]")
        return record

    def _is_unclean(self, state):
        """判断保存的断点状态是否说明上一次没有正常退出。"""
        return bool(state) and bool(state.get('armed')) and state.get('phase') in BREAKPOINT_ALIVE_PHASES

    def _report_previous(self):
        """报告上一次没有正常退出的会话。"""
        state = self.previous_state
        if not self._is_unclean(state):
            return
        self._append_record("BreakpointRecovery:the last session did not exit normally",
                            self._describe_state(state)
                            )
        logger.debug("BreakpointWarning:the last session did not exit normally. "
                     "[BREAKPOINT:('%s', '%s', '%s', '%s')]"
                     % (state.get('username'), state.get('last_command'),
                        state.get('updated_at'), state.get('phase'))
                     )

    def install(self):
        """安装断点保护的各个钩子，重复调用不会重复安装。"""
        if self.installed:
            return self
        for path in (os.path.dirname(BREAKPOINT_STATE_FILE), SYSTEM_LOGPATH):
            if not os.path.exists(path):
                os.makedirs(path)
        self.previous_state = self._read_state()
        try:
            self._old_excepthook = sys.excepthook
            sys.excepthook = self._excepthook
        except (AttributeError, TypeError) as error:
            logger.warning(f"BreakpointInstallError:cannot install the excepthook. [{error}]")
        try:
            self._old_threading_excepthook = threading.excepthook
            threading.excepthook = self._thread_excepthook
        except (AttributeError, TypeError) as error:
            logger.warning(f"BreakpointInstallError:cannot install the threading excepthook. [{error}]")
        try:
            self._fault_file = open(BREAKPOINT_FAULT_FILE, 'a+', encoding='utf-8')
            faulthandler.enable(file=self._fault_file, all_threads=True)
        except (OSError, RuntimeError, ValueError) as error:
            logger.warning(f"BreakpointInstallError:cannot enable the faulthandler. [{error}]")
        try:
            self._emergency_fd = os.open(BREAKPOINT_RECORD_FILE,
                                         os.O_CREAT | os.O_APPEND | os.O_WRONLY,
                                         0o644
                                         )
        except OSError as error:
            logger.warning(f"BreakpointInstallError:cannot open the emergency record file. [{error}]")
        for signame in BREAKPOINT_SIGNALS:
            signum = getattr(signal, signame, None)
            if signum is None:
                continue
            try:
                signal.signal(signum, self._signal_handler)
                self._signals.append(signum)
            except (OSError, RuntimeError, ValueError) as error:
                logger.warning(f"BreakpointInstallError:cannot install the signal {signame}. [{error}]")
        atexit.register(self._atexit)
        self.phase = 'boot'
        self.armed = True
        self.session_start = self._now()
        self.updated_at = self.session_start
        self._write_state()
        self._report_previous()
        self.installed = True
        logger.info(f"Breakpoint protection installed. [BREAKPOINT:('boot', {self.pid})]")
        return self

    def arm(self, username, mode):
        """开始保护一个新的终端会话。"""
        self.username = username
        self.mode = mode
        self.session_start = self._now()
        self.updated_at = self.session_start
        self.command_count = 0
        self.last_command = ''
        self.phase = 'running'
        self.armed = True
        self._write_state()
        logger.info(f"Breakpoint protection armed. [BREAKPOINT:('{username}', '{mode}', {self.pid})]")

    def checkpoint(self, command):
        """在执行命令前写入断点，保证意外中断时能知道停在哪条命令。"""
        if not self.armed:
            return
        self.command_count += 1
        self.last_command = command
        self.updated_at = self._now()
        if self.phase != 'running':
            self.phase = 'running'
        self._write_state()

    def interrupt(self, tracebacktext=None):
        """记录一次键盘中断，终端会继续运行。"""
        self.phase = 'interrupted'
        self.updated_at = self._now()
        self._write_state()
        detail = self._describe()
        if tracebacktext:
            detail += '------------------------------ traceback ------------------------------\n' \
                      + str(tracebacktext).rstrip() + '\n'
        self._append_record("BreakpointInterrupt:the current command was interrupted by the user", detail)
        logger.warning("BreakpointInterrupt:the current command was interrupted by the user. "
                       "[BREAKPOINT:('%s', '%s')]" % (self.username, self.last_command)
                       )

    def crash_report(self, reason, exc_text=None, fatal=True):
        """记录一次异常中断。

        fatal 为 True 时表示进程即将退出，为 False 时表示终端命令级保护拦截了异常。
        """
        self.phase = 'crashed' if fatal else 'interrupted'
        self.updated_at = self._now()
        self._write_state()
        detail = self._describe()
        detail += 'reason       : %s\n' % reason
        if exc_text:
            detail += '------------------------------ traceback ------------------------------\n' \
                      + str(exc_text).rstrip() + '\n'
        detail += '--------------------------- thread stacks -----------------------------\n' \
                  + self._thread_stacks() + '\n'
        if fatal:
            self._append_record("BreakpointEmergency:the system was interrupted unexpectedly", detail)
            logger.critical("BreakpointEmergency:the system was interrupted unexpectedly. "
                            "[BREAKPOINT:('%s', '%s')]\n%s" % (self.username, reason, detail)
                            )
        else:
            self._append_record("BreakpointCommandError:the command was blocked by the breakpoint protection",
                                detail
                                )
            logger.error("BreakpointCommandError:the command was blocked by the breakpoint protection. "
                         "[BREAKPOINT:('%s', '%s')]\n%s" % (self.username, reason, detail)
                         )

    def recover(self):
        """返回上一次没有正常退出的会话信息，只返回一次。"""
        state, self.previous_state = self.previous_state, None
        if not self._is_unclean(state):
            return None
        return state

    def disarm(self):
        """正常结束终端会话，清除断点警示。"""
        if not self.armed:
            return
        self.phase = 'shutdown'
        self.armed = False
        self.updated_at = self._now()
        self._write_state()
        logger.info("Breakpoint protection disarmed. "
                    "[BREAKPOINT:('%s', '%s', %s, %s)]"
                    % (self.username, self.mode, self.command_count, self.updated_at)
                    )

    def _excepthook(self, exc_type, exc_value, exc_tb):
        """未捕获异常钩子。"""
        try:
            exc_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
            self.crash_report("uncaught exception '%s: %s'" % (exc_type.__name__, exc_value), exc_text)
        except Exception as error:  # 钩子本身不能再抛出异常，否则会掩盖原始错误
            try:
                logger.error(f"BreakpointReportError:failed to dump the breakpoint record. [{error}]")
            except Exception:
                pass
        if self._old_excepthook is not None:
            self._old_excepthook(exc_type, exc_value, exc_tb)
        else:
            sys.__excepthook__(exc_type, exc_value, exc_tb)

    def _thread_excepthook(self, args):
        """线程异常钩子。"""
        thread_name = args.thread.name if getattr(args, 'thread', None) is not None else 'unknown'
        try:
            exc_text = ''.join(traceback.format_exception(args.exc_type, args.exc_value,
                                                          args.exc_traceback)
                               )
            self.phase = 'interrupted'
            self._write_state()
            self._append_record("BreakpointThreadError:uncaught exception in thread '%s'" % thread_name,
                                self._describe() + exc_text + '\n'
                                )
            logger.error("BreakpointThreadError:uncaught exception in thread '%s'. "
                         "[BREAKPOINT:('%s', '%s')]"
                         % (thread_name, self.username, args.exc_type.__name__)
                         )
        except Exception as error:
            try:
                logger.error(f"BreakpointReportError:failed to dump the thread record. [{error}]")
            except Exception:
                pass
        if self._old_threading_excepthook is not None:
            self._old_threading_excepthook(args)
        else:
            sys.__excepthook__(args.exc_type, args.exc_value, args.exc_traceback)

    def _signal_handler(self, signum, frame):
        """致命信号处理：先留下断点记录，再恢复系统默认的退出方式。"""
        try:
            message = "[BREAKPOINT] %s BreakpointSignal:the system received signal %s " \
                      "(pid=%s, user=%s, last command=%r)\n" \
                      % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), signum,
                         self.pid, self.username, self.last_command
                         )
            if self._emergency_fd is not None:
                os.write(self._emergency_fd, message.encode('utf-8', errors='replace'))
                os.fsync(self._emergency_fd)
        except (OSError, ValueError):
            pass
        try:
            signal.signal(signum, signal.SIG_DFL)
        except (OSError, RuntimeError, ValueError):
            pass
        try:
            os.kill(self.pid, signum)
        except (OSError, RuntimeError, ValueError):
            raise SystemExit(1)

    def _atexit(self):
        """进程退出时检查断点状态，清理文件句柄。"""
        if self.armed and self.phase in ('boot', 'running', 'interrupted'):
            self.crash_report('process exited without a normal shutdown')
        try:
            faulthandler.disable()
        except (RuntimeError, ValueError):
            pass
        if self._fault_file is not None:
            try:
                self._fault_file.close()
            except OSError:
                pass
            self._fault_file = None
        if self._emergency_fd is not None:
            try:
                os.close(self._emergency_fd)
            except OSError:
                pass
            self._emergency_fd = None


_breakpoint_guard = None


def get_guard():
    """获取全局断点保护实例。"""
    global _breakpoint_guard
    if _breakpoint_guard is None:
        _breakpoint_guard = BreakpointGuard()
    return _breakpoint_guard
