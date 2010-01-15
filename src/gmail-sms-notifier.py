#!/usr/bin/env python
#
# This includes a threading daemon that checks gmail new messages feed
#

import sys
import time
import re
import pickle

from threading import Thread

from libs.gcal import Calendar # Access Google Calendar
from libs.gmail import Gmail # Access Gmail via RSS Feed

# Constants
DEBUG = True
DELETE_EVENT_AFTER = 70 # Seconds

class Daemon(threading.Thread):
    """
    Check if there are new emails on your Gmail account.
    If there are then add an event Google Calendar.
    Wait a minute then delete the event to leave calendar account clean.
    """
    def run(self):
        self.sent = {}
        try:
            file_pi = open(sentFile, 'r')
            sentData = pickle.load(file_pi)
            file_pi.close()
            if sentData:
                self.sent = sentData
        except:
            pass
        self.email = ''
        self.password = ''
        self.sendMessages()

    def send_messages(self):
        if not self.email and not self.password:
            file_pi = open(authFile, 'r')
            authData = pickle.load(file_pi)
            file_pi.close()
            self.email = authData['email']
            self.password = authData['password']

            gmail = Gmail(self.email, self.password)
            entries = gmail.entries()
            if entries['error'] == 'Unauthorized':
                print "Login Failed!"
        unread = gmail.getInbox()
        for message_id, subject in unread.iteritems():
            if not self.sent.has_key(message_id):
                account = self.email.split('@')[0]
                self.sent[message_id] = subject

                file_pi = open(sentFile, 'w')
                pickle.dump(self.sent, file_pi)
                file_pi.close()

                calendar = Calendar(account, self.password)
                event = calendar._InsertEvent(title = subject)
                try:
                    calendar._AddReminder(event)
                except :
                    time.sleep(2)
                    calendar._AddReminder(event)
                time.sleep(70)
                calendar._DeleteEvent(event)
        time.sleep(10)
        self.sendMessages()
if __name__ == "__main__":
    gmail = Gmail()