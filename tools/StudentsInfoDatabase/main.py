#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os
import sys
import time
import xlrd
from prettytable import PrettyTable
from config import SYSTEM_PRINTER

"""
Help:
    name xxx  /  name 'xxx'  /  name ""
    class 1
    zodiac 天蝎座  /  zodiac 天蝎座 --class 1
"""

Main_DIR = os.path.dirname(os.path.abspath(__file__))

def Zodiac(month, day) -> str:
    month = int(month)
    day = int(day)
    n = (u'摩羯座', u'水瓶座', u'双鱼座', u'白羊座', u'金牛座', u'双子座', u'巨蟹座', u'狮子座', u'处女座', u'天秤座', u'天蝎座', u'射手座')
    d = ((1, 20), (2, 19), (3, 21), (4, 21), (5, 21), (6, 22), (7, 23), (8, 23), (9, 23), (10, 23), (11, 23), (12, 23))
    a = list(filter(lambda y: y <= (month, day), d))
    return n[len(a) % 12]


def run():
    print('-' * 32)
    print('|' + ' ' * 5 + 'StudentsInfoDatabase' + ' ' * 5 + '|')
    print('-' * 32)
    time.sleep(0.5)

    database_file = xlrd.open_workbook(f'{Main_DIR}/Datas.xls')
    print('\nAvailable Database as follows:', database_file.sheet_names())
    database_sheet = input('\nPlease choose one from the Available list: ')
    if database_sheet in database_file.sheet_names():
        database_temp = database_file.sheet_by_name(database_sheet)
    else:
        print('DatabaseNotFoundError:cannot found this database from the Available list! Default use the first one.')
        database_temp = database_file.sheet_by_index(0)

    def make_birth_zodiac(info_index, table):
        zhixue_tmp = database_temp.row_values(info_index)[9]
        zhixue_id = int(zhixue_tmp) if zhixue_tmp != '' else 'N/A'

        if database_temp.row_values(info_index)[8] != 'N/A':
            birth = database_temp.row_values(info_index)[8][6:14]
            birth_temp = birth[-4:]
            zodiacmean = Zodiac(birth_temp[:2] if '0' not in birth_temp[:2] else birth_temp[1],
                                birth_temp[2:] if '0' not in birth_temp[2:] else birth_temp[3]
                                )
            table.add_row(list(map(str, list(map(int, database_temp.row_values(info_index)[:2])))) +
                          database_temp.row_values(info_index)[2:9] +
                          [zhixue_id] +
                          [birth, zodiacmean]
                          )
        else:
            birth = 'N/A'
            zodiacnomean = 'N/A'
            table.add_row(list(map(str, list(map(int, database_temp.row_values(info_index)[:2])))) +
                          database_temp.row_values(info_index)[2:9] +
                          [zhixue_id] +
                          [birth, zodiacnomean]
                          )
    print('\nStarting database service ... ', end='')

    database = PrettyTable(['班级', '学号', '姓名', '性别', '是否住宿', '语种', '组合', '艺体生', '身份证号', '智学网号'])
    database.add_column('出生日期', [])
    database.add_column('星座', [])

    for num in range(2, database_temp.nrows):
        make_birth_zodiac(num, database)

    time.sleep(3)
    print('done.\n')

    while True:
        key_word = input('Please input some keywords about the result [exit]：')
        if key_word == 'exit':
            if __name__ == '__main__':
                print('Stopping database ... ', end='')
                time.sleep(3)
                print('done.')
                break
            else:
                print('Stopping StudentsInfoDatabase Tool ...')
                time.sleep(1)
                if sys.platform == 'win32':
                    os.system(f'cls && echo. && {SYSTEM_PRINTER} motd && echo.')
                elif sys.platform == 'linux':
                    os.system(f'clear && echo && {SYSTEM_PRINTER} motd && echo')
                break
        elif key_word == 'all':
            print(database)
        elif key_word.startswith('class') and len(key_word.strip()) > 6:
            classindex = int(key_word[6:].strip())
            classTable = PrettyTable(['班级', '学号', '姓名', '性别', '是否住宿', '语种', '组合', '艺体生', '身份证号', '智学网号'])

            if classindex in [num for num in range(1, 18)]:
                classTable.add_column('出生日期', [])
                classTable.add_column('星座', [])
                for i in range(2, database_temp.nrows):
                    if int(database_temp.cell_value(rowx=i, colx=0)) == classindex:
                        make_birth_zodiac(i, classTable)
                    elif int(database_temp.cell_value(rowx=i, colx=0)) > classindex:
                        break
                    else:
                        continue

                print(classTable)
            else:
                print('IndexError:class index out of database!')
        elif key_word.startswith('name') and len(key_word.strip()) > 5:
            name = key_word.split(' ')[1].strip("' '").strip('"')
            names = database_temp.col_values(2)
            if name and name in database_temp.col_values(2):
                print(database.get_string(start=names.index(name) - 2, end=names.index(name) - 1))
            else:
                print(f'StudentNotFoundError:cannot found the student named {name}! '
                      f'Had he or she registered in the school database?'
                      )
        elif key_word.startswith('zodiac') and len(key_word.strip()) > 5:
            zodiacTable = PrettyTable(['班级', '学号', '姓名', '性别', '出生日期', '星座'])
            command = key_word.split(' ')
            if len(command) == 2:
                for index in range(2, database_temp.nrows):
                    z = database_temp.cell_value(rowx=index, colx=8)
                    if z != 'N/A':
                        zodiac = Zodiac(z[10:12].strip('0'), z[12:14].strip('0'))
                        if zodiac == key_word.split(' ')[1].strip(' " ').strip("'"):
                            zodiacTable.add_row([int(float(database_temp.cell_value(rowx=index, colx=0))),
                                                 int(float(database_temp.cell_value(rowx=index, colx=1))),
                                                 database_temp.cell_value(rowx=index, colx=2),
                                                 database_temp.cell_value(rowx=index, colx=3),
                                                 z[6:14],
                                                 Zodiac(z[10:12].strip('0'), z[12:14].strip('0'))
                                                 ])
                        else:
                            continue
                    else:
                        continue
                print(zodiacTable)
            elif 3 < len(command) < 5 and command[2].strip(' " ').strip("'") == '--class':
                class_num = int(command[3].strip(' " ').strip("'"))
                for index in range(2, database_temp.nrows):
                    z = database_temp.cell_value(rowx=index, colx=8)
                    if z != 'N/A':
                        zodiac = Zodiac(z[10:12].strip('0'), z[12:14].strip('0'))
                        if zodiac == key_word.split(' ')[1].strip(' " ').strip("'") \
                                and int(database_temp.cell_value(rowx=index, colx=0)) == class_num:
                            zodiacTable.add_row([int(float(database_temp.cell_value(rowx=index, colx=0))),
                                                 int(float(database_temp.cell_value(rowx=index, colx=1))),
                                                 database_temp.cell_value(rowx=index, colx=2),
                                                 database_temp.cell_value(rowx=index, colx=3),
                                                 z[6:14],
                                                 Zodiac(z[10:12].strip('0'), z[12:14].strip('0'))
                                                 ])
                        else:
                            continue
                    else:
                        continue
                print(zodiacTable)
            else:
                print('CommandError:incorrect command usage! [Wrong : Assignment]')
        elif key_word.strip() in ['name', 'class', 'zodiac']:
            print('CommandError:incorrect command usage! [Wrong : Usage]')
        else:
            print(f'KeyError:invalid key "{key_word}"! [Wrong : Undefined Command]')
        print('')


if __name__ == '__main__':
    run()
    input('\nPress Enter to exit.')

print('')
