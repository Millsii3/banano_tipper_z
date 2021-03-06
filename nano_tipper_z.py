import shared
import praw
import time
from datetime import datetime
from time import sleep
from rpc_bindings import open_account, generate_account, generate_qr, banoshi_to_raw, receive_all, send_all, \
    check_balance, validate_address, open_or_receive, get_pendings, open_or_receive_blocks, open_or_receive_block
from rpc_bindings import send_w as send
import mysql.connector
import configparser
import sys
from message_functions import *
from helper_functions import *

# access the sql library
config = configparser.ConfigParser()
config.read('./tipper.ini')

# config.sections()
sql_password = config['SQL']['sql_password']
database_name = config['SQL']['database_name']
tip_bot_on = config['BOT']['tip_bot_on']
tip_bot_username = config['BOT']['tip_bot_username']
program_minimum = float(config['BOT']['program_minimum'])
recipient_minimum = float(config['BOT']['recipient_minimum'])
tip_commands = config['BOT']['tip_commands'].split(',')
donate_commands = config['BOT']['donate_commands'].split(',')
tipbot_owner = config['BOT']['tipbot_owner']
cmc_token = config['OTHER']['cmc_token']

mydb = mysql.connector.connect(user='root', password=sql_password,
                              host='localhost',
                              auth_plugin='mysql_native_password', database=database_name)
mycursor = mydb.cursor()

# initiate the bot and all friendly subreddits
reddit = praw.Reddit('bot1')
mycursor.execute("SELECT subreddit FROM subreddits")
results = mycursor.fetchall()
subreddits=''
for result in results:
    subreddits += '%s+' % result[0]
subreddits = subreddits[:-1]
subreddit = reddit.subreddit(subreddits)

# a few globals. We'll put them in a shared file for use by other scripts
toggle_receive = True

# make a package with our shared objects. All of these shared variables are static
shared.cmc_token = cmc_token
shared.mycursor = mycursor
shared.mydb = mydb
shared.recipient_minimum = recipient_minimum
shared.tip_bot_username = tip_bot_username
shared.program_minimum = program_minimum
shared.reddit = reddit
shared.donate_commands = donate_commands

# and pull a few out!
excluded_redditors = shared.excluded_redditors
help_text = shared.help_text
new_tip = shared.new_tip
comment_footer = shared.comment_footer
welcome_tipped = shared.welcome_tipped
welcome_create = shared.welcome_create


# generator to stream comments and messages to the main loop at the bottom, and contains the auto_receive functionality.
# Maybe this wasn't necessary, but I never get to use generators.
# To check for new messages and comments, the function scans the subreddits and inbox every 6 seconds and builds a
# set of current message. I compare the old set with the new set.
def stream_comments_messages():
    previous_time = time.time()
    previous_comments = {comment for comment in subreddit.comments()}
    previous_messages = {message for message in reddit.inbox.all(limit=25)}
    global toggle_receive
    while True:
        if toggle_receive and tip_bot_on:
            auto_receive()
        toggle_receive = not toggle_receive

        delay = 6-(time.time()-previous_time)

        if delay <= 0:
            delay = 0
        sleep(delay)
        previous_time = time.time()
        updated_comments = {comment for comment in subreddit.comments()}
        new_comments = updated_comments - previous_comments
        previous_comments = updated_comments

        # check for new messages
        updated_messages = {message for message in reddit.inbox.all(limit=25)}
        new_messages = updated_messages - previous_messages
        previous_messages = updated_messages

        # send anything new to our main program
        # also, check the message type. this will prevent posts from being seen as messages
        if len(new_comments) >= 1:
            for new_comment in new_comments:
                # if new_comment starts with 't1_, it's just a regular comment'
                if new_comment.name[:3] == 't1_':
                    yield ('comment', new_comment)
        if len(new_messages) >= 1:
            for new_message in new_messages:
                # print(new_message, new_message.subject, new_message.body)
                if new_message.name[:3] == 't4_':
                    yield ('message', new_message)
                # if the message has any of these subjects and it is labeled t1_, it is a username tag
                elif (new_message.subject == "comment reply" or new_message.subject == "username mention" or new_message.subject == "post reply") and new_message.name[:3] == 't1_':
                    # print('****username mention + comment reply')
                    yield ('username mention', new_message)
        else:
            yield None


# handles tip commands on subreddits
def handle_comment(message, parsed_text=None):
    """
    Prepares a reddit comment starting with !ban to send banano if everything goes well
    :param message:
    :param parsed_text
    :return:
    """
    # remove an annoying extra space that might be in the front
    if parsed_text is None:
        if message.body[0] == ' ':
            parsed_text = parse_text(str(message.body[1:]))
        else:
            parsed_text = parse_text(str(message.body))

    # attempt to parse the message, send the Nano, and record responses
    # response is a 6-member list with some info
    # response[0] - message to the tip sender
    # response[1] - a status code
    # response[2] - Tip amount in 'Nano'
    # response[3] - reddit username
    # response[4] - reddit address
    # response[5] - transaction hash
    # If the recipient is new, it will automatically send a welcome greeting.
    response = handle_send_nano(message, parsed_text, 'comment')

    # apply the subreddit rules to our response message
    # potential statuses:
    #   friendly
    #   hostile
    #   minimal
    # if it is a friendly subreddit, just reply with the response + comment_footer
    # if it is not friendly, we need to notify the sender as well as the recipient if they have not elected silence
    # handle top level comment
    sql = 'SELECT status FROM subreddits WHERE subreddit=%s'
    val = (str(message.subreddit).lower(), )
    mycursor.execute(sql, val)
    results = mycursor.fetchall()

    if len(results) == 0:
        subreddit_status = 'hostile'
    else:
        subreddit_status = results[0][0]
    # if it is a top level reply and the subreddit is friendly
    if (str(message.parent_id)[:3] == 't3_') and (subreddit_status == 'friendly'):
        message.reply(response[0] + comment_footer)
    # otherwise, if the subreddit is friendly (and reply is not top level) or subreddit is minimal
    elif (subreddit_status == 'friendly') or (subreddit_status == 'minimal'):
        if response[1] <= 8:
            message.reply('^(Tip not sent. Error code )^[%s](https://github.com/bananocoin/banano_tipper_z#error-codes) ^- [^(Banano Tipper)](https://github.com/bananocoin/banano_tipper_z)'
                          % response[1])
        elif (response[1] == 9):
            message.reply('^[Sent](https://creeper.banano.cc/explorer/block/%s) ^%s ^Banano ^to ^%s ^- [^(Banano Tipper)](https://github.com/bananocoin/banano_tipper_z)'
                          % (response[5], response[2], response[3]))
        elif (response[1] == 10) or (response[1] == 13):
            # user didn't request silence or it's a new account, so tag them
            message.reply(
                '^[Sent](https://creeper.banano.cc/explorer/block/%s) ^%s ^Banano ^to ^(/u/%s) ^- [^(Banano Tipper)](https://github.com/bananocoin/banano_tipper_z)'
                % (response[5], response[2], response[3]))
        elif (response[1] == 11) or (response[1] == 12):
            # this actually shouldn't ever happen
            message.reply(
                '^[Sent](https://creeper.banano.cc/explorer/block/%s) ^(%s Banano to %s)' % (response[5], response[2], response[4]))
        elif (response[1] == 14):
            message.reply(
                '^[Sent](https://creeper.banano.cc/explorer/block/%s) ^(%s Banano to NanoCenter Project %s)' % (
                response[5], response[2], response[3]))
    elif subreddit_status == 'hostile':
        # it's a hostile place, no posts allowed. Will need to PM users
        if response[1] <= 8:
            message_recipient = str(message.author)
            subject = 'Your Banano tip did not go through'
            message_text = response[0] + comment_footer
            sql = "INSERT INTO messages (username, subject, message) VALUES (%s, %s, %s)"
            val = (message_recipient, subject, message_text)
            mycursor.execute(sql, val)
            mydb.commit()
        else:
            # if it was a new account, a PM was already sent to the recipient
            message_recipient = str(message.author)
            subject = 'Successful tip!'
            message_text = response[0] + comment_footer
            sql = "INSERT INTO messages (username, subject, message) VALUES (%s, %s, %s)"
            val = (message_recipient, subject, message_text)
            mycursor.execute(sql, val)
            mydb.commit()
            # status code 10 means the recipient has not requested silence, so send a message
            if response[1] == 10:
                message_recipient = response[3]
                subject = 'You just received a new Banano tip!'
                message_text = 'Somebody just tipped you ```%s Banano``` at your address %s. ' \
                               '[Transaction on Banano Creeper](https://creeper.banano.cc/explorer/block/%s)\n\n' \
                                'To turn off these notifications, reply with "silence yes"' % (
                                response[2], response[4], response[5]) + comment_footer

                sql = "INSERT INTO messages (username, subject, message) VALUES (%s, %s, %s)"
                val = (message_recipient, subject, message_text)
                mycursor.execute(sql, val)
                mydb.commit()

    elif subreddit_status == 'custom':
        # not sure what to do with this yet.
        pass


# These functions below handle the various messages the bot will receive
def handle_auto_receive(message):
    message_time = datetime.utcfromtimestamp(message.created_utc)  # time the reddit message was created
    username = str(message.author)
    add_history_record(
        username=str(message.author),
        action='auto_receive',
        comment_id=message.name,
        comment_or_message='message',
        reddit_time=message_time.strftime('%Y-%m-%d %H:%M:%S')
        )

    parsed_text = parse_text(str(message.body))

    if len(parsed_text) < 2:
        response = "I couldn't parse your command. I was expecting 'auto_receive <yes/no>'. " \
                   "Be sure to check your spacing."
        return response


    if parsed_text[1] == 'yes':
        sql = "UPDATE accounts SET auto_receive = TRUE WHERE username = %s "
        val = (username, )
        mycursor.execute(sql, val)
        response = "auto_receive set to 'yes'."
    elif parsed_text[1] == 'no':
        sql = "UPDATE accounts SET auto_receive = FALSE WHERE username = %s"
        val = (username, )
        mycursor.execute(sql, val)
        response = "auto_receive set to 'no'. Use 'receive' to manually receive unpocketed transactions."
    else:
        response = "I did not see 'no' or 'yes' after 'auto_receive'. If you did type that, check your spacing."
    mydb.commit()

    return response


def handle_message(message):
    # activate the account
    activate(message.author)
    response = 'not activated'
    message_body = str(message.body).lower()
    print("Body: **", message_body, "**")
    if message.body[0] == ' ':
        parsed_text = parse_text(str(message.body[1:]))
    else:
        parsed_text = parse_text(str(message.body))
    print("Parsed Text:", parsed_text)

    # standard things
    if (parsed_text[0].lower() == 'help') or (parsed_text[0].lower() == '!help'):
        print("Helping")
        subject = 'Banano Tipper - Help'
        response = handle_help(message)
    elif (parsed_text[0].lower() == 'balance') or (parsed_text[0].lower() == 'address'):
        print("balance")
        subject = 'Banano Tipper - Account Balance'
        response = handle_balance(message)
    elif parsed_text[0].lower() == 'minimum':
        print("Setting Minimum")
        subject = 'Banano Tipper - Tip Minimum'
        response = handle_minimum(message)
    elif parsed_text[0].lower() == 'percentage' or parsed_text[0].lower() == 'percent':
        print("Setting Percentage")
        subject = 'Banano Tipper - Returned Tip Percentage for Donation'
        response = handle_percentage(message)
    elif (parsed_text[0].lower() == 'create') or parsed_text[0].lower() == 'register':
        print("Creating")
        subject = 'Banano Tipper - Create'
        response = handle_create(message)
    elif (parsed_text[0].lower() == 'send') or (parsed_text[0].lower() == 'withdraw'):
        subject = 'Banano Tipper - Send'
        print("send via PM")
        response = handle_send(message)
    elif parsed_text[0].lower() == 'history':
        print("history")
        subject = 'Banano Tipper - History'
        response = handle_history(message)
    elif parsed_text[0].lower() == 'silence':
        print("silencing")
        subject = 'Banano Tipper - Silence'
        response = handle_silence(message)

    # nanocenter donation commands
    elif parsed_text[0].lower() == 'project' or parsed_text[0].lower() == 'projects':
        if ((str(message.author) == tipbot_owner) or (str(message.author).lower() == 'rockmsockmjesus')) and len(parsed_text) > 2:
            sql = "INSERT INTO projects (project, address) VALUES(%s, %s) ON DUPLICATE KEY UPDATE address=%s"
            val = (parsed_text[1], parsed_text[2], parsed_text[2])
            mycursor.execute(sql, val)
            mydb.commit()
        add_history_record(
            username=str(message.author),
            action='project',
            comment_text=str(message.body)[:255],
            comment_or_message='message',
            comment_id=message.name,
        )

        response = "Current NanoCenter Donation Projects: \n\n"
        subject = 'Nanocenter Projects'
        sql = "SELECT project, address FROM projects"
        mycursor.execute(sql)
        results = mycursor.fetchall()
        for result in results:
            response += "%s %s  \n" % (result[0], result[1])
    elif parsed_text[0].lower() == 'delete_project':
        if ((str(message.author) == tipbot_owner) or (str(message.author).lower() == 'rockmsockmjesus')) and len(parsed_text) > 1:
            sql = "DELETE FROM projects WHERE project=%s"
            val = (parsed_text[1], )
            mycursor.execute(sql, val)
            mydb.commit()
        response = "Current NanoCenter Donation Projects: \n\n"
        subject = 'Nanocenter Projects'
        sql = "SELECT project, address FROM projects"
        mycursor.execute(sql)
        results = mycursor.fetchall()
        for result in results:
            response += "%s %s  \n" % (result[0], result[1])


    # a few administrative tasks
    elif parsed_text[0].lower() == 'restart':
        if str(message.author) == tipbot_owner:
            add_history_record(
                username=str(message.author),
                action='restart',
                comment_text=str(message.body)[:255],
                comment_or_message='message',
                comment_id=message.name,
            )
            sys.exit()
    elif parsed_text[0].lower() == 'status':
        # benchmark a few SQL Selects
        if str(message.author) == tipbot_owner:
            previous_message_check = time.time()
            message_in_database(message)
            previous_message_check = previous_message_check-time.time()
            subject = 'Status'
            message = 'Check for Previous Messages: %s\n'%previous_message_check
    elif parsed_text[0].lower() == 'test_welcome_tipped':
        subject = 'Banano Tipper - Welcome By Tip'
        response = welcome_tipped % (0.01, 'ban_3jy9954gncxbhuieujc3pg5t1h36e7tyqfapw1y6zukn9y1g6dj5xr7r6pij', 'ban_3jy9954gncxbhuieujc3pg5t1h36e7tyqfapw1y6zukn9y1g6dj5xr7r6pij')
    elif parsed_text[0].lower() == 'test_welcome_create':
        subject = 'Banano Tipper - Create'
        response = welcome_create % ('ban_3jy9954gncxbhuieujc3pg5t1h36e7tyqfapw1y6zukn9y1g6dj5xr7r6pij', 'ban_3jy9954gncxbhuieujc3pg5t1h36e7tyqfapw1y6zukn9y1g6dj5xr7r6pij')

    else:
        add_history_record(
            username=str(message.author),
            comment_text=str(message.body)[:255],
            comment_or_message='message',
            comment_id=message.name,
        )
        return None
    message_recipient = str(message.author)
    message_text = response + comment_footer
    sql = "INSERT INTO messages (username, subject, message) VALUES (%s, %s, %s)"
    val = (message_recipient, subject, message_text)
    mycursor.execute(sql, val)
    mydb.commit()


def auto_receive():
    count = 0
    mycursor.execute("SELECT username, address, private_key FROM accounts")
    myresult = mycursor.fetchall()

    addresses = [str(result[1]) for result in myresult]
    private_keys = [str(result[2]) for result in myresult]
    mydb.commit()
    pendings = get_pendings(addresses, threshold=banoshi_to_raw(program_minimum))
    # get any pending blocks from our address
    for address, private_key in zip(addresses, private_keys):
        # allow 5 transactions to be received per cycle. If the bot gets transaction spammed, at least it won't be locked up receiving.
        if count >= 5:
            break
        try:
            if pendings['blocks'][address]:
                for sent_hash in pendings['blocks'][address]:
                    # address, private_key, dictionary where the blocks are the keys
                    open_or_receive_block(address, private_key, sent_hash)
                    count += 1
                    if count >= 2:
                        break

        except KeyError:
            pass
        except Exception as e:
            print(e)


def message_in_database(message):
    sql = "SELECT * FROM history WHERE comment_id = %s"
    val = (message.name, )
    mycursor.execute(sql, val)
    results = mycursor.fetchall()
    if len(results) > 0:
        print("previous message")
        print(message.name)
        for result in results:
            print('Result: ', results)
        return True
    return False


def check_inactive_transactions():
    t0 = time.time()
    print('running inactive script')
    mycursor.execute("SELECT username FROM accounts WHERE active IS NOT TRUE")
    myresults = mycursor.fetchall()
    inactivated_accounts = {item[0] for item in myresults}

    mycursor.execute("SELECT recipient_username FROM history WHERE action = 'send' AND hash IS NOT NULL AND `sql_time` <= SUBDATE( CURRENT_DATE, INTERVAL 31 DAY) AND (return_status = 'cleared' OR return_status = 'warned' OR return_status = 'return failed')")
    results = mycursor.fetchall()
    tipped_accounts = {item[0] for item in results}

    tipped_inactivated_accounts = inactivated_accounts.intersection(tipped_accounts)
    print('Accounts on warning: ', sorted(tipped_inactivated_accounts))
    returns = {}
    # scrolls through our inactive members and check if they have unclaimed tips
    for result in tipped_inactivated_accounts:
        # send warning messages on day 31
        sql = "SELECT * FROM history WHERE action = 'send' AND hash IS NOT NULL AND recipient_username = %s AND `sql_time` <= SUBDATE( CURRENT_DATE, INTERVAL 31 DAY) AND return_status = 'cleared'"
        val = (result, )
        mycursor.execute(sql, val)
        txns = mycursor.fetchall()
        if len(txns) >= 1:
            print('generating a message for %s' % result)

            message_recipient = result
            subject = 'Please Activate Your Banano Tipper Account'
            message_text = "Somebody tipped you at least 30 days ago, but your account hasn't been activated yet.\n\nPlease activate your account by replying any command to this bot. If you do not, any tips 35 days or older will be returned.\n\n***\n\n"
            message_text += help_text
            sql = "INSERT INTO messages (username, subject, message) VALUES (%s, %s, %s)"
            val = (message_recipient, subject, message_text)
            mycursor.execute(sql, val)
            mydb.commit()
            for txn in txns:
                sql = "UPDATE history SET return_status = 'warned' WHERE id = %s"
                val = (txn[0], )
                mycursor.execute(sql, val)
                mydb.commit()
            # print(message_recipient, subject, message_text)

        # return transactions over 35 days old
        sql = "SELECT * FROM history WHERE action = 'send' AND hash IS NOT NULL AND recipient_username = %s AND `sql_time` <= SUBDATE( CURRENT_DATE, INTERVAL 35 DAY) AND return_status = 'warned'"
        val = (result, )
        mycursor.execute(sql, val)
        txns = mycursor.fetchall()
        if len(txns) >= 1:
            sql = "SELECT address, private_key FROM accounts WHERE username = %s"
            val = (result,)
            mycursor.execute(sql, val)
            inactive_results = mycursor.fetchall()
            address = inactive_results[0][0]
            private_key = inactive_results[0][1]

            for txn in txns:
                # set the pre-update message to 'return failed'. This will be changed to 'returned' upon success
                sql = "UPDATE history SET return_status = 'return failed' WHERE id = %s"
                val = (txn[0], )
                mycursor.execute(sql, val)
                mydb.commit()

                # get the transaction information and find out to whom we are returning the tip
                sql = "SELECT address, percentage FROM accounts WHERE username = %s"
                val = (txn[1], )
                mycursor.execute(sql, val)
                returned_results = mycursor.fetchall()
                recipient_address = returned_results[0][0]
                percentage = returned_results[0][1]
                percentage = float(percentage) / 100
                # print('History record: ', txn[0], address, private_key, txn[9], recipient_address)

                # send it back
                donation_amount = int(txn[9])/10**30
                donation_amount = donation_amount * percentage
                donation_amount = banoshi_to_raw(donation_amount)

                return_amount = int(txn[9]) - donation_amount

                if (return_amount > 0) and (return_amount <= int(txn[9])):
                    hash = send(address, private_key, return_amount, recipient_address)['hash']
                    add_history_record(action='return', hash=hash, amount=return_amount,
                                       notes='Returned transaction from history record %s' % txn[0])
                if (donation_amount > 0) and (donation_amount <= int(txn[9])):
                    hash2 = send(address, private_key, donation_amount, 'ban_3jy9954gncxbhuieujc3pg5t1h36e7tyqfapw1y6zukn9y1g6dj5xr7r6pij')['hash']
                    add_history_record(action='donate', hash=hash2, amount=donation_amount,
                                       notes='Donation from returned tip %s' % txn[0])
                # print("Returning a transaction. ", hash)

                # update database if everything goes through
                sql = "UPDATE history SET return_status = 'returned' WHERE id = %s"
                val = (txn[0], )
                mycursor.execute(sql, val)
                mydb.commit()

                # add transactions to the messaging queue to build a single message
                message_recipient = txn[1]
                if message_recipient not in returns.keys():
                    returns[message_recipient] = {
                        'percent': round(percentage*100, 2),
                        'transactions': []
                    }
                returns[message_recipient]['transactions'].append([result, int(txn[9])/10**30, return_amount/10**30, donation_amount/10**30])


                """
                # send a message informing the tipper that the tip is being returned
                message_recipient = txn[1]
                subject = 'Returned your tip of %s to %s' % (int(txn[9])/10**30, result)
                message_text = "Your tip to %s for %s Banano was returned since the user never activated their account, and %s percent of this was donated to the TipBot development fund. You can change this percentage by messaging the TipBot 'percentage <amount>', where <amount> is a number between 0 and 100." % (result, int(txn[9])/10**30, round(percentage*100, 2))
                sql = "INSERT INTO messages (username, subject, message) VALUES (%s, %s, %s)"
                val = (message_recipient, subject, message_text)
                mycursor.execute(sql, val)
                mydb.commit()
                """

        # return transactions over 35 days old
        sql = "SELECT * FROM history WHERE action = 'send' AND hash IS NOT NULL AND recipient_username = %s AND `sql_time` <= SUBDATE( CURRENT_DATE, INTERVAL 35 DAY) AND return_status = 'return failed'"
        val = (result,)
        mycursor.execute(sql, val)
        txns = mycursor.fetchall()
        if len(txns) >= 1:
            sql = "SELECT address, private_key FROM accounts WHERE username = %s"
            val = (result,)
            mycursor.execute(sql, val)
            inactive_results = mycursor.fetchall()
            address = inactive_results[0][0]
            private_key = inactive_results[0][1]

            for txn in txns:
                # set the pre-update message to 'return failed'. This will be changed to 'returned' upon success
                sql = "UPDATE history SET return_status = 'return failed2' WHERE id = %s"
                val = (txn[0],)
                mycursor.execute(sql, val)
                mydb.commit()

                # get the transaction information and find out to whom we are returning the tip
                sql = "SELECT address, percentage FROM accounts WHERE username = %s"
                val = (txn[1],)
                mycursor.execute(sql, val)
                returned_results = mycursor.fetchall()
                recipient_address = returned_results[0][0]
                percentage = returned_results[0][1]
                percentage = float(percentage) / 100
                # print('History record: ', txn[0], address, private_key, txn[9], recipient_address)

                # send it back
                donation_amount = int(txn[9]) / 10 ** 29
                donation_amount = donation_amount * percentage
                donation_amount = banoshi_to_raw(donation_amount)

                return_amount = int(txn[9]) - donation_amount
                print('sending transaction')
                if (return_amount > 0) and (return_amount <= int(txn[9])):
                    hash = send(address, private_key, return_amount, recipient_address)['hash']
                    add_history_record(action='return', hash=hash, amount=return_amount,
                                       notes='Returned transaction from history record %s' % txn[0])
                print('sending donation')
                if (donation_amount > 0) and (donation_amount <= int(txn[9])):
                    hash2 = send(address, private_key, donation_amount,
                                 'ban_3jy9954gncxbhuieujc3pg5t1h36e7tyqfapw1y6zukn9y1g6dj5xr7r6pij')['hash']
                    add_history_record(action='donate', hash=hash2, amount=donation_amount,
                                       notes='Donation from returned tip %s' % txn[0])
                print('sent')
                # print("Returning a transaction. ", hash)

                # update database if everything goes through
                sql = "UPDATE history SET return_status = 'returned' WHERE id = %s"
                val = (txn[0],)
                mycursor.execute(sql, val)
                mydb.commit()

                # send a message informing the tipper that the tip is being returned
                message_recipient = txn[1]
                subject = 'Returned your tip of %s to %s' % (int(txn[9]) / 10 ** 29, result)
                message_text = "Your tip to %s for %s Banano was returned since the user never activated their account, and %s percent of this was donated to the TipBot development fund. You can change this percentage by messaging the TipBot 'percentage <amount>', where <amount> is a number between 0 and 100." % (
                result, int(txn[9]) / 10 ** 29, round(percentage * 100, 2))
                sql = "INSERT INTO messages (username, subject, message) VALUES (%s, %s, %s)"
                val = (message_recipient, subject, message_text)
                mycursor.execute(sql, val)
                mydb.commit()

        # send out our return messages
    for user in returns:
        message = 'The following tips have been returned and %s percent of each tip has been donated to the tipbot development fund:\n\n ' \
                                   '(Redditor, Total Tip Amount, Returned Amount, Donation Amount)\n\n '%returns[user]['percent']
        for transaction in returns[user]['transactions']:
            message += "%s | %s | %s | %s\n\n " % (transaction[0], transaction[1], transaction[2], transaction[3])
        sql = "INSERT INTO messages (username, subject, message) VALUES (%s, %s, %s)"
        val = (user, 'Returned Tips', message)
        mycursor.execute(sql, val)
        mydb.commit()

# main loop
t0 = time.time()
check_inactive_transactions()
for action_item in stream_comments_messages():
    # our 'stream_comments_messages()' generator will give us either a comment/reply, message, or username mention
    # (t1 = comment, t4 = message)
    # The bot handles these differently
    if action_item is None:
        # if we have nothing after the poll, pass
        pass
    elif message_in_database(action_item[1]):
        # if a message was already handled, pass
        pass
    elif action_item[0] == 'comment':
        if action_item[1].body[0] == ' ':
            # remove any leading spaces. for convenience
            parsed_text = parse_text(str(action_item[1].body[1:]))
        else:
            parsed_text = parse_text(str(action_item[1].body))
        try:
            if (parsed_text[0] in tip_commands) or (parsed_text[0] in donate_commands):
                print('*****************************************************')
                print(time.strftime('%Y-%m-%d %H:%M:%S'), 'Comment, beginning: ', action_item[1].author, ' - ', action_item[1].body[:20])

                if allowed_request(action_item[1].author, 30, 5) and not message_in_database(action_item[1]):
                    if tip_bot_on:
                        handle_comment(action_item[1])
                    else:
                        reddit.redditor(str(action_item[1].author)).message('Banano Tipper Currently Disabled', '[^(Banano Tipper is currently disabled)]')
                else:
                    print('Too many requests for %s' % action_item[1].author)
                print('*****************************************************')
            elif (parsed_text[-2] in tip_commands):
                print('*****************************************************')
                print(time.strftime('%Y-%m-%d %H:%M:%S'), 'Comment, end: ', action_item[1].author, ' - ',
                      action_item[1].body[:20])

                if allowed_request(action_item[1].author, 30, 5) and not message_in_database(action_item[1]):
                    if tip_bot_on:
                        if str(action_item[1].subreddit).lower() == 'cryptocurrency':
                            print('ignoring cryptocurrency post')
                        else:
                            handle_comment(action_item[1], parsed_text=parsed_text[-2:])
                    else:
                        reddit.redditor(str(action_item[1].author)).message('Banano Tipper Currently Disabled',
                                                                            '[^(Banano Tipper is currently disabled)]')
                else:
                    print('Too many requests for %s' % action_item[1].author)
                print('*****************************************************')
            elif (parsed_text[-3] in donate_commands):
                print('*****************************************************')
                print('Donate command."%s", %s' % (parsed_text[-3], donate_commands))
                print(time.strftime('%Y-%m-%d %H:%M:%S'), 'Comment, end: ', action_item[1].author, ' - ',
                      action_item[1].body[:20])

                if allowed_request(action_item[1].author, 30, 5) and not message_in_database(action_item[1]):
                    if tip_bot_on:
                        if str(action_item[1].subreddit).lower() == 'cryptocurrency':
                            print('ignoring cryptocurrency post')
                        else:
                            handle_comment(action_item[1], parsed_text=parsed_text[-3:])
                    else:
                        reddit.redditor(str(action_item[1].author)).message('Banano Tipper Currently Disabled',
                                                                            '[^(Banano Tipper is currently disabled)]')
                else:
                    print('Too many requests for %s' % action_item[1].author)
                print('*****************************************************')

        except IndexError:
            pass

    elif action_item[0] == 'message':
        if action_item[1].author == tip_bot_username:
            if (action_item[1].name[:3] == 't4_') and (action_item[1].body[:11] == 'send 0.001 ') and not message_in_database(action_item[1]):
                print('*****************************************************')
                print(time.strftime('%Y-%m-%d %H:%M:%S'), 'Faucet Tip: ', action_item[1].author, ' - ', action_item[1].body[:20])
                handle_message(action_item[1])
                print('*****************************************************')
            else:
                print('ignoring nano_tipper message')

        elif not allowed_request(action_item[1].author, 30, 5):
            print('Too many requests for %s' % action_item[1].author)
        else:
            if tip_bot_on:
                #parse out the text
                if action_item[1].name[:3] == 't4_' and not message_in_database(action_item[1]):

                    print('*****************************************************')
                    print(time.strftime('%Y-%m-%d %H:%M:%S'), 'Message: ', action_item[1].author, ' - ', action_item[1].body[:20])
                    handle_message(action_item[1])
                    print('*****************************************************')
            else:
                action_item[1].reply('[^(Banano Tipper is currently disabled)]')

    elif action_item[0] == 'username mention':
        # print('Printing Username mention: ', parsed_text[0])
        if action_item[1].body[0] == ' ':
            # remove any leading spaces. for convenience
            parsed_text = parse_text(str(action_item[1].body[1:]))
        else:
            parsed_text = parse_text(str(action_item[1].body))


        try:
            if (parsed_text[0] == '/u/%s'%tip_bot_username) or (parsed_text[0] == 'u/%s' % tip_bot_username):
                print('*****************************************************')
                print(time.strftime('%Y-%m-%d %H:%M:%S'), 'Username Mention: ', action_item[1].author, ' - ', action_item[1].body[:20])
                if allowed_request(action_item[1].author, 30, 5) and not message_in_database(action_item[1]):
                    if tip_bot_on:
                        handle_comment(action_item[1])
                        pass
                    else:
                        reddit.redditor(str(action_item[1].author)).message('Banano Tipper Currently Disabled',
                                                                            '[^(Banano Tipper is currently disabled)]')
                else:
                    print('Too many requests for %s' % action_item[1].author)
                print('*****************************************************')
            elif (parsed_text[-2] == '/u/%s'%tip_bot_username) or (parsed_text[-2] == 'u/%s' % tip_bot_username):
                print('*****************************************************')
                print(time.strftime('%Y-%m-%d %H:%M:%S'), 'Username Mention: ', action_item[1].author, ' - ',
                      action_item[1].body[:20])
                if allowed_request(action_item[1].author, 30, 5) and not message_in_database(action_item[1]):
                    if tip_bot_on:
                        handle_comment(action_item[1], parsed_text=parsed_text[-2:])
                    else:
                        reddit.redditor(str(action_item[1].author)).message('Banano Tipper Currently Disabled',
                                                                            '[^(Banano Tipper is currently disabled)]')
                else:
                    print('Too many requests for %s' % action_item[1].author)
                print('*****************************************************')
        except IndexError:
            pass

    # run the inactive script at the end of the loop; every 12 hours
    if time.time()-t0 > 43200:
        t0 = time.time()
        check_inactive_transactions()
