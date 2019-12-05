# Banano Tipper

 is a reddit tipping service to easily give Banano to your favorite redditors! [Banano](https://banano.cc) is a fast and feeless cryptocurrency that can be traded at numerous exchanges. Before using Banano Tipper.

### To get started with Banano Tipper, either:

A) **Create an account** by [sending a message](https://reddit.com/message/compose/?to=banano_tipper&subject=command&message=create) to /u/banano_tipper with 'create' or 'register' in the message body. You will receive a Banano address, to which you can add Banano\*. You will receive a 1 Banano tip for registering! Also, try any of the faucets at [Banano Facuets](https://banano.cc/#faucets) (\**Banano Tipper is in early beta! Only send small amounts of Banano*.)

\-or-

B) **Receive a Banano tip** from a fellow redditor, and you will automatically have an account made! be sure to activate it afterwards by [sending a message](https://reddit.com/message/compose/?to=banano_tipper&subject=command&message=create) to /u/banano_tipper.

Once you have funds in your account, you can tip other redditors, or send to Banano address via PM to /u/banano_tipper.

# Comment Replies:

Banano Tipper is intended for tipping on reddit posts and replies. On the subreddit r/banano you can tip and type a message like:

    !ban 1 This is great!

This will tip a redditor 1 Banano. !ban <amount> must be the first thing in your message OR the last thing. Such, this is also a valid tip:

    This is great! !ban 1

Or from anywhere on reddit, you can tip a commenter by:

    /u/banano_tipper 1 This is great!

or

    This is great! /u/banano_tipper 1

If the subreddit is a [friendly subreddit](https://www.reddit.com/r/banano), the bot will repsond with a message. If the subreddit is not friendly, a PM will be sent to both the sender and the recipient.

### NEW!

    !nanocenter <amount> <project>

such as

    !nanocenter 1 unity

for a list of NanoCenter projects, see the PM commands below.

# Private Messages

Banano Tipper also works by PM. [Send a message](https://reddit.com/message/compose/?to=banano_tipper&subject=command&message=type_command_here) to /u/banano_tipper for a variety of actions.

To send 1 Banano to ChocolateFudCake, include this text in the message body:

    send 1 /u/ChocolateFudCake
-or-

    send 1 ChocolateFudCake

To send 1 Banano to ban_3fudcakefr9jyw7b4kfafrgaekmd37ez7q4pmzuo1fd7wo9jo8gsha7z7e1c, include this text in the message body:

    send 1 ban_3fudcakefr9jyw7b4kfafrgaekmd37ez7q4pmzuo1fd7wo9jo8gsha7z7e1c

or send all your balance:

    send all ban_3fudcakefr9jyw7b4kfafrgaekmd37ez7q4pmzuo1fd7wo9jo8gsha7z7e1c

There are many other commands.

    'create' - Create a new account if one does not exist
    'send <amount or all, optional: Currency> <user/address>' - Send Banano to a reddit user or an address
    'withdraw <amount or all> <user/address>' - Same as send
    'balance' or 'address' - Retrieve your account balance. Includes both pocketed and unpocketed transactions
    'minimum <amount>' - (default 1) Sets a minimum amount for receiving tips
    'silence <yes/no>' - (default 'no') Prevents the bot from sending you tip notifications or tagging in posts
    'percentage <percent>' - (default 10 percent) Sets a percentage of returned tips to donate to TipBot development
    'history <optional: number of records>' - Retrieves tipbot commands. Default 10, maximum is 50.
    'projects' - Retrives a list of NanoCenter donation projects
    'help' - Get this help message

### Here's a few other great links:
[Banano Subreddit](https://reddit.com/r/banano) -- Post any questions about Banano

[Banano Tipper GitHub](https://github.com/bananocoin/banano_tipper_z) -- This software is open source!

[Banano Wesbite](https://banano.cc) -- The Official Banano website

[Banano Discord](https://chat.banano.cc) -- Where the party is at!

[Banano Twitter](https://www.twitter.com/bananocoin) -- To follow the latest Banano shenanigans

# Terms of Service
* Don't keep a lot of Banano in your Banano Tip Bot account
* You accept the risks of using this Tip Bot--I won't steal your Banano, but they might be lost at any point, and I'm under no obligation to replace them. Don't put in more than you're willing to lose.
* Don't submit more than 5 requests every 30 seconds. The bot will ignore any commands you issue until 30 seconds have passed.


# FAQ
## Why does the message have to start or end with !ban <amount>?
This is to prevent unintentional tips! If the program simply scanned the entire comment, a user might accidentally quote someone else's tip command in a response.

## Are my funds safe?
**NO! Unless you and you alone control your private keys, your funds are never safe!** Please don't keep large amounts on the tipbot at any time! This program is in early beta testing and weird things could happen, including lost funds! **Use at your own risk!**

## I sent a tip to the wrong address. Can I get it back?
 **No.** please be careful were you send your funds.

## Have you implemented any spam prevention for your bot?
Users are allowed 5 requests every 30 seconds. If you do more than that, the bot ignores you until 30 seconds have passed.

## I tried to send a tip, but received no response. Did it go through?
Probably not. It's most likely the bot was temporarily disconnected. If a command is issued while the bot is offline, the command will not be seen. If no response is received from the bot after a few minutes, send a message to the bot with the text 'history'. If you get a response and the tip isn't in your history, that means it wasn't seen. If you don't get a response, the bot is probably still offline. Try again in a few minutes.

## I found a bug or I have a concern. Question Mark?
Send /u/ChocolateFudCake a PM on reddit, or post on https://reddit.com/r/banano

# Error Codes
If a reddit tip is a reply to a reply, it's better to keep a short message with an error code.
* 0 - Could not read the tip command
* 1 - Could not read the tip amount -- use either a number or the word 'all', or if using currency conversion, make sure there is no space
* 2 - Sender does not have an account -- Create an account by typing 'create' or by receiving a tip from another redditor
* 3 - Tip amount is below program minimum -- This is to prevent spamming other redditors.
* 4 - Insufficient funds -- The amount of Banano in your account is lower than your tip amount. If you are using 'auto_receive' for your transactions, your account is scanned every 12 seconds.
* 5 - User or address not specified -- If you are sending via PM, you must specify the recipient. Make sure there aren't extra spaces.
* 6 - Address is invalid or recipient redditor does not exist -- You have a typo somewhere
* 7 - Recipient redditor does not exist -- The redditor you specified doesn't have a reddit account.
* 8 - Tip amount is below recipients specified tip minimum -- The recipient doesn't want to receive tips below a certain amount

and FYI there are success codes, but you won't see these

* 9 - Success! Sent to a redditor who requested silence -- This redditor will *not* receive a notification of their tip.
* 10 - Success! Sent to redditor -- Redditor will receive a notification on their tip
* 11 - Success! Sent to registered banano address -- If redditor has requested silence, they won't get a notification.
* 12 - Success! Sent to unregistered banano address
* 13 - Success! Sent to a newly created reddit account
* 14 - Success! Send to a NanoCenter project fund
