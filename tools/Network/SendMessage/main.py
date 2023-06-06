import os

target = os.popen('whoami').read().strip().split('\\')[-1]

os.system('msg /server:localhost {target}')
