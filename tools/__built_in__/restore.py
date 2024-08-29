#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os
from config import SYSTEM_DIR

ImagePath = os.path.join(SYSTEM_DIR, 'backup/TSL-SYSTEM-BACKUP-FILES')
Images = [fileimg for fileimg in os.listdir(ImagePath) if fileimg.endswith('.tar.gz')]


def restore(username, is_root, imagepath, cmd_tmp, tempmgr, usermgr, logger):
    if os.path.exists(imagepath):
        if is_root:
            tempmgr.PwdUserTmpFile.close()
            usermgr.databasefile.close()
            os.system(f'tar -xzvf "{imagepath}" -m -p')
            print('\nSuccessfully restore system from the image.\n')
            logger.info(f"Successfully restore system from the image. [USERINFO:('{username}')]")
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
