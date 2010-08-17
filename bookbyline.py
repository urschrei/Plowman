#!/usr/bin/env python
# coding=utf-8
""" 
This module reads a text file from disk, and tweets properly-
formatted lines from it, one or two lines at a time, depending on
whether it's a header line, or body text. The line position is stored in
a sqlite3 database, which will be created in the current working directory.
The module takes exactly two arguments: the file name (including path), and
the text to match against in order to designate a header line. The second
argument can be given as a single word, or a comma-separated list

Requires the Tweepy library: http://github.com/joshthecoder/tweepy
"""
import sys, hashlib, sqlite3, tweepy, datetime, logging, re, getOauth

# logging stuff
log_filename = '/var/log/twitter_books.log'
logging.basicConfig(filename=log_filename, level=logging.ERROR)
now = datetime.datetime.now()



class BookFromTextFile:
	""" Create a Book object from a text file. Takes two arguments:
	1. a filename, from which text will be read
	2. a string used to identify header lines
	A sqlite3 connection object is created, and an attempt is made to
	retrieve a row from a db matching the filename which was
	passed. If no db is found, a new db, table and row are created.
	"""
	def __init__(self, fname = None, hid = None):
		self.name = fname
		self.headers = hid.split(",")
		self.db_name = "tweet_books.sl3"
		
		# try to open the specified text file to read, and get its SHA1 digest
		# we're creating the digest from non-blank lines only, just because
		try:
			with open(self.name, "r") as t_file:
				get_lines = t_file.readlines()
		except IOError:
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " Couldn't open text file %s for reading.") % (self.name)
			sys.exit()
		self.lines = [l for l in get_lines if l.strip()]
		self.sha = hashlib.sha1("".join(self.lines)).hexdigest()
		sl_digest = (self.sha,)
		
		# create a SQLite connection, or create a new db and table
		try:
			self.connection = sqlite3.connect(self.db_name)
		except IOError:
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " Couldn't read from, or create a db. That's a show-stopper.")
			sys.exit()
		self.cursor = self.connection.cursor()
		try:
			self.cursor.execute \
			('SELECT * FROM position WHERE digest = ?',sl_digest)
		except sqlite3.OperationalError:
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " Couldn't find table \'position\'. Creating…")
			# set up a new blank table
			self.cursor.execute('CREATE TABLE position \
			(id INTEGER PRIMARY KEY, position INTEGER, displayline INTEGER, \
			header STRING, digest DOUBLE, conkey STRING, consecret STRING, \
			acckey STRING, accsecret STRING)')
		
		# try to select the correct row, based on the SHA1 digest
		row = self.cursor.fetchone()
		if row == None:
			# no rows were returned, so insert default values with new digest
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " New file found, inserting row. Digest:\n" + str(self.sha)) 
			try:
				# attempt to create OAuth credentials
				try:
					oa_vals = []
					getOAuth.get_creds(oa_vals)
				except tweepy.error.TweepError:
					print "Couldn't complete OAuth process. Fatal. Exiting."
					logging.error(now.strftime("%Y-%m-%d %H:%M") \
					+ " Couldn't complete OAuth setup. Unable to continue.")
					self.connection.rollback()
					sys.exit()
				
				self.cursor.execute \
				('INSERT INTO position VALUES \
				(null, ?, ?, null, ?, ?, ?, ?, ?)',(0, 0, self.sha,\
				oa_vals[0], oa_vals[1], oa_vals[2], oa_vals[3]))
				# and select it
				self.cursor.execute \
				('SELECT * FROM position WHERE digest = ?',sl_digest)
				row = self.cursor.fetchone()
			except sqlite3.OperationalError:
				logging.error(now.strftime("%Y-%m-%d %H:%M") \
				+ " Couldn't insert new row into table. Exiting")
				# close the SQLite connection, and quit
				self.connection.rollback()
				self.connection.close()
				sys.exit()
		# set instance attrs from the db
		self.db_lastline = row[1]
		self.displayline = row[2]
		self.prefix = row[3]
		self.consumer_key = row[5]
		self.consumer_secret = row[6]
		self.access_key = row[7]
		self.access_secret = row[8]
		
		# now slice the lines list so we have the next two untweeted lines
		# right slice index value is ONE LESS THAN THE SPECIFIED NUMBER)
		self.lines = self.lines[self.db_lastline:self.db_lastline + 2]
		
	def format_tweet(self):
		""" Properly format an input string based on whether it's a header
		line, or a poetry line. If the current line is a header
		(see self.headers),
		we join the next line and reset the line number to 1.
		
		Prints a properly-formatted poetry line, including book/canto/line.
		"""
		# match against any single member of self.headers
		comped = re.compile("^(" + "|".join(self.headers) + ")")
		try:
			if comped.search(self.lines[0]):
				self.displayline = 1
				# counter skips the next line, since we're tweeting it
				self.db_lastline += 2
				self.prefix = self.lines[0]
				output_line = ('%s\nl. %s: %s') \
				% (self.lines[0].strip(), str(self.displayline), \
				self.lines[1].strip())
				self.lines.append(output_line)
				return self.lines
		# means we've reached the end of the file
		except IndexError:
			logging.error(now.strftime("%Y-%m-%d %H:%M") + \
			" %s Reached %s EOF on line %s"
			% (str(sys.argv[0]), self.name, str(self.db_lastline)))
			sys.exit()
		# proceed by using the latest untweeted line
		self.displayline += 1
		# move counter to the next line
		self.db_lastline += 1
		output_line = ('%sl. %s: %s') \
		% (self.prefix, self.displayline, self.lines[0].strip())
		self.lines.append(output_line)
		return self.lines
		
	def emit_tweet(self):
		""" First call the format_tweet() function, which correctly formats
		the current object's line[] members, depending
		on what they are, then tweets the resulting string. It then writes the
		updated file position, line display number, and header values to the
		db
		"""
		self.format_tweet()
		auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
		auth.set_access_token(self.access_key, self.access_secret)
		api = tweepy.API(auth, secure=True)
		# don't print the line unless the db is updateable
		with self.connection:
			try:
				self.cursor.execute('UPDATE position SET position = ?,\
				displayline = ?, header = ?, digest = ? WHERE digest = ?', \
				(self.db_lastline, self.displayline, self.prefix, \
				self.sha, self.sha))
			except (sqlite3.OperationalError, IndexError):
				print "Wasn't able to update the db."
				logging.error(now.strftime("%Y-%m-%d %H:%M") \
				+ " %s Couldn't update the db") % (str(sys.argv[0]))
				sys.exit()
			try:
				#api.update_status(str(self.lines[-1]))
				print self.lines[-1]
			except tweepy.TweepError, err:
				logging.error(now.strftime("%Y-%m-%d %H:%M") + 
				" %s Couldn't update status. Error was: %s") \
				% (str(sys.argv[0]), err)
				#self.connection.rollback()
				sys.exit()
		self.connection.close()
		
			
def main():
	""" main function
	"""
	# first argument (argv[0]) is the abs. path + filename -- not what we want
	if len(sys.argv) != 3:
		print "Incorrect number of arguments. Please call the script like this: \
		bookbyline.py filename.txt header"
		logging.error(now.strftime("%Y-%m-%d %H:%M") + " %s " +  \
		+ " Incorrect number of arguments") % (str(sys.argv[0]))
		sys.exit()
	input_book = BookFromTextFile(sys.argv[1], sys.argv[2])
	input_book.emit_tweet()


if __name__ == '__main__':
	main()

