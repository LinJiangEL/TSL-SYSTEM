# -*- encoding:utf-8 -*-
import os
import sys
import time
from ast import literal_eval
from setuptools.errors import PlatformError
from loguru import logger
from bin.helpformat import Help
from config import SYSTEM_DIR, SYSTEM_LOGPATH, SYSTEM_LOGFORMAT, SYSTEM_LOGSTDOUT, \
    SuperUser, SYSTEM_FILES, SYSTEM_PRINTER
from sysmgr import TempManager, UserManager

if not SYSTEM_LOGSTDOUT:
    logger.remove(handler_id=None)

terminal_logger = logger.add(os.path.join(SYSTEM_LOGPATH, "log-{time:YYYY-MM}.log"),
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

    logger.info("Load sysmgr.UserManager.")
    usermgr = UserManager(os.path.join(SYSTEM_DIR, 'Database/login.db'))

    while os.path.exists(Bin_DIR):
        try:
            Bin_DIR = Bin_DIR.replace('\\', '/')
            command = input(f'{USERNAME}@TSL-SYSTEM {MODE} ').strip()
            cmd_tmp = [cmd_argv.strip() for cmd_argv in command.split(' ')]
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
            elif cmd_tmp[0] == "execute":
                from tools import execute
                execute.Execute()
                literal_eval(execute._ok)
            elif cmd_tmp[0] == 'backup':
                filename = f"TSL-SYSTEM_{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}.tar.gz"
                tempmgr.PwdUserTmpFile.close()
                os.system(f'tar -zcvf "backup/TSL-SYSTEM-BACKUP-FILES/{filename}" ' +
                          ' '.join([file for file in SYSTEM_FILES if file != 'backup'])
                          )
                print('\nSuccessfully create an current system image.\n')
                logger.info(f"{USERNAME} create an current system image. [IMAGEINFO:'{filename}']")
                tempmgr.PwdUserTmpFile = open(os.path.join(SYSTEM_DIR, 'Temp/PwdUser'), 'r+')
            elif cmd_tmp[0] == 'restore':
                if [fileimg for fileimg in os.listdir(os.path.join(SYSTEM_DIR, 'backup/TSL-SYSTEM-BACKUP-FILES'))
                        if fileimg.endswith('.tar.gz')] is []:
                    print("Empty images in BACKUP_DIR.")
                    logger.warning(f"'{USERNAME}' tried to list backup images and chose one to execute 'restore', "
                                   "but this operation was blocked because there were no previous backup images. "
                                   f"[USERINFO:('{USERNAME}')]"
                                   )
                else:
                    print('\nAvailable system images:')
                    for imagefile in [fileimg for fileimg in
                                      os.listdir(os.path.join(SYSTEM_DIR, 'backup/TSL-SYSTEM-BACKUP-FILES')) if
                                      fileimg.endswith('.tar.gz')]:
                        print(imagefile)
                    print('')

                    image = input('Please choose one image to recover this system: ')
                    imagepath = os.path.join(SYSTEM_DIR, 'backup/TSL-SYSTEM-BACKUP-FILES/%s' % image)
                    if os.path.exists(imagepath):
                        if is_root:
                            tempmgr.PwdUserTmpFile.close()
                            usermgr.databasefile.close()
                            os.system(f'tar -xzvf "{imagepath}" -m -p')
                            print('\nSuccessfully restore system from the image.\n')
                            logger.info(f"Successfully restore system from the image. [USERINFO:('{USERNAME}')]")
                            tempmgr.PwdUserTmpFile = open(os.path.join(SYSTEM_DIR, 'Temp/PwdUser'), 'r+')
                            usermgr.databasefile = open(os.path.join(SYSTEM_DIR, 'Database/login.db'), 'r')
                        else:
                            print('sh: restore: Permission denied.\n')
                            logger.error(f"{USERNAME} failed to execute 'restore' because {USERNAME} is a SimpleUser. "
                                         f"[CMDINFO:{cmd_tmp}]"
                                         )
                    else:
                        print('FileNotFoundError:cannot find such image from BACKUP_DIR.\n')
                        logger.error("Cannot restore system from the image, image was not found in BACKUP_DIR. "
                                     f"[USERINFO:('{USERNAME}')]"
                                     )
            elif cmd_tmp[0] == 'user' and len(cmd_tmp) >= 2:
                if cmd_tmp[1] not in ['add', 'remove', 'info', 'set', 'list']:
                    print(f"AttitudeError:assignment '{cmd_tmp[1]}' is not defined in UserManager.\n")
                    continue
                else:
                    if len(cmd_tmp) == 2 and cmd_tmp[1] != 'list':
                        print(f"ArgumentError:cannot find any arguments followed by '{cmd_tmp[1]}'.\n")
                        continue
                    else:
                        pass
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
                        print(f"OperationForbidden:cannot operate built-in user, currently pemission denied.\n")
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
                        exec("print('OperationInterupt:cannot get the new value.\n')") \
                        if key != 'password' else None
                    if value is None:
                        continue
                    usermgr.set(key, target, value)
                else:
                    if cmd_tmp[1] not in ['add', 'remove', 'list', 'info', 'set']:
                        print(f"AttitudeError:assignment '{cmd_tmp[1]}' is not defined in UserManager.\n")
                    else:
                        print(f"SyntaxError:invaild UserManager.{cmd_tmp[1]} called format.\n")
                    continue
            elif cmd_tmp[0] == 'help':
                print('\nSystem Usage Help Page\n')
                print('System built-in commands:')
                Help(helpdict)
            elif cmd_tmp[0] == 'logger':
                pass
            elif cmd_tmp[0] == "exit" or cmd_tmp[0] == 'logout':
                print('System shutting ... ', end='', flush=True)
                time.sleep(3)
                usermgr.databasefile.close()
                logger.info("UserManager hostdown.")
                tempmgr.WritePwdUser()
                tempmgr.PwdUserTmpFile.close()
                logger.info("TempManager hostdown.")
                print('done.\n')
                logger.info("System Terminal hostdown.")
                break
            elif cmd_tmp[0] == 'clear' and len(cmd_tmp) == 1:
                os.system(cmd_tmp[0])
                print('')
                os.system(f'{SYSTEM_PRINTER} motd')
                print('')
            elif cmd_tmp[0] in ['trunc', 'internal', 'user'] and len(cmd_tmp) == 1:
                print(f"CommandUsageError:incorrectly {cmd_tmp[0]} usage, please input 'help' to get its help-page.\n")
                continue
            else:
                print(
                    f"\033[31mTypeError:cannot execute '{cmd_tmp[0]}', "
                    "because trunc or internal type is unspecified!\033[0m\n"
                )
        except KeyboardInterrupt:
            print("\nCtrl-C")
            continue
