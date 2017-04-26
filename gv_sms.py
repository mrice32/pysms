#!/usr/bin/env python

#
# SMS test via Google Voice
#
# John Nagle
#   nagle@animats.com
#
import BeautifulSoup
from datetime import datetime
from datetime import timedelta
from googlevoice import Voice
from googlevoice.util import input
import sched
import sys
import time
import re



def extractsms(htmlsms):
    """
    extractsms  --  extract SMS messages from BeautifulSoup tree of Google Voice SMS HTML.

    Output is a list of dictionaries, one per message.
    """
    msgitems = []  # accum message items here
    #	Extract all conversations by searching for a DIV with an ID at top level.
    tree = BeautifulSoup.BeautifulSoup(htmlsms)  # parse HTML into tree
    conversations = tree.findAll("div", attrs={"id": True}, recursive=False)
    for conversation in conversations:
        #	For each conversation, extract each row, which is one SMS message.
        rows = conversation.findAll(attrs={"class": "gc-message-sms-row"})
        for row in rows:  # for all rows
            #	For each row, which is one message, extract all the fields.
            msgitem = {"id": conversation["id"]}  # tag this message with conversation ID
            spans = row.findAll("span", attrs={"class": True}, recursive=False)
            for span in spans:  # for all spans in row
                cl = span["class"].replace('gc-message-sms-', '')
                msgitem[cl] = (" ".join(span.findAll(text=True))).strip()  # put text in dict
            msgitems.append(msgitem)  # add msg dictionary to list
    return msgitems


def convertToInt(string):
    num_str = re.sub("[^0-9]", "", string)
    if num_str:
        return int(num_str)
    return 0

def sendMessage(voice, message_text, number):
    voice.send_sms(number, message_text)

def poll(scheduler, voice):
    for message in voice.sms().messages:
        if message.isRead:
            message.delete()
            print 'Deleted a message'

    voice.sms()
    for msg in extractsms(voice.sms.html):
        print str(msg)
        message_content = msg['text']
        sending_number = msg['from']
        if sending_number.startswith('Me'):
            continue
        mini_messages = message_content.split('.')
        date = mini_messages[0].split(",")

        month = 0
        week = 0
        day = 0
        hour = 0
        minute = 0
        second = 0

        for string in date:
            if "command" in string:
                pass
            elif "mo" in string:
                month = convertToInt(string)
            elif "w" in string:
                week = convertToInt(string)
            elif "d" in string and "second" not in string:
                day = convertToInt(string)
            elif "h" in string:
                hour = convertToInt(string)
            elif "m" in string:
                minute = convertToInt(string)
            elif "s" in string:
                second = convertToInt(string)

        now = datetime.now()

        day = month * 30 + day
        new_time = now + timedelta(weeks=week, days=day, hours=hour, minutes=minute, seconds=second)

        scheduler.enterabs(time.mktime(new_time.timetuple()), 1, sendMessage, (voice, '.'.join(mini_messages[1:]), sending_number))

        outgoing_message = 'Roger, roger.'

        sendMessage(voice, outgoing_message, sending_number)

    scheduler.enter(10, 2, poll, (scheduler, voice))


def main():
    voice = Voice()
    voice.login()

    # Write stdout to file after prompts
    orig_stdout = sys.stdout
    f = open('pygv_log.txt', 'a')
    sys.stdout = f
    scheduler = sched.scheduler(time.time, time.sleep)

    try:
        poll(scheduler, voice)
        scheduler.run()

    except:
        voice.logout()
        sys.stdout = orig_stdout
        f.close()
        raise

    voice.logout()
    sys.stdout = orig_stdout
    f.close()


if __name__ == "__main__":
    main()