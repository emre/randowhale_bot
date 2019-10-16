# Installation

Requires Python3.6+ and a Mongodb server.

```
$ virtualenv -p python3.6 randowhale-env
$ git clone https://github.com/emre/randowhale.git
$ pip install -r requirements.txt
$ vim config.py
```

Running:

```
$ python run.py
```

It's always suggested to use a process manager to make sure the runner is always up and running. I use [supervisor](https://supervisord.org) to manage this kind of scripts, personally.

# Configuration

Config variables are pretty straight-forward.

```
PROBABILITY_DIMENSIONS = (
    (1, 25, 0.4),
    (25, 50, 0.3),
    (50, 75, 0.2),
    (75, 99, 0.09),
    (99, 100, 0.01),
)
BOT_ACCOUNT = "randowhale.test"
POSTING_KEY = "posting_key"
ACTIVE_KEY = "active_key"
MIN_AGE_TO_VOTE = 300  # 5 mins
MAX_AGE_TO_VOTE = 432000  # 5 days
MINIMUM_VP_TO_VOTE = 80 # in percent
VOTE_PRICE = "0.001 STEEM"
```
***

`PROBABILITY_DIMENSIONS` is the root of the **weighted** random number generator. First element in each item is the vote percent start, second element is the vote percent end, third element is the probability factor of the item.

For this configuration, There is a %40 chance that the vote will be between %1 and %25. There is a %30 chance the vote will be between %25 and %50, and so on.
