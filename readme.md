# Description #

(With apologies to [William Langland][2])  

A Python script designed to tweet an epic poem stored in a text file, line by line. Line position, line display number, current header, and a [SHA1][1] digest of the file which generated them are stored in a SQLite 3 database. The script is configured to take account of header lines, and thus maintain line numbering (i.e. line numbers are reset to 1, and the new header is prepended as necessary). In addition, the digest ensures that line generation will not continue if the file contents are edited in any way. If the file is modified (other than renaming), the script will reset to the first line of the text file. This mechanism also allows a single db to be used for many poems, the digest providing an excellent primary key. The header configuration and display are particular to epic poetry in this case, allowing us to see the current book/passus/canto and line number, respectively.
[SQLite 3], The [tweepy] library, as well as a [Twitter] account are required.
In order to authorise and make use of the script, you will require *OAuth API access to your Twitter account.* OAuth credentials are stored alongside the line position and file digest.

# Initial Setup #

These setup steps assume that you are familiar with a terminal, and that you have a terminal window open.

1. If you haven't already done so, download and install [tweepy], and sign up for a [Twitter] account
2. Copy `bookbyline.py`, `getOAuth.py`, and the text file containing your poem into a directory of your choosing (cron should be able to access it). Ensure that both of the python files have been [chmod]ded `a+x`
3. Switch back to your home directory (`cd ~`), and call the script as follows: `python /path/to/bookbyline.py -l -file /path/to/text.txt -header header1 header2 … headern`, where "header*n*" is a word (including punctuation, such as colons etc.) which will cause any line which begins with it to be treated as a header line
	* example: `python mydir/bookbyline.py -l -file mydir/assets/poem.txt -header Inferno: Purgatory: Paradise:`
4. When you first run the script, you will be prompted to create OAuth credentials, and the script will attempt to open your default browser on the <https://dev.twitter.com/apps/new> page.
5. Once you have signed into Twitter, you will have to complete a form with the following fields:
	* `Application Name:` this is the name of the application which will appear in your tweets, feel free to personalise it
	* `Description:` enter a brief description of what this application does
	* `Application Website:` enter the Plowman GitHub repository's URL
	* `Organization:` if you are part of an organisation, enter its name here
	* `Website:` if you or your organisation have a website, enter its URL here
	* `Application Type:` **ensure that this is set to `client`**
	* `Callback URL:` leave this blank
	* `Default Access type:` **ensure that this is set to `Read & Write`**
	* `Use Twitter for login:` leave this unchecked

6. Now, complete the Captcha, and press the `save` button.
7. On the next page, look for the following: `Consumer Key` and `Consumer Secret`. Copy the key, switch back to the terminal and paste it at the prompt, then press return. Repeat this process with the secret.
8. The browser will then be redirected to a page asking you if you would like to allow the application name you chose in step 5 to connect to your account. Click `allow`. You may wish to note the Consumer Key and Secret, as they can be used to re-authorise your application, should it become necessary.
9. On the next page, you will see a PIN. Copy this, switch back to the terminal, and paste it at the prompt, then press return. An `Access Key` and `Access Secret` will be displayed, the script will complete its initial setup, and tweet the first line of your chosen poem.
10. You may now add the command detailed in step 3 to your crontab if you wish it to be fully automated, or call it from the command line whenever you like.
11. You should see a new file, `tweet_books.sl3` in your home directory. This contains various settings and access keys for the account you just set up. If you remove it, or alter its contents, the script will reset, and you'll have to regenerate OAuth credentials. Don't move it unless you know what you're doing.

# Usage #

Standard usage: `python bookbyline.py [-l] -file file.txt -header header1 header2 header3 … headerN`  

Display usage help: `python bookbyline.py -h` 

Arguments:
>`-l` live switch: will tweet the line. If omitted, script prints to stdout  
>`-h`, `--help`			show this help message and exit  
>`-file` filename		the full path to a text file  
>`-header` header-line word [header-line word ...]  
>A case-sensitive list of words (and punctuation) which  
>will be treated as header lines. Enter as many as you  
>wish, separated by a space.  
>Example - Purgatory: BOOK Passus  



[tweepy]: http://github.com/joshthecoder/tweepy
[Twitter]: https://twitter.com/signup
[SQLite 3]: http://www.sqlite.org/
[chmod]: http://en.wikipedia.org/wiki/Chmod

[1]: http://en.wikipedia.org/wiki/Sha1 "Secure Hash Algorithm"

[2]: http://en.wikipedia.org/wiki/William_Langland "Author of "Piers Plowman""

