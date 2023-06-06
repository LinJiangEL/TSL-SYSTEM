from loading import start

_ok = "True"
Developing_list = ["Chemistry", "MultiMedia", "Philosophy"]
available_list = ["Mathematics", "Passwd", "Translate", "Network", "StudentsInfoDatabase"]


def Execute():
    while True:
        print('Please input the fullname of tool which you want to use. [Input "@available" to get the available list.]')
        tool_choice = input("> ")
        if tool_choice in Developing_list:
            print(f"The {tool_choice} tool is still developing! Please wait for some days to use it!")
        elif tool_choice == "exit":
            print('')
            break
        elif tool_choice == '@available':
            print(f"Available tools as follows:\n{available_list}\n")
        elif tool_choice == "":
            print()
            continue
        else:
            try:
                start(tool_choice)
            except StopIteration:
                continue
