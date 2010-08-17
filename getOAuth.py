#!/usr/bin/env python
# coding=utf-8
"""
Attempt to obtain a consumer key/secret,
then attempt to fetch a valid access token.
"""
import webbrowser
import tweepy
import sys

def get_creds(creds):
	""" Obtain and return OAuth credentials from twitter.com
	Takes an empty list, and returns a list containing:
	consumer key
	consumer secret
	access key
	access secret
	"""
	print """\nI will now attempt to open a web browser to create an OAuth key.
	If you have previously obtained a Consumer key and secret, you may close
	the browser window, and enter them below. Otherwise, follow the
	instructions on screen, and refer to
	https://github.com/urschrei/Plowman/blob/master/readme.md
	for instructions. Be sure to choose "client", and "Read & Write access"
	"""
	inp = raw_input("Press Return to continue, or q then Return to quit...")
	if inp == "q":
		print "Abandoning OAuth process."
		raise tweepy.TweepError("OAuth process was abandoned")
	webbrowser.open("http://dev.twitter.com/apps/new")
	creds.append(raw_input('Consumer Key: ').strip())
	creds.append(raw_input('Consumer Secret: ').strip())
	autho = tweepy.OAuthHandler(creds[0], creds[1])

	# open authorisation URL in browser
	try:
		webbrowser.open(autho.get_authorization_url())
	except tweepy.TweepError:
		raise
	# ask user for verification pin
	pin = raw_input('Verification PIN from twitter.com: ').strip()
	# get access token
	token = autho.get_access_token(verifier=pin)

	# give user the access token
	print "Access token: "
	print "  Key: %s" % token.key
	print "  Secret: %s" % token.secret
	creds.append(token.key)
	creds.append(token.secret)
	return creds


def main():
	""" main function
	"""
	oac = []
	get_creds(oac)
	print "Consumer key: %s" % oac[0]
	print "Consumer secret: %s" % oac[1]
	print "Access key: %s" % oac[2]
	print "Access secret: %s" % oac[3]


if __name__ == '__main__':  
# only do comprehensive error handling if running in standalone mode
# thanks to Brad Wright (github.com/bradleywright) for this
	try:
	    main()
	except (KeyboardInterrupt, SystemExit):
	    # actually raise these so it exits cleanly
	    raise 
	except Exception, error:
	    # all other exceptions, so display the error
	    print error 
	else:
	    pass
	finally:
	    # exit once we've done everything else
	    sys.exit()
