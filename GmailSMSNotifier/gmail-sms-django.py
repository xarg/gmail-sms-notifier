#!/usr/bin/env python
#	GmailSMSNotifier Daemon with connection to Django - this is just an example
#
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

from threading import Thread

from libs.gcal import Calendar # Access Google Calendar
from libs.gmail import Gmail # Access Gmail via RSS Feed

# Django Connection
# !!! IMPORTANT !!!
DJANGO_PATH = '/home/sasha/django/gmailsms'

sys.path.append(DJANGO_PATH)
from django.core.management import setup_environ
import settings
setup_environ(settings)


from django.contrib.auth.models import User

# Profile modules and labels and so on..
from accounts.models import UserProfile, UserLabel, UserEmail

from django.core.mail import send_mail, mail_admins

# Constants
DEBUG = True
DELETE_EVENT_AFTER = 180 # Seconds
CHECK_INTERVAL = 60 # Seconds
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
# Check five times if an OAuth is ok, if not remove authorizations from DB and notify user via e-mail
FAIL_COUNT = 5
UNAUTHORIZED_ACCESS = {}

class Daemon(Thread):
	"""
	Check if there are new emails on your Gmail account.
	If there are then add an event Google Calendar.
	Wait a minute then delete the event to leave calendar account clean.
	"""
	def __init__(self, user):
		Thread.__init__(self)
		self.user = user
		self.unauthorized = False
	def run(self):
		gmail = Gmail('OAuth', labels=self.user['labels'])
		gmail.login(
			oauth_consumer_key=settings.OAUTH_CONSUMER_KEY,
			oauth_consumer_secret=settings.OAUTH_CONSUMER_SECRET,
			oauth_token_access=self.user['oauth_token_access'],
			oauth_token_secret=self.user['oauth_token_secret']
		)
		entries = gmail.entries()
		if entries['error'] == 'Unauthorized':
			self.unauthorized = True
			if UNAUTHORIZED_ACCESS[self.user['id']] is None:
				UNAUTHORIZED_ACCESS[self.user['id']] = 1
			elif UNAUTHORIZED_ACCESS[self.user['id']] == FAIL_COUNT:
				try:
					user_profile = UserProfile.objects.get(user_id=self.user['id'])
					user_profile.oauth_token_access = ''
					user_profile.oauth_token_secret = ''
					user_profile.save()
					send_mail(
						'Invalid authorization',
						render_to_string('emails/invalid_authorization.txt', { 'SITE': settings.SITE }),
						settings.DEFAULT_FROM_EMAIL,
						[self.user['email'], ]
					)
				except:
					pass
			else:
				UNAUTHORIZED_ACCESS[self.user['id']] +=1
		else:
			try:
				del(UNAUTHORIZED_ACCESS[self.user['id']])
			except KeyError:
				pass
		if not self.unauthorized:
			calendar = Calendar('OAuth')
			calendar.login(
				oauth_consumer_key=settings.OAUTH_CONSUMER_KEY,
				oauth_consumer_secret=settings.OAUTH_CONSUMER_SECRET,
				oauth_token_access=self.user['oauth_token_access'],
				oauth_token_secret=self.user['oauth_token_secret']
			)
			events = []
			for label in entries['entries']:
				for entry in entries['entries'][label]:
					label_text = "Inbox" if label == '^inbox' else label
					print entry	
					try:
						UserEmail.objects.filter(user=self.user['id']).filter(email_id=entry['id']).get() # This email has been verified
					except UserEmail.DoesNotExist:						
						user_email = UserEmail(user_id=self.user['id'], email_id=entry['id'])
						events.append(calendar.create(title="("+entry['author_name']+") " + entry['title'], where = label_text))
						user_email.save() # Event created save log							
			time.sleep(DELETE_EVENT_AFTER)
			for event in events: # Clean calendar from added notifications
				calendar.delete(event)
def main():
	while True:
		try:
			user_profiles = UserProfile.objects.filter(stop=0).exclude(oauth_token_access='').all()
			users = []
			for user_profile in user_profiles:
				try:
					user = User.objects.get(pk=user_profile.pk)
					user_labels = UserLabel.objects.filter(user=user_profile.pk).all()
					labels = []
					for label in user_labels:
						labels.append(label.name)
					if len(labels) == 0: # No labels, no notifications
						break
					users.append({
						'id': user.pk,
						'email':user.email,
						'labels': labels,
						'oauth_token_access': user_profile.oauth_token_access,
						'oauth_token_secret': user_profile.oauth_token_secret,
					})
				except User.DoesNotExist:
					pass			
			for user in users:
				daemon = Daemon(user)
				daemon.start()
			time.sleep(CHECK_INTERVAL)
		except KeyboardInterrupt:
			sys.exit(2)
if __name__ == "__main__":
	main()