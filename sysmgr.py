import os
import getpass
import hashlib
from ast import literal_eval
from prettytable import PrettyTable
from config import SYSTEM_ID, SYSTEM_DIR
from tools.Passwd.process import encrypt


class TempManager:
    def __init__(self):
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

class UserManager:
    def __init__(self, database_path):
        self.PwdUser = TempManager().ReadPwdUser()
        self.database = database_path
        self.databasefile = open(self.database, 'r')
        self.userinfos = list(filter(lambda line: (not line.startswith('# ')) or line.strip() not in ['', '\n'],
                                     [userinfo for userinfo in self.databasefile.readlines() if (not userinfo.startswith('#')) or userinfo.strip() == '']))
        self.users = [user.split('@')[0] for user in self.userinfos]
        self.UserTable = PrettyTable(['User', 'Mode'])


    def add(self, username, mode='user', password=False):
        if username not in self.users:
            if not password:
                password_processor = hashlib.md5()
                password = getpass.getpass(f"Please set a password to new user named '{username}': ")
                password = password.encode(encoding='utf-8')
                password_processor.update(password)
                password = password_processor.hexdigest()

            new_info = f'{username}@{mode}:{encrypt(password.strip(), 3, SYSTEM_ID[:6])}'
            with open(self.database, 'a+') as addoptfile:
                addoptfile.write(new_info)
                addoptfile.write('\n')
            print(f"Successfully add a user named '{username}' to login database.\n")
        else:
            print(f"UserExistsError:user '{username}' exists in login database!\n")

    def remove(self, username):
        if username in self.users:
        	if username != self.PwdUser:
        		self.userinfos = list(filter(lambda user: username != user.split('@')[0], self.userinfos))
        		self.users = [user.split('@')[0] for user in self.userinfos]
        		self.rewrite(self.userinfos)
        		print(f"Successfully remove a user named '{username}' from login database.\n")
        	else:
        		print('OperationForbidden:cannot remove user from I/O, user has been using.\n')
        		return 256
        else:
        	print(f"UserNotExistsError:cannot found user named '{username}' in database.\n")
        	return 256

    def list(self, mode):
        if mode == 'all':
            for userRow in self.userinfos:
                self.UserTable.add_row(userRow.split(':')[0].split('@'))
        elif mode in ['root', 'user']:
            userRows = list(filter(lambda info: mode == info.split('@')[1], [userinfo.split(':')[0] for userinfo in self.userinfos]))
            for userRow in userRows:
                self.UserTable.add_row(userRow.split('@'))
        else:
            print(f"ValueError:mode '{mode}' is not defined in ModeTuple.\n")
            return 256
        
        print(self.UserTable, '\n')
        del self.UserTable
        self.UserTable = PrettyTable(['User', 'Mode'])


    def set(self, key, target=None, value=None):
        index = self.users.index(target) if target in self.users else None
        if index is None:
            print(f"UserNotExistsError:user '{target}' is not exists in database.\n")
            return 256
        infotmp = self.userinfos[index].split(':')
        
        if key == 'username':
            self.userinfos[index] = f"{value}@{self.userinfos[index].split('@')[1]}"
            self.rewrite(self.userinfos)
            print('Successfully operate the login database.\n')
        elif key == 'mode':
            self.userinfos[index] = f"{infotmp[0].split('@')[0]}@{value}:{infotmp[1]}"
            self.rewrite(self.userinfos)
            print('Successfully operate the login database.\n')
        elif key == 'password':
            passwd_processor = hashlib.md5()
            original_password = getpass.getpass('Original Password:')
            original_password = original_password.encode(encoding='utf-8')
            passwd_processor.update(original_password)
            original_password = passwd_processor.hexdigest()
            oldpasswd = encrypt(original_password, 3, SYSTEM_ID[:6])
            del original_password, passwd_processor
            if oldpasswd.strip() == infotmp[1].strip():
                passwd_processor = hashlib.md5()
                if value == None:
                    value = getpass.getpass('New Password: ')

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
                    self.userinfos[index] = f"{infotmp[0]}:{encrypt(value, 3, SYSTEM_ID[:6])}\n"
                    self.rewrite(self.userinfos)
                    print('Successfully operate the login database.\n')
                    del value, confirmpasswd
                else:
                    print("ValueError:confirmed password does not match the new password.\n")
                    return 256
            else:
                print("ValueError:uncorrectly original password, so UserMgr cannot get the permission to change the target's password.\n")
                return 256
        else:
            print(f"KeyError:key '{key}' is not defined in UserMgr.set._keys.\n")
            return 256

    def info(self, username):
        if username in self.users:
        	for userRow in self.userinfos:
        		if username == userRow.split('@')[0]:
        			self.UserTable.add_row(userRow.split(':')[0].split('@'))
        			break
        	print(self.UserTable, '\n')
        else:
        	print(f"UserNotExistedError:no such user named '{username}' was found in login database.\n")
        
        del self.UserTable
        self.UserTable = PrettyTable(['User', 'Mode'])
    
    def rewrite(self, context):
        self.databasefile.close()
        os.remove(self.database)
        with open(self.database, 'w') as rewriteoptfile:
            rewriteoptfile.write('# Username@Mode:HashPasswd\n')
            for info in context:
                rewriteoptfile.write(info)
        rewriteoptfile.close()
        self.databasefile = open(self.database, 'r')
