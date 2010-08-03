import sys
import os
import sqlite3
connection = sqlite3.connect('dc.db')
cursor = connection.cursor()
# cursor.execute('CREATE TABLE position (id INTEGER PRIMARY KEY, position INTEGER, tweeted INTEGER)')
# open sqlite db, and retrieve last row
# set some variable to the value of 'position': something = cursor.lastrowid
lastline = cursor.execute('SELECT position FROM position ORDER BY POSITION DESC LIMIT 1')
print(lastline)
lastline = lastline + 1

to_db = list()
with open('dc.txt', encoding='utf-8') as t_file:
	for a_line in t_file:
		if not a_line.strip():
			continue
			# if we encounter a blank line, do nothing and carry on
		else:
			to_db.append(a_line)
# printout = range(1,201)
# for counter in printout:
print(to_db[latestline])
cursor.execute('INSERT INTO position VALUES (null, ?, ?)',(latestline, "1"))
connection.commit()