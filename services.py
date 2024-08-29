#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os
import sys
import time
if sys.platform == 'win32':
    import win32api
    import win32serviceutil


def startService_linux(servicelist):
    for service in servicelist:
        print(f'Starting {service} service ... ', end='')
        os.popen(f'service {service} start')
        r = os.popen(f'service {service} status').read()
        if 'active (running)' in r:
            print("ok")
            time.sleep(0.01)
        elif 'inactive (dead)' in r:
            print('failed')
            time.sleep(0.01)
            raise RuntimeError(f'the {service} service cannot be started! Please make it sure.')
        elif r == f'Unit {service}.service could not be found.':
            raise OSError(f'service {service} could not be found on your PATH, please make it sure.')
        else:
            raise SystemError('unknown error!')


def startService_win32(servicelist):
    UNKNOWN = 0
    STOPPED = 1
    START_PENDING = 2
    STOP_PENDING = 3
    RUNNING = 4

    for service in servicelist:
        status = win32serviceutil.QueryServiceStatus(service)[1]

        print(f'Start {service} service ... ', end='')
        if status == STOPPED:
            win32serviceutil.StartService(service)
            win32api.Sleep(1000)
            statusx = win32serviceutil.QueryServiceStatus(service)[1]
            if statusx == STOPPED:
                print("ok")
            else:
                print("failed")
                sys.exit(256)
        elif status == RUNNING:
            print('exists')
        else:
            print('error')
