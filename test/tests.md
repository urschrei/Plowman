# Unit Tests #

These tests provide around 80% code coverage, the main exception being the [`DBconn._create_oauth()`][1] method. However, the [Tweepy][2] module on which the method primarily relies – essentially, it just calls a [wrapper][3] for Tweepy's OAuth functionality – is extensively covered by Tweepy's own [tests][4].  

[1]: https://github.com/urschrei/Plowman/blob/master/bookbyline.py#L162
[2]: https://github.com/joshthecoder/tweepy
[3]: https://github.com/urschrei/Plowman/blob/master/getOAuth.py#L162
[4]: https://github.com/joshthecoder/tweepy/blob/master/tests.py