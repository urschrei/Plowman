import sys
import os
import sqlite3
connection = sqlite3.connect('dc.db')
cursor = connection.cursor()
# cursor.execute('CREATE TABLE position (id INTEGER PRIMARY KEY, position INTEGER, tweeted INTEGER)')
# This is useful: http://openbookproject.net//thinkCSpy/
# This, too: http://www.devshed.com/c/a/Python/Using-SQLite-in-Python/
# TO-DO:
# check if the following operation is successful.
# If not, then don't try setting row = cursor, or any of that other stuff
# The implication is that the script hasn't been run before
# Just set lastline = 0, then continue

cursor.execute('SELECT position FROM position ORDER BY POSITION DESC LIMIT 1')
row = cursor.fetchone()

lastline = row[0]
print(lastline+1)


print_this = list()
with open('dc.txt', encoding='utf-8') as t_file:
	for a_line in t_file:
		if not a_line.strip():
			continue
			# if we encounter a blank line, do nothing and carry on
		else:
			print_this.append(a_line)
			# we could just jump to a specific line in the file, but that appears to be tricky in Python
# substitute some form of tweeting mechanism for the next line
# maybe also prettify it, e.g. l.123: bla bla bla
print(print_this[lastline])
# if it's successful, execute the next three lines, else exit
lastline = lastline + 1
cursor.execute('INSERT INTO position VALUES (null, ?, ?)',(lastline, "1"))
connection.commit()