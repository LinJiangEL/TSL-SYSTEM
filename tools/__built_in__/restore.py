#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

import os
from config import SYSTEM_DIR
from tools.__built_in__.external import run

ImagePath = os.path.join(SYSTEM_DIR, 'backup/TSL-SYSTEM-BACKUP-FILES')
Images = [fileimg for fileimg in os.listdir(ImagePath) if fileimg.endswith('.tar.gz')]


def restore(username, is_root, imagepath, cmd_tmp, tempmgr, usermgr, logger):
    if os.path.exists(imagepath):
        if is_root:
            tempmgr.PwdUserTmpFile.close()
            usermgr.databasefile.close()
            restore_code = run(['tar', '-xzvf', imagepath, '-m', '-p'], cwd=SYSTEM_DIR)
            if restore_code == 0:
                print('\nSuccessfully restore system from the image.\n')
                logger.info(f"Successfully restore system from the image. [USERINFO:('{username}')]")
            else:
                print(f"RuntimeError:failed to restore system from the image, "
                      f"tar exited with code {restore_code}.\n"
                      )
                logger.error(f"Failed to restore system from the image because tar "
                             f"exited with code {restore_code}. [USERINFO:('{username}')]"
                             )
            tempmgr.PwdUserTmpFile = open(os.path.join(SYSTEM_DIR, 'Temp/PwdUser'), 'r+')
            usermgr.databasefile = open(os.path.join(SYSTEM_DIR, 'Database/login.db'), 'r')
        else:
            print('sh: restore: Permission denied.\n')
            logger.error(f"{username} failed to execute 'restore' because {username} is a SimpleUser. "
                         f"[CMDINFO:{cmd_tmp}]"
                         )
    else:
        print('FileNotFoundError:cannot find such image from BACKUP_DIR.\n')
        logger.error("Cannot restore system from the image, image was not found in BACKUP_DIR. "
                     f"[USERINFO:('{username}')]"
                     )
