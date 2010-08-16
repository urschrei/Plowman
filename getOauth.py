import webbrowser
import sys
import tweepy

"""
    Query the user for their consumer key/secret
    then attempt to fetch a valid access token.
"""


def get_creds(creds):
	""" docstring
	"""
	print """I will now attempt to open a web browser to create an OAuth key.
	If you have previously obtained a consumer key and secret, you may close
	the browser window, and enter them here. Otherwise, follow the
	instructions on screen, and refer to
	http://jmillerinc.com/2010/05/31/twitter-from-the-command-line
	-in-python-using-oauth/
	for instructions.
	
	You may manually access the page at: https://dev.twitter.com/apps/new"""
	
	webbrowser.open(\
	"http://jmillerinc.com/2010/05/31/twitter-from-the-command\
	-line-in-python-using-oauth/")
	webbrowser.open("http://dev.twitter.com/apps/new")
	creds.append(raw_input('Consumer key: ').strip())
	creds.append(raw_input('Consumer secret: ').strip())
	autho = tweepy.OAuthHandler(creds[0], creds[1])
	
	# Open authorization URL in browser
	try:
		webbrowser.open(autho.get_authorization_url())
	except 	tweepy.error.TweepError:
		raise
	# Ask user for verifier pin
	pin = raw_input('Verification pin number from twitter.com: ').strip()
	# Get access token
	token = autho.get_access_token(verifier=pin)

	# Give user the access token
	print 'Access token:'
	print '  Key: %s' % token.key
	print '  Secret: %s' % token.secret
	creds.append(token.key)
	creds.append(token.secret)
	return creds