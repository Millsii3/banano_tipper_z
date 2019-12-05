mycursor = None
mydb = None
recipient_minimum = None
tip_bot_username = None
program_minimum = None
reddit = None
donate_commands = None

comment_footer = """\n\n
***\n\n
[*^(Banano)*](https://banano.cc)*^( | )*
[*^(Banano Faucets!)*](https://banano.cc/#faucets)*^( | )*
[*^(Banano Github)*](https://github.com/bananocoin/)*^( | )*
[*^(Banano Discord!)*](https://chat.banano.cc)*^( | )*
[*^(Banano Twitter)*](https://twitter.com/bananocoin)"""

help_text = """
Help from Banano Tipper! This bot was handles tips via the Banano cryptocurrency.
[Visit us on GitHub](https://github.com/bananocoin/banano_tipper_z)
or /r/banano for more information on its use and its status.\n\n

Banano Tipper works in two ways -- either publicly tip a user on a subreddit, or send a PM to /u/banano_tipper with a PM command below.\n\n
To tip 1 Banano on a comment or post on the r/banano subreddit, make a comment starting with:\n
    !ban 1\n
To tip anywhere on reddit, tag the bot as such (it won't post on the all subreddits, but it will PM the users):\n
    /u/banano_tipper 1
You can tip any amount above the program minimum of 1 Banano.\n\n

For PM commands, create a new message with any of the following commands (be sure to remove the quotes, '<'s and '>'s):\n
    'create' - Create a new account if one does not exist
    'send <amount or all> <user/address>' - Send Banano to a reddit user or an address
    'balance' or 'address' - Retrieve your account balance. Includes both pocketed and unpocketed transactions
    'minimum <amount>' - (default 1) Sets a minimum amount for receiving tips
    'silence <yes/no>' - (default 'no') Prevents the bot from sending you tip notifications or tagging in posts
    'history <optional: number of records>' - Retrieves tipbot commands. Default 10, maximum is 50.
    'percentage <percent>' - (default 10 percent) Sets a percentage of returned tips to donate to TipBot development
    'help' - Get this help message\n
If you wanted to send 1 Banano to ChocolateFudCake, reply:\n
    send 1 ChocolateFudCake\n
If you have any questions or bug fixes, please contact /u/ChocolateFudCake."""

welcome_create = """
Welcome to Banano Tipper, a reddit tip bot which allows you to tip and send the Banano Currency to your favorite redditors!
Your account is **active** and your Banano address is %s.\n\n

You will be receiving a tip of 1 Banano as a welcome gift! To load more Banano, try any of the the free
[Banano Faucets](https://banano.cc/#faucets), or deposit some,
or receive a tip from a fellow redditor!\n\n
***\n\n
Banano Tipper can be used in two ways. The most common is to tip other redditors publicly by replying to a comment on the Banano subreddit.
To tip someone 1 Banano, reply to their message with:\n\n
```!ban 1```\n\n
To tip a redditor on any subreddit, tag the bot instead of issuing a command:\n\n
```/u/banano_tipper 1```\n\n
In unfamiliar subreddits, the minimum tip is 1 Banano.\n\n
***\n\n
There are also PM commands by [messaging](https://reddit.com/message/compose/?to=banano_tipper&subject=command&message=type_command_here) /u/banano_tipper. Remove any quotes, <'s and >'s.\n\n
```send <amount> <valid_banano_address>``` Withdraw your Banano to your own wallet.\n\n
```send <amount> <redditor username>``` Send to another redditor.\n\n
```minimum <amount>``` Prevent annoying spam by setting a receiving tip minimum.\n\n
```balance``` Check your account balance.\n\n
```help``` Receive an in-depth help message.\n\n

View your account on (the block explorer)[https://creeper.banano.cc/explorer/account/%s].\n\n
If you have any questions, please post at /r/banano
"""

welcome_tipped = """
Welcome to Banano Tipper, a reddit tip bot which allows you to tip and send the Banano Currency to your favorite redditors!
You have just received a Banano tip in the amount of ```%.4g Banano``` at your address %s.\n\n
Please activate your account by replying to this message or any tips which are 30 days old will be returned to the sender.\n\n
To load more Banano, try any of the the free
[Banano Faucets](https://banano.cc/#faucets), or deposit some (click on the Banano Creeper link for a QR code).\n\n
***\n\n
Banano Tipper can be used in two ways. The most common is to tip other redditors publicly by replying to a comment on the Banano subreddit.
To tip someone 1 Banano, reply to their message with:\n\n
```!ban 1```\n\n
To tip a redditor on any subreddit, tag the bot instead of issuing a command:\n\n
```/u/banano_tipper 1```\n\n
In unfamiliar subreddits, the minimum tip is 1 Banano.\n\n
***\n\n
There are also PM commands by [messaging](https://reddit.com/message/compose/?to=banano_tipper&subject=command&message=type_command_here) /u/banano_tipper. Remove any quotes, <'s and >'s.\n\n
```send <amount> <valid_banano_address>``` Withdraw your Banano to your own wallet.\n\n
```send <amount> <redditor username>``` Send to another redditor.\n\n
```minimum <amount>``` Prevent annoying spam by setting a receiving tip minimum.\n\n
```balance``` Check your account balance.\n\n
```help``` Receive an in-depth help message.\n\n

View your account on Banano Creeper: https://creeper.banano.cc/explorer/account/%s\n\n
If you have any questions, please post at /r/banano
"""

new_tip = """
Somebody just tipped you %.4g Banano at your address %s. Your new account balance is:\n\n
Available: %s Banano\n\n
Unpocketed: %s Banano\n\n
Unpocketed Banano will be pocketed automatically. [Transaction on Banano Creeper](https://creeper.banano.cc/explorer/block/%s)\n\n
To turn off these notifications, reply with "silence yes".
"""

excluded_redditors = [
    'nano',
    'nanos',
    'btc',
    'xrb',
    'eth',
    'xrp',
    'eos',
    'ltc',
    'bch',
    'xlm',
    'etc',
    'neo',
    'bat',
    'aed',
    'afn',
    'all',
    'amd',
    'ang',
    'aoa',
    'ars',
    'aud',
    'awg',
    'azn',
    'ban',
    'bam',
    'bbd',
    'bdt',
    'bgn',
    'bhd',
    'bif',
    'bmd',
    'bnd',
    'bob',
    'bov',
    'brl',
    'bsd',
    'btn',
    'bwp',
    'byr',
    'bzd',
    'cad',
    'cdf',
    'che',
    'chf',
    'chw',
    'clf',
    'clp',
    'cny',
    'cop',
    'cou',
    'crc',
    'cuc',
    'cup',
    'cve',
    'czk',
    'djf',
    'dkk',
    'dop',
    'dzd',
    'egp',
    'ern',
    'etb',
    'eur',
    'fjd',
    'fkp',
    'gbp',
    'gel',
    'ghs',
    'gip',
    'gmd',
    'gnf',
    'gtq',
    'gyd',
    'hkd',
    'hnl',
    'hrk',
    'htg',
    'huf',
    'idr',
    'ils',
    'inr',
    'iqd',
    'irr',
    'isk',
    'jmd',
    'jod',
    'jpy',
    'kes',
    'kgs',
    'khr',
    'kmf',
    'kpw',
    'krw',
    'kwd',
    'kyd',
    'kzt',
    'lak',
    'lbp',
    'lkr',
    'lrd',
    'lsl',
    'lyd',
    'mad',
    'mdl',
    'mga',
    'mkd',
    'mmk',
    'mnt',
    'mop',
    'mru',
    'mur',
    'mvr',
    'mwk',
    'mxn',
    'mxv',
    'myr',
    'mzn',
    'nad',
    'ngn',
    'nio',
    'nok',
    'npr',
    'nzd',
    'omr',
    'pab',
    'pen',
    'pgk',
    'php',
    'pkr',
    'pln',
    'pyg',
    'qar',
    'ron',
    'rsd',
    'rub',
    'rwf',
    'sar',
    'sbd',
    'scr',
    'sdg',
    'sek',
    'sgd',
    'shp',
    'sll',
    'sos',
    'srd',
    'ssp',
    'stn',
    'svc',
    'syp',
    'szl',
    'thb',
    'tjs',
    'tmt',
    'tnd',
    'top',
    'try',
    'ttd',
    'twd',
    'tzs',
    'uah',
    'ugx',
    'usd',
    'usn',
    'uyi',
    'uyu',
    'uzs',
    'vef',
    'vnd',
    'vuv',
    'wst',
    'xaf',
    'xcd',
    'xdr',
    'xof',
    'xpf',
    'xsu',
    'xua',
    'yer',
    'zar',
    'zmw',
    'zwl',
]
