import os
import gc
import getpass
import hashlib
from datetime import datetime
from ast import literal_eval
from loguru import logger
from termcolor import colored
from prettytable import PrettyTable
from config import SYSTEM_ID, SYSTEM_DIR, SYSTEM_LOGSTDOUT, SYSTEM_LOGPATH, SYSTEM_LOGFORMAT, SuperUser
from tools.Passwd.process import encrypt
from tools.__built_in__.IOProcessor import InputProcessor
from tools.__built_in__.TSLlogger import Logger
Logger()

if not SYSTEM_LOGSTDOUT:
    logger.remove(handler_id=None)

sysmgr_logger = logger.add(os.path.join(SYSTEM_LOGPATH, "log_{time:YYYY-MM}.log"),
                           format=SYSTEM_LOGFORMAT,
                           level="DEBUG",
                           rotation="32 MB",
                           enqueue=False
                           )


class TempManager:
    def __init__(self):
        self._ok = "True"
        self.PwdUserTmpFile = open(os.path.join(SYSTEM_DIR, 'Temp/PwdUser'), 'r+')

    def WritePwdUser(self, username='0'):
        self.PwdUserTmpFile.close()
        os.remove(os.path.join(SYSTEM_DIR, 'Temp/PwdUser'))
        self.PwdUserTmp = open(os.path.join(SYSTEM_DIR, 'Temp/PwdUser'), 'w')
        self.PwdUserTmp.write(username)
        self.PwdUserTmp.close()
        self.PwdUserTmpFile = open(os.path.join(SYSTEM_DIR, 'Temp/PwdUser'), 'r+')

    def ReadPwdUser(self):
        return str(self.PwdUserTmpFile.readlines()[0].strip())

    def CheckPwdUser(self):
        PwdUser = f'"{self.ReadPwdUser()}"'
        return tuple([literal_eval(PwdUser) == '0', PwdUser])

    def Flush(self, name):
        literal_eval(self._ok)
        print(f"Successfully flush the '{name}' temp.\n")
        return gc.collect()


class UserManager:
    def __init__(self, database_path, opuser):
        self.PwdUser = TempManager().ReadPwdUser()
        self.database = database_path
        self.databasefile = open(self.database, 'r')
        self.opuser = opuser
        self.userinfos = list(filter(lambda line: (not line.startswith('# ')) or line.strip() not in ['', '\n'], [userinfo for userinfo in self.databasefile.readlines() if (not userinfo.startswith('#')) or userinfo.strip() == '']))
        self.users = [user.split('@')[0] for user in self.userinfos]
        self.superusers = list(filter(lambda info: 'root' == info.split('@')[1], [userinfo.split(':')[0] for userinfo in self.userinfos]))
        self.UserTable = PrettyTable(['User', 'Mode'])
        self.InputProcessor = InputProcessor()

    def add(self, username: str, mode='user', password=False):
        if username not in self.users:
            if self.InputProcessor.Input_illegal_check(username, "username"):
                if username.isidentifier() and 4 <= len(username) <= 12:
                    if not password:
                        password_processor = hashlib.md5()
                        password = getpass.getpass(f"Please set a password to user '{username}': ")
                        if self.InputProcessor.Input_illegal_check(password, "password"):
                            if len(password) >= 6:
                                password = password.encode(encoding='utf-8')
                                password_processor.update(password)
                                password = password_processor.hexdigest()
                            else:
                                print("ValueError:invalid password format, length must be more than or equal to 6.")
                                logger.warning(f"'{self.PwdUser}' tried to add a new user to Login Database "
                                               f"but this operation was blocked because the password was invalid. "
                                               f"[USERINFO:('{username}', '{mode}')]"
                                               )
                                return -1
                        else:
                            print("ValueError:more than one illegal characters were found in the password.")
                            logger.warning(f"'{self.PwdUser}' tried to add a new user to Login Database "
                                           "but this operation was blocked because "
                                           "the password has invalid characters. "
                                           f"[USERINFO:('{username}', '{mode}')]"
                                           )
                            return -1

                    new_info = f'{username}@{mode}:{encrypt(password.strip(), 3, SYSTEM_ID[:6])}'
                    self.userinfos.append(new_info)
                    self.users.append(username)
                    self.superusers = [*self.superusers, username] if mode == 'root' else self.superusers
                    with open(self.database, 'a+') as addoptfile:
                        addoptfile.write(new_info)
                        addoptfile.write('\n')
                    print(f"Successfully add a user named '{username}' to login database.\n")
                    logger.info(f"'{self.PwdUser}' added a new user to Login Database successfully. "
                                f"[USERINFO:('{username}', '{mode}')]"
                                )
                else:
                    print("ValueError:the username must be a legal identifier, "
                          "and the length of it should be between 4 and 12."
                          )
                    logger.warning(f"'{self.PwdUser}' tried to add a new user to Login Database "
                                   f"but this operation was blocked because the username was invalid. "
                                   f"[USERINFO:('{username}', '{mode}')]"
                                   )
                    return -1
            else:
                print("ValueError:more than one illegal characters were found in the username.")
                logger.warning(f"'{self.PwdUser}' tried to add a new user to Login Database "
                               f"but this operation was blocked because the username has invalid characters. "
                               f"[USERINFO:('{username}', '{mode}')]"
                               )
                return -1
        else:
            print(f"UserExistsError:user '{username}' exists in login database!\n")
            logger.warning(f"'{self.PwdUser}' tried to add a user, "
                           "but this operation has been blocked because the user already existed in Login Database. "
                           f"[USERINFO:('{username}', '{mode}')]"
                           )
            return -1

    def remove(self, username):
        if username in self.users:
            if username != self.PwdUser:
                self.userinfos = list(filter(lambda user: username != user.split('@')[0], self.userinfos))
                self.users = [user.split('@')[0] for user in self.userinfos]
                self.rewrite(self.userinfos)
                self.superusers = list(filter(lambda info: 'root' == info.split('@')[1], [userinfo.split(':')[0] for userinfo in self.userinfos]))
                print(f"Successfully remove a user named '{username}' from login database.\n")
                logger.info(f"'{self.PwdUser}' removed a user from Login Database successfully. "
                            f"[USERINFO:('{username}')]"
                            )
            else:
                print('OperationForbidden:cannot remove user from I/O, user has been using.\n')
                logger.warning(f"'{self.PwdUser}' tried to remove a user from Login Database,"
                               "but this operation has been blocked because the user was in used. "
                               f"[USERINFO:('{username}')]"
                               )
                return -1
        else:
            print(f"UserNotExistsError:cannot found user named '{username}' in database.\n")
            logger.warning(f"'{self.PwdUser}' tried to remove a user from Login Database,"
                           "but this operation has been blocked because the user does not exist in Login Database. "
                           f"[USERINFO:('{username}')]"
                           )
            return -1

    def list(self, mode):
        if mode == 'all':
            for userRow in self.userinfos:
                self.UserTable.add_row(userRow.split(':')[0].split('@'))
            logger.info(f"'{self.PwdUser}' called the Login Database and got all users' info successfully. "
                        f"[GETINFO:('All Users', 'All Users Mode')]"
                        )
        elif mode in ['root', 'user']:
            userRows = list(filter(lambda info: mode == info.split('@')[1],
                                   [userinfo.split(':')[0] for userinfo in self.userinfos]))
            for userRow in userRows:
                self.UserTable.add_row(userRow.split('@'))
            logger.info(f"'{self.PwdUser}' called the Login Database and got all the {mode} users' info successfully. "
                        f"[GETINFO:('All {mode} Users', '{mode}')]"
                        )
        else:
            logger.warning(f"'{self.PwdUser}' called the Login Database and tried to get the users' info,"
                           f"but this operation was blocked because the specified mode is not defined. "
                           f"[GETINFO:(None, None)]"
                           )
            print(f"ValueError:mode '{mode}' is not defined in ModeTuple.\n")
            return -1

        print(self.UserTable, '\n')
        del self.UserTable
        self.UserTable = PrettyTable(['User', 'Mode'])

    def info(self, username):
        if username in self.users:
            for userRow in self.userinfos:
                if username == userRow.split('@')[0]:
                    self.UserTable.add_row(userRow.split(':')[0].split('@'))
                    logger.info(f"'{self.PwdUser}' called the Login Database and got the user's info successfully. "
                                f"[GETINFO:('{username}', '{userRow.split(':')[0].split('@')[1]}')]"
                                )
                    break
                else:
                    continue
            print(self.UserTable, '\n')
        else:
            print(f"UserNotExistedError:no such user named '{username}' was found in login database.\n")
            logger.warning(f"'{self.PwdUser}' called the Login Database and tried to got the user's info,"
                           "but this operation failed because the user does not exist in Login Database. "
                           f"[GETINFO:('{username}', None)]"
                           )

        del self.UserTable
        self.UserTable = PrettyTable(['User', 'Mode'])

    def set(self, key, target=None, value: str = None):
        if target not in SuperUser:
            index = self.users.index(target) if target in self.users else None
            if index is None:
                print(f"UserNotExistsError:user '{target}' is not exists in database.\n")
                return -1
            infotmp = self.userinfos[index].split(':')

            if key == 'username':
                if self.InputProcessor.Input_illegal_check(value, key):
                    if value.isidentifier() and 4 <= len(value) <= 12:
                        if target != value:
                            self.userinfos[index] = f"{value}@{self.userinfos[index].split('@')[1]}"
                            self.users[index] = value
                            self.rewrite(self.userinfos)
                            logger.info(f"'{self.PwdUser}' changed the user's name successfully. "
                                        f"[OPERATEINFO:('{target}' -> '{value}')]"
                                        )
                            print('Successfully operate the login database.\n')
                        else:
                            print("Nothing happen because username is not changed.")
                    else:
                        print("ValueError:the username must be a legal identifier, "
                              "and the length of it should be between 4 and 12."
                              )
                        return -1
                else:
                    print("ValueError:more than one illegal characters were found in the username.")
                    return -1
            elif key == 'mode':
                _old_value = self.userinfos[index].split(':')[0].split('@')[1]
                if _old_value != value:
                    self.userinfos[index] = f"{infotmp[0].split('@')[0]}@{value}:{infotmp[1]}"
                    self.rewrite(self.userinfos)
                    self.superusers.remove(infotmp[0].split('@')[0]) if value == 'user' else self.superusers.append(infotmp[0].split('@')[0])
                    logger.info(f"'{self.PwdUser}' changed the user's mode successfully. "
                                f"[USERINFO:('{target}', '{_old_value}' -> '{value}')]"
                                )
                    print('Successfully operate the login database.\n')
                else:
                    print("Nothing happen because mode is not changed.")
            elif key == 'password':
                if value is None or len(value) >= 6:
                    passwd_processor = hashlib.md5()
                    original_password = getpass.getpass('Original Password:')
                    original_password = original_password.encode(encoding='utf-8')
                    passwd_processor.update(original_password)
                    original_password = passwd_processor.hexdigest()
                    oldpasswd = encrypt(original_password, 3, SYSTEM_ID[:6])
                    del passwd_processor
                    if oldpasswd.strip() == infotmp[1].strip():
                        passwd_processor = hashlib.md5()
                        if value is None:
                            value = getpass.getpass('New Password: ')
                            if self.InputProcessor.Input_illegal_check(value, key):
                                if len(value) < 6:
                                    print("ValueError:invalid password format, length must be more than or equal to 6.")
                                    return -1
                            else:
                                print("ValueError:more than one illegal characters were found in the password.")
                                return -1
                        else:
                            if not self.InputProcessor.Input_illegal_check(value, key):
                                print("ValueError:more than one illegal characters were found in the password.")
                                return -1
                        value = value.encode(encoding='utf-8')
                        passwd_processor.update(value)
                        value = passwd_processor.hexdigest()

                        del passwd_processor
                        passwd_processor = hashlib.md5()
                        confirmpasswd = getpass.getpass('Confirm Password:')
                        confirmpasswd = confirmpasswd.encode(encoding='utf-8')
                        passwd_processor.update(confirmpasswd)
                        confirmpasswd = passwd_processor.hexdigest()
                        del passwd_processor
                        if confirmpasswd.strip() == value.strip():
                            if original_password.strip() != value.strip():
                                self.userinfos[index] = f"{infotmp[0]}:{encrypt(value, 3, SYSTEM_ID[:6])}\n"
                                self.rewrite(self.userinfos)
                                print('Successfully operate the login database.\n')
                                logger.info(f"'{self.PwdUser}' changed the user's password successfully. "
                                            f"[USERINFO:('{target}', '{infotmp[1]}' -> '{encrypt(value, 3, SYSTEM_ID[:6])}')]"
                                            )
                                del value, confirmpasswd, original_password
                            else:
                                print("Nothing will happen because password is not changed.")
                        else:
                            print("ValueError:confirmed password does not match the new password.\n")
                            return -1
                    else:
                        print("ValueError:uncorrectly original password, so UserMgr cannot "
                              "get the permission to change the target's password.\n"
                              )
                        logger.warning(f"'{self.PwdUser}' tried to change the user's password, "
                                       "but this operation has been blocked because "
                                       "the user's original password does not match the password entered. "
                                       f"[USERINFO:('{target}')]"
                                       )
                        return -1
                else:
                    print("ValueError:invalid password format, length must be more than or equal to 6.")
                    return -1
            else:
                print(f"KeyError:key '{key}' is not defined in UserMgr.set._keys.\n")
                return -1
        else:
            print("PermissionError:UserManager cannot set the SuperUser's attribute, permission denied.")
            return -1

        return

    def rewrite(self, context):
        self.databasefile.close()
        os.remove(self.database)
        with open(self.database, 'w') as rewriteoptfile:
            rewriteoptfile.write('# Username@Mode:HashPasswd\n')
            for info in context:
                rewriteoptfile.write(info)
        rewriteoptfile.close()
        self.databasefile = open(self.database, 'r')

    def issuperuser(self, username):
        return True if username in self.superusers else False


class LoggerManager:
    def __init__(self, logpath, printer):
        self.LOGPATH = logpath
        self.printer = printer
        if not os.path.exists(self.LOGPATH):
            os.makedirs(self.LOGPATH)
        self.logfiles = [logfile for logfile in os.listdir(self.LOGPATH) if logfile.endswith('.log')]
        self.logfilesindex = [logfile.split('_')[1].split('.')[0] for logfile in self.logfiles]
        self.logcolors = {'info': 'green', 'debug': 'cyan', 'warning': 'yellow', 'error': 'red', 'critical': 'red'}
        self.return_codes = {'RuntimeError': -1, 'Warning': 1, 'Normal': 0}

    def list(self):
        n = 0
        for logfileindex in self.logfilesindex:
            n = n + 1 if n <= 5 else 0
            if n > 5:
                print("")
            print(logfileindex, end='\t')
        print("")

    def read(self, logtime):
        logname = logtime if logtime.endswith('.log') else f"log_{logtime}.log"
        logfile = os.path.join(self.LOGPATH, logname)
        print("{0:-^37}".format(logtime))
        if logtime in self.logfilesindex and os.path.exists(logfile):
            os.system(f'{self.printer} "{logfile}"')
        else:
            print("An error was found when open the logfile, maybe it is missing.")
        print("{0:-^37}".format("The End"))

    def write(self, level, message, logfile="stdout"):
        logtext = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}"
        logtextlist = logtext.split(" ")
        attrs = ['bold'] if level == 'critical' else None
        logftext = " ".join([logtextlist[0], logtextlist[1],
                             f"[{colored(logtextlist[2][1:-1], color=self.logcolors[level], attrs=attrs)}]",
                             " ".join(logtextlist[3:])
                             ])
        if logfile != "stdout":
            if not logfile.isascii():
                print("ValueError:invalid logfile format, you may need to use 'help logger' to learn how to use it.")
                return -1
            else:
                with open(logfile, 'a+') as logf:
                    logf.write(logtext)
                    logf.write('\n')
        print(logftext)

    def delete(self, logtime):
        logname = logtime if logtime.endswith('.log') else f"log_{logtime}.log"
        logfile = os.path.join(self.LOGPATH, logname)
        if os.path.exists(logfile):
            os.remove(logfile)
        else:
            print("FileNotFoundError:cannot delete this logfile, the logfile does not exist.")

    def flush(self):
        print("RuntimeError:class method 'flush' is obsolete.")

        return self.return_codes['RuntimeError']
