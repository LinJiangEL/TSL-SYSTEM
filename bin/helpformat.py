#  Copyright (c) 2024. L.J.Afres, All rights reserved.

from ast import literal_eval
from prettytable import PrettyTable

def Help(helpDict):
	helpTable = PrettyTable(['Command', 'Usage'])
	helpTable.align['Command'] = 'l'
	helpTable.align['Usage'] = 'l'
	for cmd, usage in helpDict.items():
		helpTable.add_row([literal_eval(cmd), literal_eval(usage)])

	print(helpTable, '\n')

