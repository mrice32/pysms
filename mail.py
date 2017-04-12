#!/usr/bin/env python

import sys
import imaplib
import getpass
import email
import datetime
import smtplib
from datetime import datetime
from datetime import timedelta
import re
from subprocess import Popen, PIPE


def convertToInt(string):
    return int(re.sub("[^0-9]", "", string))


def sendEmail(message, username, password, phone_number):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, password)
    server.sendmail(username + "@gmail.com", phone_number + "@txt.att.net", message)



username = raw_input('Please enter your gmail username (*@gmail.com):')
print 'Please enter your gmail password'
password = getpass.getpass()
phone_number = raw_input('Please enter your ATT cell phone number')

M = imaplib.IMAP4_SSL('imap.gmail.com')


M.login(username + '@gmail.com', password) 

print "pre while"

times_and_messages = []


while True:

    indices = []
    index = 0
    for time_and_message in times_and_messages:
        if time_and_message[0] < datetime.now():
            sendEmail(time_and_message[1], username, password, phone_number)
            indices.append(index)
        index = index + 1

    for i in sorted(indices, reverse = True):
        del times_and_messages[i]

    print "during while"
    try:
        rv, data = M.select("INBOX")
        if rv != 'OK':
            print "select failed"
            continue
    except:
        print "exception in select"
        continue


    try:
        rv, texts = M.search(None, '(FROM "' + phone_number + '@txt.att.net")')

        print texts
        if rv != 'OK':
            print "Nothing found"
            continue

        for num in texts[0].split():
            rv, message = M.fetch(num, '(RFC822)')
            if rv != 'OK':
                print "Problem getting message"
                continue
            msg_data = email.message_from_string(message[0][1])
            if email.utils.parseaddr(msg_data["From"])[1] != (phone_number + "@txt.att.net"):
                print "The address isn't correct"
                print email.utils.parseaddr(msg_data["From"])
                continue

            mini_messages = msg_data.get_payload().split(".")

            date = mini_messages[0].split(",")
            
            month = 0
            week = 0
            day = 0
            hour = 0
            minute = 0
            second = 0

            for string in date:
                if "command" in string:
                    a=5
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
            new_time = now + timedelta(weeks = week, days = day, hours = hour, minutes = minute, seconds = second)

            times_and_messages.append((new_time, mini_messages[1]))
            
            print msg_data.get_payload()
            
            my_message = "\nRoger roger."

            sendEmail(my_message, username, password, phone_number)

            M.store(num, '+FLAGS', '\\Deleted')
            
            

        M.expunge()
                   
    except:
         print "message issues"
         continue
