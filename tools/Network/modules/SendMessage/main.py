import os

target = os.getlogin()
os.system(f'msg /server:localhost "{target}"')
