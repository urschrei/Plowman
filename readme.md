# Description #

(With apologies to William Langland)  

A Python script designed to tweet an epic poem stored in a text file, line by line. Line position, line display number, and current header are stored in a SQLite 3 database. The script is configured to take account of header lines, and thus maintain line numbering (i.e. line numbers are reset to 1, and the new header is prepended as necessary.) The header configuration and display are particular to epic poetry in this case, allowing us to see the current book/passus/canto, and line, respectively.
[SQLite 3], The [Tweepy] library, as well as a valid Twitter username and password are required.

Future "features" include properly customisable settings, allowing multiple text/header/twitter instances to be stored, then called by reference.

[Tweepy]: http://github.com/joshthecoder/tweepy
[SQLite 3]: http://www.sqlite.org/