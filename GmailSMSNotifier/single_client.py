#!/usr/bin/env python
__doc__ = """ Console client using both Programmatic and OAuth authentification
methods to Google services.
"""
import getopt
import os
import pickle
import re
import sys
import time
from threading import Thread

from libs.gcal import Calendar # Access Google Calendar
from libs.gmail import Gmail # Access Gmail via RSS Feed

# Constants
DEBUG = True
DELETE_EVENT_AFTER = 70 # Seconds
CHECK_INTERVAL = 60 # Seconds
#We will store here message ids that have been sent notifications to
ENTRY_IDS_FILE =  os.path.join(os.getcwd(), 'message_ids.pickle')

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
		self.emails = []
		self._email_ids() # loading pickled message ids
	def run(self):
		gmail = Gmail('Programmatic', labels=self.labels)
		gmail.login(email=self.email, password=self.password)
		entries = gmail.entries()
		if entries['error'] == 'Unauthorized':
			print "Login failed! Make sure your email and password is correct"
			sys.exit(2)

		calendar = Calendar('Programmatic')
		calendar.login(email=self.email, password=self.password)

		for label in entries['entries']:
			for entry in entries['entries'][label]:
				if entry['id'] not in self.emails:
					label_text = "Inbox" if label == '^inbox' else label
					event = calendar.create(title="("+entry['author_name']+") "
							+ entry['title'], where = label_text)
					self.emails.append(entry['id'])
					self._email_ids() # Write this event to pickled file
					time.sleep(180)
					calendar.delete(event)
	def _email_ids(self):
		""" Sync email ids. This pickled file will know what mails have been
		noted in gcalendar

		"""
		if os.path.exists(ENTRY_IDS_FILE):
			try:
				if len(self.emails):
					pickle.dump(self.emails, open(ENTRY_IDS_FILE, 'wb'))
				self.emails = pickle.load(open(ENTRY_IDS_FILE, 'rb'))
			except:
				print 'Error reading pickled file'
				sys.exit(2)
		else:
			try:
				pickle.dump(self.emails, open(ENTRY_IDS_FILE, 'wb'))
			except:
				print 'Error creating pickled file'
def usage():
	print """Usage: %s [-e|--email=GMAIL_EMAIL] [-p|--password=GMAIL_PASSWORD] [-l|--labels=LABELS]'
Example:
    %s --email=account@gmail.com --password=my_password --labels=Important,Work,Family
    If no --labels are set it will watch the inbox
""" % (sys.argv[0], sys.argv[0])
	sys.exit(2)

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "he:p:l:",
								   ["help", "email=", 'password=', 'labels='])
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
	elif (email and not password) or (password and not email):
		usage()
	else: # Password and email set - start daemon
		while True:
			try:
				daemon = Daemon(email = email, password = password,
								labels = labels)
				daemon.start()
				time.sleep(500)
			except KeyboardInterrupt:
				sys.exit(2)
if __name__ == "__main__":
	main()
