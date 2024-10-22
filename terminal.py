#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os
import sys
import time
from ast import literal_eval
from setuptools.errors import PlatformError
from loguru import logger
from bin.helpformat import Help
from doc.helppage import HelpPage
from tools.__built_in__.restore import ImagePath, Images, restore
from tools.__built_in__.typemod import gettype
from config import SYSTEM_DIR, SYSTEM_LOGPATH, SYSTEM_LOGFORMAT, SYSTEM_LOGSTDOUT, \
    SuperUser, SYSTEM_FILES, SYSTEM_PRINTER, SYSTEM_CLEARSTDOUT, HelpPages_DIR, PageReader, id_md5
from sysmgr import TempManager, UserManager, LoggerManager
from tools.__built_in__.TSLlogger import Logger
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
    logger.info("Load sysmgr.TempManager.")
    tempmgr = TempManager()
    check_usertmp = tempmgr.CheckPwdUser()
    if not check_usertmp[0]:
        logger.warning("SystemWarning:the user who logged on last on the system did not shutdown the system properly. "
                       "[USERINFO:('%s')]" % check_usertmp[1]
                       )
        print("SystemWarning:the user who logged on last on the system did not shutdown the system properly. "
              f"[USERINFO: ('{check_usertmp[1]}')]\n"
              )
        tempmgr.WritePwdUser()
    tempmgr.WritePwdUser(USERNAME)

    logger.info("Load sysmgr.LoggerManager.")
    loggermgr = LoggerManager(SYSTEM_LOGPATH, SYSTEM_PRINTER)

    logger.info("Load sysmgr.UserManager.")
    usermgr = UserManager(os.path.join(SYSTEM_DIR, 'Database/login.db'), USERNAME)

    while os.path.exists(Bin_DIR) and id_md5[2] is chr(int(0x66)):
        try:
            Bin_DIR = Bin_DIR.replace('\\', '/')
            command = input(f'{USERNAME}@TSL-SYSTEM {MODE} ').strip()
            cmd_tmp = [cmd_argv.strip() for cmd_argv in command.split()]
            if not cmd_tmp:
                cmd_tmp.append('')

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
            elif cmd_tmp[0] == 'trunc' and len(cmd_tmp) >= 2:
                if is_root:
                    os.system(f'{" ".join(cmd_tmp[1:])}')
                    logger.info(f"{USERNAME} succeed in executing 'trunc' as a SuperUser. "
                                f"[CMDINFO:('trunc', '{cmd_tmp[1:]}')]"
                                )
                else:
                    print('sh: trunc: Permission denied.\n')
                    logger.info(f"{USERNAME} failed to execute 'trunc' because {USERNAME} is a SimpleUser. "
                                f"[CMDINFO:('trunc', '{cmd_tmp[1:]}')]"
                                )
            elif cmd_tmp[0] == 'internal' and len(cmd_tmp) >= 2:
                argvs = cmd_tmp[2:]
                if (cmd_tmp[1] if sys.platform == 'linux' else f'{cmd_tmp[1]}.bat') in os.listdir(Bin_DIR):
                    os.system(f'{os.path.join(Bin_DIR, cmd_tmp[1])} {" ".join(argvs)}')
                    logger.info(f"{USERNAME} succeed in executing 'internal'. [CMDINFO:{cmd_tmp}]")
                else:
                    print(f"CommandNotFoundError:internal command '{cmd_tmp[1]}' cannot be found in BinDIR.")
                    logger.error(f"{USERNAME} failed to execute 'trunc' because command cannot be found in BinDIR. "
                                 f"[CMDINFO:{cmd_tmp}]"
                                 )
            elif cmd_tmp[0] == "execute" and len(cmd_tmp) <= 2:
                from tools import execute
                toolcode = execute.Execute(cmd_tmp[1] if len(cmd_tmp) == 2 else None)
                if toolcode == -1:
                    continue
                literal_eval(execute._ok)
            elif cmd_tmp[0] == 'backup' and len(cmd_tmp) == 1:
                filename = f"TSL-SYSTEM_{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}.tar.gz"
                tempmgr.PwdUserTmpFile.close()
                os.system(f'tar -zcvf "backup/TSL-SYSTEM-BACKUP-FILES/{filename}" ' +
                          ' '.join([file for file in SYSTEM_FILES if file != 'backup'])
                          )
                print('\nSuccessfully create an current system image.\n')
                logger.info(f"{USERNAME} create an current system image. [IMAGEINFO:'{filename}']")
                tempmgr.PwdUserTmpFile = open(os.path.join(SYSTEM_DIR, 'Temp/PwdUser'), 'r+')
            elif cmd_tmp[0] == 'restore' and len(cmd_tmp) <= 2:
                if not is_root:
                    print('sh: restore: Permission denied.\n')
                    logger.info(f"{USERNAME} failed to execute 'restore' because {USERNAME} is a SimpleUser. "
                                f"[CMDINFO:('restore', '{cmd_tmp[1:]}')]"
                                )
                    continue
                if '-l' in cmd_tmp:
                    if not Images:
                        print("Empty images in BACKUP_DIR.")
                        logger.warning(f"'{USERNAME}' tried to list exists images and chose one to execute 'restore', "
                                       "but this operation was blocked because there were no previous backup images. "
                                       f"[USERINFO:('{USERNAME}')]"
                                       )
                    else:
                        print('\nAvailable system images:')
                        for imagefile in Images:
                            print(imagefile)
                        print('')
                elif '-l' not in cmd_tmp and len(cmd_tmp) == 2:
                    image = cmd_tmp[1]
                    imagepath = os.path.join(ImagePath, image)
                    restore(USERNAME, is_root, imagepath, cmd_tmp, tempmgr, usermgr, logger)
                else:
                    image = input('Please input image filename to recover this system: ').strip()
                    if image == '':
                        continue
                    imagepath = os.path.join(ImagePath, image)
                    restore(USERNAME, is_root, imagepath, cmd_tmp, tempmgr, usermgr, logger)
            elif cmd_tmp[0] == 'user' and len(cmd_tmp) >= 2:
                if cmd_tmp[1] not in ['add', 'remove', 'info', 'set', 'list']:
                    print(f"AttitudeError:assignment '{cmd_tmp[1]}' is not defined in UserManager.\n")
                    continue
                else:
                    if len(cmd_tmp) == 2 and cmd_tmp[1] != 'list':
                        print(f"ArgumentError:cannot find any arguments followed by '{cmd_tmp[1]}'.\n")
                        continue
                if cmd_tmp[2] in ['--mode', '--password'] if len(cmd_tmp) > 2 else False:
                    if cmd_tmp[1] != 'list':
                        print("CommandError:invaild user command format:"
                              f"'{cmd_tmp[2]}' cannot be followed by '{cmd_tmp[1]}'!\n"
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
                            print(f"NameError:user '{opt_username}' is not exists, "
                                  "the interpreter will ignore the request to delete it.\n"
                                  )
                            continue
                elif cmd_tmp[1] == 'list' and len(cmd_tmp) <= 4:
                    if len(cmd_tmp) != 2:
                        mode = cmd_tmp[cmd_tmp.index('--mode') + 1] if '--mode' in cmd_tmp \
                            and cmd_tmp[-1] != '--mode' else \
                            cmd_tmp[2] if len(cmd_tmp) == 3 else \
                            exec("print('SyntaxError:invaild UserManager.list called format.\n')")
                        if mode is None:
                            continue
                        usermgr.list(mode)
                    else:
                        print("ParameterWarning:unclarified parameter mode, default set 'all' to it.\n")
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
                        continue
                    else:
                        usermgr.set(key, target, value)
                else:
                    if cmd_tmp[1] not in ['add', 'remove', 'list', 'info', 'set']:
                        print(f"AttitudeError:assignment '{cmd_tmp[1]}' is not defined in UserManager.\n")
                    else:
                        print(f"SyntaxError:invaild UserManager.{cmd_tmp[1]} called format.\n")
                    continue
            elif cmd_tmp[0] == 'help' and len(cmd_tmp) <= 2:
                if len(cmd_tmp) == 1:
                    print('\nSystem Usage Help Page\n')
                    print('System built-in commands:')
                    Help(helpdict)
                else:
                    print('')
                    HelpPage(HelpPages_DIR, PageReader, cmd_tmp[1])
            elif cmd_tmp[0] == 'logger' and len(cmd_tmp) >= 2:
                if cmd_tmp[1] not in ['list', 'read', 'write', 'delete', 'flush']:
                    print(f"AttitudeError:assignment '{cmd_tmp[1]}' is not defined in LoggerManager.\n")
                    continue
                else:
                    if len(cmd_tmp) == 2 and cmd_tmp[1] != 'list':
                        print(f"ArgumentError:cannot find any arguments followed by '{cmd_tmp[1]}'.\n")
                        continue

                if cmd_tmp[1] == 'list' and len(cmd_tmp) == 2:
                    loggermgr.list()
                elif cmd_tmp[1] == 'read' and len(cmd_tmp) == 3:
                    logtime = cmd_tmp[-1]
                    loggermgr.read(logtime)
                elif cmd_tmp[1] == 'write' and len(cmd_tmp) >= 4:
                    if cmd_tmp[-1] == '--log':
                        print("ParameterWarning:unclarified '--log' parameter, default set 'stdout' to it.")
                    logfile = cmd_tmp[-1] if cmd_tmp[-2] == '--log' and command.count('--log') == 1 else 'stdout'
                    if not logfile.endswith('.log') and logfile != 'stdout':
                        print('ValueError:invaild logfile format.\n')
                        continue

                    level = cmd_tmp[2]
                    if level not in loggermgr.logcolors.keys():
                        print('KeyError:unrecognized level parameter key.\n')
                        continue

                    message = " ".join(cmd_tmp[3:] if '--log' not in cmd_tmp[-2:] else cmd_tmp[3:-2])
                    if message.count('"') != 2 or not message.startswith('"') or not message.endswith('"'):
                        print("ValueError:unrecognized message parameter format.\n")
                        continue

                    loggermgr.write(level, message, logfile)
                elif cmd_tmp[1] == 'delete' and len(cmd_tmp) == 3:
                    if is_root:
                        loggermgr.delete(cmd_tmp[-1])
                    else:
                        print('sh: logger: Permission denied.')
                        logger.error(f"Failed to execute 'logger delete' because {USERNAME} is a SimpleUser. "
                                     f"[CMDINFO:{cmd_tmp}]"
                                     )
                        print()
                        continue
                elif cmd_tmp[1] == 'flush':
                    loggermgr.flush()
                else:
                    if cmd_tmp[1] not in ['list', 'read', 'write', 'delete', 'flush']:
                        print(f"AttitudeError:assignment '{cmd_tmp[1]}' is not defined in LoggerManager.\n")
                    else:
                        print(f"SyntaxError:invaild LoggerManager.{cmd_tmp[1]} called format.\n")
                    continue
                print()
            elif cmd_tmp[0] == "exit" and len(cmd_tmp) == 1:
                print('System shutdown ... ', end='', flush=True)
                time.sleep(1)
                print('done.\n')
                usermgr.databasefile.close()
                logger.info("UserManager hostdown.")
                tempmgr.WritePwdUser()
                tempmgr.PwdUserTmpFile.close()
                logger.info("TempManager hostdown.")
                logger.info("System Terminal hostdown.")
                time.sleep(0.5)
                return 0
            elif cmd_tmp[0] == 'logout' and len(cmd_tmp) == 1:
                print(f"User '{USERNAME}' logout ... ", end='', flush=True)
                usermgr.databasefile.close()
                tempmgr.WritePwdUser()
                tempmgr.PwdUserTmpFile.close()
                time.sleep(1)
                print('done.\n')
                return -1
            elif cmd_tmp[0] == 'init' and len(cmd_tmp) <= 2:
                cmd_tmp[1] = literal_eval(cmd_tmp[1])
                if not isinstance(cmd_tmp[1], int):
                    print(f"TypeError:syscode must be int not {gettype(cmd_tmp[1])}.")
                    continue
                else:
                    if is_root:
                        if (not cmd_tmp[1]) if len(cmd_tmp) == 2 else 0:
                            print('System shutdown ... ', end='', flush=True)
                            time.sleep(3)
                            print('done.\n')
                            usermgr.databasefile.close()
                            logger.info("UserManager hostdown.")
                            tempmgr.WritePwdUser()
                            tempmgr.PwdUserTmpFile.close()
                            logger.info("TempManager hostdown.")
                            logger.info("System Terminal hostdown.")
                            time.sleep(1)
                        if len(cmd_tmp) == 2:
                            return cmd_tmp[1]
                        else:
                            return 0
                    else:
                        print('sh: init: Permission denied.\n')
                        logger.info(f"{USERNAME} failed to execute 'init' because {USERNAME} is a SimpleUser. "
                                    f"[CMDINFO:('init', '{cmd_tmp[1]}')]"
                                    )
            elif cmd_tmp[0] == 'clear' and len(cmd_tmp) == 1:
                os.system(SYSTEM_CLEARSTDOUT)
                print('')
                os.system(f'{SYSTEM_PRINTER} motd')
                print('')
            elif (cmd_tmp[0] in ['trunc', 'internal', 'user', 'logger'] and len(cmd_tmp) == 1) \
                    or (cmd_tmp[0] in ['backup', 'exit', 'logout', 'clear'] and len(cmd_tmp) != 1) \
                    or (cmd_tmp[0] in ['restore', 'execute', 'init', 'help'] and len(cmd_tmp) > 2):
                print(f"CommandUsageError:incorrectly {cmd_tmp[0]} usage, "
                      f"please input 'help {cmd_tmp[0]}' to get its help-page.\n"
                      )
                continue
            else:
                print(
                    f"\033[31mTypeError:cannot execute '{cmd_tmp[0]}', "
                    "because trunc or internal type is unspecified!\033[0m\n"
                )
        except KeyboardInterrupt:
            print("\nCtrl-C")
            continue
