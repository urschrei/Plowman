#!/usr/bin/python
# coding=utf-8
# This is useful: http://openbookproject.net//thinkCSpy/
# This, too: http://www.devshed.com/c/a/Python/Using-SQLite-in-Python/

# twitter: robo_dante/beatrice
# gmail: alighieribot2010/beatrice1265

import sys
import os
import sqlite3
sys.path.append("/Users/sth/scripts")
import tweepy

connection = sqlite3.connect('dc.db')
cursor = connection.cursor()
try:
	cursor.execute('SELECT position FROM position ORDER BY POSITION DESC LIMIT 1')
except sqlite3.OperationalError:
	print "Couldn't find the specified table. Creating…" 
	cursor.execute('CREATE TABLE position (id INTEGER PRIMARY KEY, position INTEGER, tweeted INTEGER)')
	lastline=0
	cursor.execute('INSERT INTO position VALUES (null, ?, ?)',(lastline, "1"))
	# set up a new blank table, and start off at line 0
	# retry logic goes here

# get the highest page number
row = cursor.fetchone()
lastline = row[0]
printline = lastline+1

print_this = list()
try:
	with open('dc.txt', "r") as t_file:
		for a_line in t_file:
			if not a_line.strip():
				continue
				# if we encounter a blank line, do nothing and carry on
			else:
				print_this.append(a_line)
				# we could just jump to a specific line in the file, but that appears to be tricky in Python
except IOError:
	print "Couldn't open the text file for reading. Exiting."
	sys.exit()

# tweepy stuff
auth = tweepy.BasicAuthHandler('robo_dante', 'beatrice')
api = tweepy.API(auth)


# TO-DO we'll want to make sure the line isn't a header, i.e. doesn't begin with "CANTO" etc.
post='l. ' + str(printline) + ': ' + print_this[lastline]
# check for exceptions:
try:
	api.update_status(post)
except:
	print "Something's gone wrong…"
	sys.exit()
# end of tweepy stuff

lastline = lastline + 1
cursor.execute('INSERT INTO position VALUES (null, ?, ?)',(lastline, "1"))
connection.commit()
