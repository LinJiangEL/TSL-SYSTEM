#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

from loading import start
from tools.__built_in__ import style
from tools.__built_in__.IOProcessor import read_input

_ok = "True"
Developing_list = ["Chemistry", "MultiMedia", "Philosophy"]
available_list = ["Mathematics", "Passwd", "Translate", "StudentsInfoDatabase", "Psychology", "Music",
                      "Network"]


def execute(tool=None):
    if tool is None:
        while True:
            style.muted('Please input the fullname of tool which you want to use. '
                        '[Input "@available" to get the available list.]'
                        )
            tool_choice = read_input(style.prompt('> '), 'terminal', strip=True)
            if tool_choice in Developing_list:
                style.warning(f"The {tool_choice} tool is still developing! Please wait for some days to use it!\n")
            elif tool_choice == "exit":
                print('')
                break
            elif tool_choice == '@available':
                style.info(f"Available tools as follows:\n{available_list}\n")
            elif tool_choice == "":
                print()
                continue
            else:
                try:
                    start(tool_choice)
                except StopIteration:
                    continue
    else:
        if tool in Developing_list:
            style.warning(f"The {tool} tool is still developing! Please wait for some days to use it!\n")
        else:
            try:
                start(tool)
            except StopIteration:
                return -1
