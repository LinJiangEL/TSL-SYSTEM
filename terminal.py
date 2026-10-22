#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import os
import sys
import time
import traceback
import subprocess
from ast import literal_eval
from setuptools.errors import PlatformError
from loguru import logger
from bin.helpformat import Help
from doc.helppage import HelpPage
from selfcheck import check_command
from tools.__built_in__.restore import ImagePath, Images, restore
from tools.__built_in__.typemod import gettype, isnum
from tools.__built_in__.IOProcessor import read_input
from tools.__built_in__.external import run, display_file, clear_screen
from config import SYSTEM_DIR, SYSTEM_LOGPATH, SYSTEM_LOGFORMAT, SYSTEM_LOGSTDOUT, \
    SuperUser, SYSTEM_FILES, SYSTEM_PRINTER, SYSTEM_CLEARSTDOUT, HelpPages_DIR, PageReader, id_md5
from sysmgr import TempManager, UserManager, LoggerManager
from guard import get_guard, BreakpointFatal
from tools.__built_in__.TSLlogger import Logger
from tools.__built_in__ import style
Logger()

"""
 系统默认不会实时输出日志内容，如果有需要:
  ·Windows下请运行:
     set LOGSTDOUT=1
     python3 system.py
  ·Linux下请运行:
     LOGSTDOUT=1 python3 system.py
"""
if not SYSTEM_LOGSTDOUT:
    logger.remove(handler_id=None)

terminal_logger = logger.add(os.path.join(SYSTEM_LOGPATH, "log_{time:YYYY-MM}.log"),
                             format=SYSTEM_LOGFORMAT,
                             level="DEBUG",
                             rotation="32 MB",
                             enqueue=True
                             )

if sys.platform == 'win32':
    from config import binhelp_win32dict as helpdict
elif sys.platform == 'linux':
    from config import binhelp_linuxdict as helpdict
else:
    logger.critical("PlatformError:TSL-SYSTEM can only run on win32 or linux platform, but yours is %s!" % sys.platform)
    logger.info("System shutdown with Exceptions.")
    raise PlatformError('TSL-SYSTEM can only run on the win32 or linux platform!')


def terminal(USERNAME, MODE, Bin_DIR):
    breakpoint_guard = get_guard()
    breakpoint_guard.install()
    last_session = breakpoint_guard.recover()
    if last_session is not None:
        style.warning(f"BreakpointWarning:the last session did not exit normally. "
                      f"[BREAKPOINTINFO:('{last_session.get('username')}', "
                      f"'{last_session.get('last_command')}', '{last_session.get('updated_at')}')]"
                      )
        print('')
    logger.info("Load sysmgr.TempManager.")
    tempmgr = TempManager()
    check_usertmp = tempmgr.CheckPwdUser()
    if not check_usertmp[0]:
        logger.warning("SystemWarning:the user who logged on last on the system did not shutdown the system properly. "
                       "[USERINFO:('%s')]" % check_usertmp[1]
                       )
        style.warning("SystemWarning:the user who logged on last on the system did not shutdown the system properly. "
                      f"[USERINFO: ('{check_usertmp[1]}')]"
                      )
        print('')
        tempmgr.WritePwdUser()
    tempmgr.WritePwdUser(USERNAME)

    logger.info("Load sysmgr.LoggerManager.")
    loggermgr = LoggerManager(SYSTEM_LOGPATH, SYSTEM_PRINTER)

    logger.info("Load sysmgr.UserManager.")
    usermgr = UserManager(os.path.join(SYSTEM_DIR, 'Database/login.db'), USERNAME)
    breakpoint_guard.arm(USERNAME, MODE)

    style.banner('TSL-SYSTEM Terminal', width=60)
    style.key_value('User', USERNAME)
    style.key_value('Mode', 'SuperUser' if MODE == '#' else 'SimpleUser')
    style.key_value('Bin_DIR', os.path.abspath(Bin_DIR).replace('\\', '/'))
    style.muted("Input 'help' to list the built-in commands, 'exit' to shut down the system.")
    print('')

    while os.path.exists(Bin_DIR) and id_md5[2] is chr(int(0x66)):
        try:
            Bin_DIR = Bin_DIR.replace('\\', '/')
            command = read_input(f'{USERNAME}@TSL-SYSTEM {MODE} ', 'terminal', strip=True)
            cmd_tmp = [cmd_argv.strip() for cmd_argv in command.split() if cmd_argv]
            if not cmd_tmp:
                cmd_tmp.append('')
            if command:
                breakpoint_guard.checkpoint(command)
                logger.debug(f"Terminal received a command. [USERINFO:('{USERNAME}')][CMDINFO:('{command}')]")

            while cmd_tmp[0] == 'sudo':
                if len(cmd_tmp) > 1:
                    cmd_tmp = cmd_tmp[1:]
                elif cmd_tmp[0] == 'sudo':
                    cmd_tmp = ['']
                else:
                    continue

            is_root = True if command.startswith('sudo') or MODE == '#' else False
            if cmd_tmp[0] == '':
                continue
            elif cmd_tmp[0] == 'trunc':
                if is_root:
                    if len(cmd_tmp) >= 2:
                        trunc_command = ' '.join(cmd_tmp[1:])
                        # cmd.exe parses the quoting rules itself, so the command line must be passed as
                        # one string; a list would be re-escaped by subprocess and break "a b"-like arguments.
                        if sys.platform == 'win32':
                            trunc_shell = f'cmd /C {trunc_command}'
                        else:
                            trunc_shell = ['/bin/sh', '-c', trunc_command]
                        try:
                            trunc_process = subprocess.run(trunc_shell)
                        except FileNotFoundError:
                            style.error("RuntimeError:the shell of the mother system cannot be found, "
                                        "please check the system environment.\n"
                                        )
                            logger.error(f"{USERNAME} failed to execute 'trunc' because the shell of the mother "
                                         f"system cannot be found. [CMDINFO:('trunc', '{cmd_tmp[1:]}')]"
                                         )
                        except OSError as error:
                            style.error(f"OSError:{error}\n")
                            logger.error(f"{USERNAME} failed to execute 'trunc' because {error}. "
                                         f"[CMDINFO:('trunc', '{cmd_tmp[1:]}')]"
                                         )
                        else:
                            if trunc_process.returncode == 0:
                                logger.info(f"{USERNAME} succeed in executing 'trunc' as a SuperUser. "
                                            f"[CMDINFO:('trunc', '{cmd_tmp[1:]}')]"
                                            )
                            else:
                                style.error(f"RuntimeError:external command exited with code "
                                            f"{trunc_process.returncode}.\n"
                                            )
                                logger.warning(f"{USERNAME} failed to execute 'trunc' because external command "
                                               f"exited with code {trunc_process.returncode}. "
                                               f"[CMDINFO:('trunc', '{cmd_tmp[1:]}')]"
                                               )
                    else:
                        style.error("CommandUsageError:incorrectly trunc usage, "
                                    "please input 'help trunc' to get its help-page.\n"
                                    )
                else:
                    style.error('sh: trunc: Permission denied.\n')
                    logger.info(f"{USERNAME} failed to execute 'trunc' because {USERNAME} is a SimpleUser. "
                                f"[CMDINFO:('trunc', '{cmd_tmp[1:]}')]"
                                )
            elif cmd_tmp[0] == 'music':
                from tools.Music.library import get_library
                from tools.Music.crawler import get_crawler, CrawlerError
                from tools.Music.player import get_player, PlaybackError
                music_start = time.time()
                music_player = get_player()
                music_library = get_library()
                music_crawler = get_crawler()
                music_method = cmd_tmp[1] if len(cmd_tmp) >= 2 else 'play'
                music_argument = ' '.join(cmd_tmp[2:])
                try:
                    if music_method == 'play':
                        if music_argument:
                            music_tracks = music_library.resolve(music_argument)
                            if not music_tracks:
                                style.error(f"MusicNotFoundError:no music matched '{music_argument}'.\n")
                                logger.warning(f"{USERNAME} failed to play music because no music matched "
                                               f"'{music_argument}'. [MUSICINFO:('{music_argument}')]"
                                               )
                                continue
                            if len(music_tracks) > 1:
                                style.warning('Multiple tracks matched, please point out one of them by its index:')
                                print(music_library.table(music_tracks), '\n')
                                continue
                            music_message = music_player.play_song(music_tracks[0])
                        else:
                            music_message = music_player.play(music_library.scan())
                        style.info(f'{music_message}')
                        logger.info(f"{USERNAME} started the music playback. "
                                    f"[MUSICINFO:('{music_player.status()}', '{music_argument}')]"
                                    )
                    elif music_method == 'stop':
                        style.info(f'{music_player.stop()}')
                        logger.info(f"{USERNAME} stopped the music playback. [MUSICINFO:('stopped')]")
                    elif music_method == 'pause':
                        style.info(f'{music_player.pause()}')
                        logger.info(f"{USERNAME} paused or resumed the music playback. "
                                    f"[MUSICINFO:('{music_player.status()}')]"
                                    )
                    elif music_method == 'search':
                        if not music_argument:
                            style.error("CommandUsageError:incorrectly music usage, "
                                  "please input 'music search KEYWORD'.\n"
                                  )
                            logger.warning(f"{USERNAME} failed to execute 'music search' because of "
                                           f"incorrect usage. [CMDINFO:{cmd_tmp}]"
                                           )
                            continue
                        try:
                            music_tracks = music_crawler.search(music_argument)
                        except CrawlerError as error:
                            style.error(f'CrawlerError:{error}\n')
                            logger.warning(f"{USERNAME} failed to search online music because {error}. "
                                           f"[CMDINFO:{cmd_tmp}]"
                                           )
                            continue
                        if not music_tracks:
                            style.error(f"MusicNotFoundError:no online music matched '{music_argument}'.\n")
                            logger.warning(f"{USERNAME} searched online music but no music matched "
                                           f"'{music_argument}'. [MUSICINFO:('{music_argument}')]"
                                           )
                            continue
                        print(music_crawler.table(music_tracks), '\n')
                        print("Input 'music get INDEX' to download the selected music.\n")
                        logger.info(f"{USERNAME} searched online music and got {len(music_tracks)} results. "
                                    f"[MUSICINFO:('search', '{music_argument}')]"
                                    )
                    elif music_method == 'get':
                        if not music_argument:
                            style.error("CommandUsageError:incorrectly music usage, "
                                  "please input 'music get INDEX/KEYWORD'.\n"
                                  )
                            logger.warning(f"{USERNAME} failed to execute 'music get' because of "
                                           f"incorrect usage. [CMDINFO:{cmd_tmp}]"
                                           )
                            continue
                        try:
                            music_tracks = music_crawler.resolve(music_argument)
                        except CrawlerError as error:
                            style.error(f'CrawlerError:{error}\n')
                            logger.warning(f"{USERNAME} failed to search online music because {error}. "
                                           f"[CMDINFO:{cmd_tmp}]"
                                           )
                            continue
                        if not music_tracks:
                            style.error(f"MusicNotFoundError:no music matched '{music_argument}'.\n")
                            logger.warning(f"{USERNAME} failed to download music because no music matched "
                                           f"'{music_argument}'. [CMDINFO:{cmd_tmp}]"
                                           )
                            continue
                        if len(music_tracks) > 1:
                            style.warning('Multiple tracks matched, please point out one of them by its index:')
                            print(music_crawler.table(music_tracks), '\n')
                            logger.warning(f"{USERNAME} failed to download music because multiple music matched "
                                           f"'{music_argument}'. [MUSICINFO:('{music_argument}')]"
                                           )
                            continue
                        music_track = music_tracks[0]
                        try:
                            music_path = music_crawler.download(music_track)
                        except CrawlerError as error:
                            style.error(f'CrawlerError:{error}\n')
                            logger.warning(f"{USERNAME} failed to download online music "
                                           f"'{music_track.label()}' because {error}. "
                                           f"[MUSICINFO:('{music_track.source}')]"
                                           )
                            continue
                        style.success(f'Downloaded: {music_path}\n')
                        music_library.scan(refresh=True)
                        print("Input 'music play KEYWORD' to play the downloaded music.\n")
                        logger.info(f"{USERNAME} downloaded online music '{music_track.label()}' "
                                    f"from '{music_track.source}' to '{music_path}'. "
                                    f"[MUSICINFO:('get', '{music_track.source}')]"
                                    )
                    else:
                        style.error("CommandUsageError:incorrectly music usage, "
                              "please input 'help music' to get its help-page.\n")
                        logger.warning(f"{USERNAME} failed to execute 'music' because of incorrect usage. "
                                       f"[CMDINFO:{cmd_tmp}]"
                                       )
                        continue
                except PlaybackError as error:
                    style.error(f'PlaybackError:{error}\n')
                    logger.error(f"{USERNAME} failed to control the music playback because {error}. "
                                 f"[CMDINFO:{cmd_tmp}]"
                                 )
                except CrawlerError as error:
                    style.error(f'CrawlerError:{error}\n')
                    logger.warning(f"{USERNAME} failed to crawl online music because {error}. "
                                   f"[CMDINFO:{cmd_tmp}]"
                                   )
                else:
                    logger.debug(f"The music command returned in {round(time.time() - music_start, 3)}s. "
                                 f"The playback is handled in the background."
                                 )
            elif cmd_tmp[0] == 'internal':
                if len(cmd_tmp) >= 2:
                    argvs = cmd_tmp[2:]
                    if (cmd_tmp[1] if sys.platform == 'linux' else f'{cmd_tmp[1]}.bat') in os.listdir(Bin_DIR):
                        internal_command = os.path.join(Bin_DIR, cmd_tmp[1])
                        internal_arguments = ['cmd', '/C', internal_command] if sys.platform == 'win32' \
                            else [internal_command]
                        internal_code = run(internal_arguments + argvs)
                        if internal_code == 0:
                            logger.info(f"{USERNAME} succeed in executing 'internal'. [CMDINFO:{cmd_tmp}]")
                        else:
                            logger.warning(f"{USERNAME} failed to execute 'internal' because internal command "
                                           f"exited with code {internal_code}. [CMDINFO:{cmd_tmp}]"
                                           )
                    else:
                        style.error(f"CommandNotFoundError:internal command '{cmd_tmp[1]}' cannot be found in BinDIR.")
                        logger.error(f"{USERNAME} failed to execute 'internal' because command cannot be found in BinDIR. "
                                     f"[CMDINFO:{cmd_tmp}]"
                                     )
                else:
                    style.error("CommandUsageError:incorrectly internal usage, "
                          "please input 'help internal' to get its help-page.\n")
                    logger.warning(f"{USERNAME} failed to execute 'internal' because of incorrect usage. "
                                   f"[CMDINFO:('internal', '{cmd_tmp[1:]}')]"
                                   )
                    continue
            elif cmd_tmp[0] == "chjava" and len(cmd_tmp) <= 2:
                if is_root:
                    if len(cmd_tmp) == 1:
                        style.error("KeyError:version\n")
                        logger.warning(f"{USERNAME} failed to execute 'chjava' because version was not specified. "
                                       f"[CMDINFO:('chjava', '{cmd_tmp[1:]}')]"
                                       )
                        continue
                    from tools.__built_in__.chjava import setjava
                    if cmd_tmp[1].isdigit():
                        setjava(int(cmd_tmp[1]))
                        logger.info(f"{USERNAME} succeed in executing 'chjava'. "
                                    f"[CMDINFO:('chjava', '{cmd_tmp[1]}')]"
                                    )
                    else:
                        style.error("TypeError:the version must be an integer.\n")
                        logger.warning(f"{USERNAME} failed to execute 'chjava' because the version is not an integer. "
                                       f"[CMDINFO:('chjava', '{cmd_tmp[1]}')]"
                                       )
                        continue
                else:
                    style.error('sh: chjava: Permission denied.\n')
                    logger.info(f"{USERNAME} failed to execute 'chjava' because {USERNAME} is a SimpleUser. "
                                f"[CMDINFO:('chjava', '{cmd_tmp[1:]}')]"
                                )
            elif cmd_tmp[0] == "execute" and len(cmd_tmp) <= 2:
                from tools import execute
                execute_start = time.time()
                logger.info(f"{USERNAME} started the tools service. "
                            f"[CMDINFO:('execute', '{cmd_tmp[1] if len(cmd_tmp) == 2 else None}')]"
                            )
                toolcode = execute.execute(cmd_tmp[1] if len(cmd_tmp) == 2 else None)
                if toolcode == -1:
                    logger.warning(f"{USERNAME} stopped the tools service because it cannot be loaded. "
                                   f"[CMDINFO:('execute', '{cmd_tmp[1] if len(cmd_tmp) == 2 else None}')]"
                                   )
                    continue
                literal_eval(execute._ok)
                logger.info(f"{USERNAME} stopped the tools service after "
                            f"{round(time.time() - execute_start, 3)}s. "
                            f"[CMDINFO:('execute', '{cmd_tmp[1] if len(cmd_tmp) == 2 else None}')]"
                            )
            elif cmd_tmp[0] == 'backup' and len(cmd_tmp) == 1:
                filename = f"TSL-SYSTEM_{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}.tar.gz"
                tempmgr.PwdUserTmpFile.close()
                logger.info(f"{USERNAME} started to create a system image. [IMAGEINFO:'{filename}']")
                backup_code = run(['tar', '-zcvf', f'backup/TSL-SYSTEM-BACKUP-FILES/{filename}']
                                  + [file for file in SYSTEM_FILES if file != 'backup'],
                                  cwd=SYSTEM_DIR)
                if backup_code == 0:
                    style.success('Successfully create an current system image.')
                    logger.info(f"{USERNAME} create an current system image. [IMAGEINFO:'{filename}']")
                else:
                    style.error(f"RuntimeError:failed to create the system image, tar exited with code {backup_code}.")
                    logger.error(f"{USERNAME} failed to create an current system image because tar "
                                 f"exited with code {backup_code}. [IMAGEINFO:'{filename}']"
                                 )
                tempmgr.PwdUserTmpFile = open(os.path.join(SYSTEM_DIR, 'Temp/PwdUser'), 'r+')
            elif cmd_tmp[0] == 'restore' and len(cmd_tmp) <= 2:
                if not is_root:
                    style.error('sh: restore: Permission denied.\n')
                    logger.info(f"{USERNAME} failed to execute 'restore' because {USERNAME} is a SimpleUser. "
                                f"[CMDINFO:('restore', '{cmd_tmp[1:]}')]"
                                )
                    continue
                if '-l' in cmd_tmp:
                    if not Images:
                        style.warning("Empty images in BACKUP_DIR.\n")
                        logger.warning(f"'{USERNAME}' tried to list exists images and chose one to execute 'restore', "
                                       "but this operation was blocked because there were no previous backup images. "
                                       f"[USERINFO:('{USERNAME}')]"
                                       )
                    else:
                        print('\nAvailable system images:')
                        for imagefile in Images:
                            print(imagefile)
                        print('')
                        logger.info(f"{USERNAME} listed all the available system images. [IMAGES:{Images}]")
                elif '-l' not in cmd_tmp and len(cmd_tmp) == 2:
                    image = cmd_tmp[1]
                    imagepath = os.path.join(ImagePath, image)
                    restore(USERNAME, is_root, imagepath, cmd_tmp, tempmgr, usermgr, logger)
                else:
                    image = read_input('Please input image filename to recover this system: ',
                                       'path', strip=True)
                    if image == '':
                        print()
                        continue
                    imagepath = os.path.join(ImagePath, image)
                    restore(USERNAME, is_root, imagepath, cmd_tmp, tempmgr, usermgr, logger)
            elif cmd_tmp[0] == 'user' and len(cmd_tmp) >= 2:
                if cmd_tmp[1] not in ['add', 'remove', 'info', 'set', 'list']:
                    style.error(f"AttitudeError:assignment '{cmd_tmp[1]}' is not defined in UserManager.\n")
                    logger.warning(f"{USERNAME} failed to execute 'user' because assignment '{cmd_tmp[1]}' "
                                   f"is not defined in UserManager. [CMDINFO:{cmd_tmp}]"
                                   )
                    continue
                else:
                    if len(cmd_tmp) == 2 and cmd_tmp[1] != 'list':
                        style.error(f"ArgumentError:cannot find any arguments followed by '{cmd_tmp[1]}'.\n")
                        logger.warning(f"{USERNAME} failed to execute 'user {cmd_tmp[1]}' because no argument "
                                       f"was found. [CMDINFO:{cmd_tmp}]"
                                       )
                        continue
                if cmd_tmp[2] in ['--mode', '--password'] if len(cmd_tmp) > 2 else False:
                    if cmd_tmp[1] != 'list':
                        style.error("CommandError:invalid user command format:"
                              f"'{cmd_tmp[2]}' cannot be followed by '{cmd_tmp[1]}'!\n"
                              )
                        logger.warning(f"{USERNAME} failed to execute 'user {cmd_tmp[1]}' because the format "
                                       f"was invalid. [CMDINFO:{cmd_tmp}]"
                                       )
                        continue

                opt_mode = cmd_tmp[cmd_tmp.index('--mode') + 1] \
                    if cmd_tmp.count('--mode') and cmd_tmp[-1] != '--mode' \
                    and ((cmd_tmp[cmd_tmp.index('--password') - 1] != '--mode') if '--password' in cmd_tmp else True) \
                    else 'user'
                opt_username = cmd_tmp[2] \
                    if ((cmd_tmp.index('--mode') > 2) if '--mode' in cmd_tmp
                        else (cmd_tmp[1] in ['add', 'remove', 'info']
                              and len(cmd_tmp) == 3) or (cmd_tmp.index('--password') > 2) if '--password' in cmd_tmp
                        else (cmd_tmp[1] in ['add', 'remove', 'info']
                        and len(cmd_tmp) == 3)) and cmd_tmp[1] not in ['set', 'list'] \
                    else None

                opt_password = cmd_tmp[cmd_tmp.index('--password') + 1] \
                    if cmd_tmp.count('--password') and cmd_tmp[-1] != '--password' \
                    and ((cmd_tmp[cmd_tmp.index('--mode') - 1] != '--password') if '--mode' in cmd_tmp else True) \
                    else False

                if cmd_tmp[1] == 'add':
                    usermgr.add(username=opt_username, mode=opt_mode, password=opt_password)
                elif cmd_tmp[1] == 'remove':
                    if opt_username in SuperUser:
                        print(f"OperationForbidden:cannot operate built-in user, current pemission denied.\n")
                        logger.critical("Someone tried to remove built-in user, this operation has been blocked. "
                                        f"[USERINFO:(‘{USERNAME}’)]"
                                        )
                        continue
                    else:
                        if opt_username is not None:
                            usermgr.remove(username=opt_username)
                        else:
                            style.error(f"NameError:user '{opt_username}' is not exists, "
                                  "the interpreter will ignore the request to delete it.\n"
                                  )
                            continue
                elif cmd_tmp[1] == 'list' and len(cmd_tmp) <= 4:
                    if len(cmd_tmp) != 2:
                        mode = cmd_tmp[cmd_tmp.index('--mode') + 1] if '--mode' in cmd_tmp \
                            and cmd_tmp[-1] != '--mode' else \
                            cmd_tmp[2] if len(cmd_tmp) == 3 else \
                            exec("print('SyntaxError:invalid UserManager.list called format.\n')")
                        if mode is None:
                            continue
                        usermgr.list(mode)
                    else:
                        style.warning("ParameterWarning:unclarified parameter mode, default set 'all' to it.\n")
                        usermgr.list(mode='all')
                elif cmd_tmp[1] == 'info' and len(cmd_tmp) == 3:
                    usermgr.info(username=cmd_tmp[-1])
                elif cmd_tmp[1] == 'set' and (3 if cmd_tmp[2] == 'password' else 4) < len(cmd_tmp) <= 5:
                    key = cmd_tmp[2]
                    target = cmd_tmp[3]
                    value = cmd_tmp[-1] if len(cmd_tmp) == 5 else \
                        exec("print('OperationInterrupt:cannot get the new value.\n')") \
                        if key != 'password' else None
                    if target != USERNAME:
                        print("Failed to change the password because user cannot change others' password. ")
                        print('sh: user: Permission denied.\n')
                        logger.error(f"{USERNAME} failed to execute 'user set' because changing others' "
                                     f"password is forbidden. [CMDINFO:{cmd_tmp}]"
                                     )
                        continue
                    else:
                        usermgr.set(key, target, value)
                else:
                    if cmd_tmp[1] not in ['add', 'remove', 'list', 'info', 'set']:
                        style.error(f"AttitudeError:assignment '{cmd_tmp[1]}' is not defined in UserManager.\n")
                    else:
                        style.error(f"SyntaxError:invalid UserManager.{cmd_tmp[1]} called format.\n")
                    logger.warning(f"{USERNAME} failed to execute the user command because the format was invalid. "
                                   f"[CMDINFO:{cmd_tmp}]"
                                   )
                    continue
            elif cmd_tmp[0] == 'help' and len(cmd_tmp) <= 2:
                if len(cmd_tmp) == 1:
                    style.banner('System Usage Help Page', width=60)
                    style.heading('System built-in commands')
                    Help(helpdict)
                    logger.debug(f"{USERNAME} opened the system usage help page. [CMDINFO:('help')]")
                else:
                    print('')
                    HelpPage(HelpPages_DIR, PageReader, cmd_tmp[1])
                    logger.debug(f"{USERNAME} opened the help page of '{cmd_tmp[1]}'. "
                                 f"[CMDINFO:('help', '{cmd_tmp[1]}')]"
                                 )
            elif cmd_tmp[0] == 'logger' and len(cmd_tmp) >= 2:
                if cmd_tmp[1] not in ['list', 'read', 'write', 'delete', 'flush']:
                    style.error(f"AttitudeError:assignment '{cmd_tmp[1]}' is not defined in LoggerManager.\n")
                    continue
                else:
                    if len(cmd_tmp) == 2 and cmd_tmp[1] != 'list':
                        style.error(f"ArgumentError:cannot find any arguments followed by '{cmd_tmp[1]}'.\n")
                        continue

                if cmd_tmp[1] == 'list' and len(cmd_tmp) == 2:
                    loggermgr.list()
                elif cmd_tmp[1] == 'read' and len(cmd_tmp) == 3:
                    logtime = cmd_tmp[-1]
                    loggermgr.read(logtime)
                elif cmd_tmp[1] == 'write' and len(cmd_tmp) >= 4:
                    if cmd_tmp[-1] == '--log':
                        style.warning("ParameterWarning:unclarified '--log' parameter, default set 'stdout' to it.")
                    logfile = cmd_tmp[-1] if cmd_tmp[-2] == '--log' and command.count('--log') == 1 else 'stdout'
                    if not logfile.endswith('.log') and logfile != 'stdout':
                        print('ValueError:invalid logfile format.\n')
                        continue

                    level = cmd_tmp[2]
                    if level not in loggermgr.logcolors.keys():
                        print('KeyError:unrecognized level parameter key.\n')
                        continue

                    message = " ".join(cmd_tmp[3:] if '--log' not in cmd_tmp[-2:] else cmd_tmp[3:-2])
                    if message.count('"') != 2 or not message.startswith('"') or not message.endswith('"'):
                        style.error("ValueError:unrecognized message parameter format.\n")
                        continue

                    loggermgr.write(level, message, logfile)
                elif cmd_tmp[1] == 'delete' and len(cmd_tmp) == 3:
                    if is_root:
                        loggermgr.delete(cmd_tmp[-1])
                    else:
                        style.error('sh: logger: Permission denied.')
                        logger.error(f"Failed to execute 'logger delete' because {USERNAME} is a SimpleUser. "
                                     f"[CMDINFO:{cmd_tmp}]"
                                     )
                        print()
                        continue
                elif cmd_tmp[1] == 'flush':
                    loggermgr.flush()
                else:
                    if cmd_tmp[1] not in ['list', 'read', 'write', 'delete', 'flush']:
                        style.error(f"AttitudeError:assignment '{cmd_tmp[1]}' is not defined in LoggerManager.\n")
                    else:
                        style.error(f"SyntaxError:invalid LoggerManager.{cmd_tmp[1]} called format.\n")
                    continue
                print()
            elif cmd_tmp[0] == "exit" and len(cmd_tmp) == 1:
                print(style.highlight('System shutdown ... ', 'yellow'), end='', flush=True)
                time.sleep(1)
                print(style.highlight('done.', 'green') + '\n')
                usermgr.databasefile.close()
                logger.info("UserManager hostdown.")
                tempmgr.WritePwdUser()
                tempmgr.PwdUserTmpFile.close()
                logger.info("TempManager hostdown.")
                logger.info("System Terminal hostdown.")
                breakpoint_guard.disarm()
                time.sleep(0.5)
                return 0
            elif cmd_tmp[0] == 'logout' and len(cmd_tmp) == 1:
                print(style.highlight(f"User '{USERNAME}' logout ... ", 'yellow'), end='', flush=True)
                usermgr.databasefile.close()
                tempmgr.WritePwdUser()
                tempmgr.PwdUserTmpFile.close()
                time.sleep(1)
                print(style.highlight('done.', 'green') + '\n')
                breakpoint_guard.disarm()
                return -1
            elif cmd_tmp[0] == 'upgrade':
                if check_command('git'):
                    if os.getcwd() == SYSTEM_DIR:
                        logger.info(f"{USERNAME} started to upgrade the system. [CMDINFO:('upgrade')]")
                        upgrade_code = run(['git', 'pull'], cwd=SYSTEM_DIR)
                        if upgrade_code == 0:
                            logger.info(f"{USERNAME} upgraded the system successfully. [CMDINFO:('upgrade')]")
                        else:
                            logger.warning(f"{USERNAME} failed to upgrade the system because git pull "
                                           f"exited with code {upgrade_code}. [CMDINFO:('upgrade')]"
                                           )
                    else:
                        style.error("FileNotFoundError:the upgrade must be performed in the SYSTEM_DIR.\n.")
                        logger.warning(f"{USERNAME} failed to upgrade the system because the system is not "
                                       f"running in SYSTEM_DIR. [CMDINFO:('upgrade')]"
                                       )
                else:
                    style.error("RuntimeError:'git' is not in the path, please install it and try again.\n")
                    logger.error(f"{USERNAME} failed to upgrade the system because 'git' was not found. "
                                 f"[CMDINFO:('upgrade')]"
                                 )
            elif cmd_tmp[0] == 'init' and len(cmd_tmp) <= 2:
                if is_root:
                    if len(cmd_tmp) == 1:
                        cmd_tmp.append(None)
                    if not isnum(cmd_tmp[1]):
                        style.error(f"TypeError:syscode must be int not {gettype(cmd_tmp[1])}.\n")
                        logger.warning(f"{USERNAME} failed to execute 'init' because syscode must be int "
                                       f"not {gettype(cmd_tmp[1])}. [CMDINFO:{cmd_tmp}]"
                                       )
                        continue
                    else:
                        cmd_tmp[1] = eval(cmd_tmp[1])
                        if (not cmd_tmp[1]) if len(cmd_tmp) == 2 else 0:
                            print(style.highlight('System shutdown ... ', 'yellow'), end='', flush=True)
                            time.sleep(1)
                            print(style.highlight('done.', 'green') + '\n')
                            usermgr.databasefile.close()
                            logger.info("UserManager hostdown.")
                            tempmgr.WritePwdUser()
                            tempmgr.PwdUserTmpFile.close()
                            logger.info("TempManager hostdown.")
                            logger.info("System Terminal hostdown.")
                            breakpoint_guard.disarm()
                            time.sleep(0.5)
                            return 0
                        else:
                            logger.info(f"{USERNAME} requested the system to shut down with "
                                        f"syscode {cmd_tmp[1]}. [CMDINFO:{cmd_tmp}]"
                                        )
                            breakpoint_guard.disarm()
                            return cmd_tmp[1]
                else:
                    print('sh: init: Permission denied.\n')
                    logger.info(f"{USERNAME} failed to execute 'init' because {USERNAME} is a SimpleUser. "
                                f"[CMDINFO:('init', '{cmd_tmp[1]}')]"
                                )
            elif cmd_tmp[0] == 'throw':
                raise BreakpointFatal("terminated system.")
            elif cmd_tmp[0] == 'clear' and len(cmd_tmp) == 1:
                clear_screen()
                print('')
                display_file(os.path.join(SYSTEM_DIR, 'motd'))
                print('')
                logger.debug(f"{USERNAME} cleared the screen. [CMDINFO:('clear')]")
            elif (cmd_tmp[0] in ['user', 'logger'] and len(cmd_tmp) == 1) \
                    or (cmd_tmp[0] in ['backup', 'exit', 'logout', 'clear'] and len(cmd_tmp) != 1) \
                    or (cmd_tmp[0] in ['restore', 'execute', 'init', 'help'] and len(cmd_tmp) > 2):
                style.error(f"CommandUsageError:incorrectly {cmd_tmp[0]} usage, "
                            f"please input 'help {cmd_tmp[0]}' to get its help-page.\n"
                            )
                logger.warning(f"{USERNAME} failed to execute '{cmd_tmp[0]}' because of incorrect usage. "
                               f"[CMDINFO:{cmd_tmp}]"
                               )
                continue
            else:
                style.error(f"TypeError:cannot execute '{cmd_tmp[0]}', "
                            "because trunc or internal type is unspecified!\n"
                            )
                logger.warning(f"{USERNAME} failed to execute '{cmd_tmp[0]}' because neither trunc nor "
                               f"internal type was specified. [CMDINFO:{cmd_tmp}]"
                               )
        except KeyboardInterrupt:
            breakpoint_guard.interrupt(traceback.format_exc())
            print("\nCtrl-C")
            continue
        except BreakpointFatal:
            breakpoint_guard.crash_report("the system was terminated by the user with 'throw'.",
                                          traceback.format_exc(),
                                          fatal=True
                                          )
            logger.critical("BreakpointFatal:the system was terminated by the user with 'throw'.")
            style.error("BreakpointFatal:the system was terminated by the user with 'throw'.\n")
            breakpoint_guard.disarm()
            raise SystemExit(1)
        except EOFError:
            logger.critical("BreakpointInputError:the standard input was closed unexpectedly, "
                            "the terminal will be shut down by the breakpoint protection."
                            )
            raise
        except Exception as error:
            breakpoint_guard.crash_report(f"uncaught exception '{type(error).__name__}: {error}'",
                                          traceback.format_exc(),
                                          fatal=False
                                          )
            style.error(f"\nUnexpectedError:{type(error).__name__}: {error}\n"
                        "The breakpoint protection has recorded this error, the terminal will keep running.\n"
                        )
            continue
