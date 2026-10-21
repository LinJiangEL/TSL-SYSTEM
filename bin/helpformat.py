#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

from ast import literal_eval
from prettytable import PrettyTable

def Help(helpDict):
	"""粗略的命令帮助界面。"""
	helpTable = PrettyTable(['Command', 'Usage'])
	helpTable.align['Command'] = 'l'
	helpTable.align['Usage'] = 'l'
	helpTable.title = 'Terminal Commands'
	helpTable.header = True
	helpTable.border = True
	helpTable.padding_width = 1
	for cmd, usage in helpDict.items():
		helpTable.add_row([literal_eval(cmd), literal_eval(usage)])

	print(helpTable, '\n')
