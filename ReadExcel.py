#!/usr/bin/python3

import openpyxl

book = openpyxl.load_workbook('c:\High_Usage_Report_2017-12-06.xlsm')

sheet = book.active

a1 = sheet['B15']
a2 = sheet['C15']
a3 = sheet.cell(row=16, column=4)



print(a1.value)
print(a2.value)
print(a3.value)