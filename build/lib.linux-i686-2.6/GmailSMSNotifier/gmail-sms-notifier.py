#!/usr/bin/env python
#	GmailSMSNotifier console client
#	Copyright (C) 2010  Alexandru Plugaru (alexandru.plugaru@gmail.com)
#
#	This program is free software; you can redistribute it and/or
#	modify it under the terms of the GNU General Public License
#	as published by the Free Software Foundation; either version 2
#	of the License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program; if not, write to the Free Software
#	Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import sys
import os
import getopt

import time
import re
import pickle

from threading import Thread, Timer

from libs.gcal import Calendar # Access Google Calendar
from libs.gmail import Gmail # Access Gmail via RSS Feed

# Constants
DEBUG = True
DELETE_EVENT_AFTER = 70 # Seconds
CHECK_INTERVAL = 60 # Seconds
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
ENTRY_IDS_FILE =  ROOT_PATH + '/tmp/message_ids.pickle'
class Daemon(Thread):
	"""
	Check if there are new emails on your Gmail account.
	If there are then add an event Google Calendar.
	Wait a minute then delete the event to leave calendar account clean.
	"""
	def __init__(self, email = None, password = None, labels = None):
		""" Setting the vars """
		Thread.__init__(self)

		self.email = email
		self.password = password
		self.labels = labels
		self.timer = None
	def run(self):
		gmail = Gmail(self.email, self.password, self.labels)
		entries = gmail.entries()
		if entries['error'] == 'Unauthorized':
			print "Login failed! Make sure your email and password is correct"
			sys.exit(2)

		calendar = Calendar(self.email, self.password)
		for label in entries['entries']:
			for entry in entries['entries'][label]:
				label_text = "Inbox" if label == '^inbox' else label
				event = calendar.create(title="("+entry['author_name']+") " + entry['title'], where = label_text)
				time.sleep(180)
				calendar.delete(event)
	def _read_ids(self):
		print ENTRY_IDS_FILE
	def _write_id(self, id = ""):
		print ENTRY_IDS_FILE
def usage():
	print """Usage: %s [-e|--email=GMAIL_EMAIL] [-p|--password=GMAIL_PASSWORD] [-l|--labels=LABELS]"
Example:
    %s --email=account@gmail.com --password=my_password --labels=Important,Work,Family
    If no --labels are set it will watch the inbox
""" % (sys.argv[0], sys.argv[0])
	sys.exit(2)
def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "he:p:l:", ["help", "email=", 'password=', 'labels='])
	except getopt.GetoptError, err:
		# print help information and exit:
		usage()
		print str(err)
	email = None
	password = None
	labels = None

	for o, a in opts:
		if o in ("-e", "--email"):
			email = a
		elif o in ("-p", "--password"):
			password = a
		elif o in ("-l", "--labels"):
			labels = a.split(',')
		elif o in ("-h", "--help"):
			usage()
		else:
			assert False, "unhandled option"
	if not email and not password and not labels: # No arguments == GUI
		usage()
	elif (email and not password) or (password and not email): #Password supplied but no email
		usage()
	else: # Password and email set - start daemon
		while True:
			try:
				daemon = Daemon(email = email, password = password, labels = labels)
				daemon.start()
				time.sleep(500)
			except KeyboardInterrupt:
				sys.exit(2)
if __name__ == "__main__":
	main()