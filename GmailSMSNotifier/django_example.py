#!/usr/bin/env python
# GmailSMSNotifier Daemon with connection to Django - this is just an example
# 
# Copyright (C) 2010  Alexandru Plugaru (alexandru.plugaru@gmail.com)
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import sys
import os
import getopt

import time
import re
import pdb
from pprint import pprint

from libs.ThreadPool import ThreadPool
from threading import current_thread
#from Queue import Queue

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

# Constants
DEBUG = True
THREADS_COUNT = 10 # Number of threads
DELETE_EVENT_AFTER = 180 # Seconds
CHECK_INTERVAL = 10 # Seconds
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
# Check five times if an OAuth is ok, if not remove authorizations from DB and notify user via e-mail
FAIL_COUNT = 2
UNAUTHORIZED_ACCESS = {}


def run(user):
	""" Make the necessary checks """
	unauthorized = False
	gmail = Gmail('OAuth', labels = user['labels'])
	gmail.login(
		oauth_consumer_key=settings.OAUTH_CONSUMER_KEY,
		oauth_consumer_secret=settings.OAUTH_CONSUMER_SECRET,
		oauth_token_access=user['oauth_token_access'],
		oauth_token_secret=user['oauth_token_secret']
	)
	entries = gmail.entries()
	if entries['error'] == 'Unauthorized':
		unauthorized = True
		if user['id'] not in UNAUTHORIZED_ACCESS:
			UNAUTHORIZED_ACCESS[user['id']] = 1
		elif UNAUTHORIZED_ACCESS[user['id']] >= FAIL_COUNT:
			user_profile = UserProfile.objects.get(user=user['id'])
			#user_profile.stop = '1'
			user_profile.oauth_token_access = ''
			user_profile.oauth_token_secret = ''
			user_profile.save()
			send_mail(
				'OAuth token no longer valid',
				render_to_string('emails/token_invalid.txt', { 'SITE': settings.SITE }),
				settings.DEFAULT_FROM_EMAIL,
				[user['email'], ]
			)
		else:
			UNAUTHORIZED_ACCESS[user['id']] +=1
	else:
		if user['id'] in UNAUTHORIZED_ACCESS:
			del(UNAUTHORIZED_ACCESS[user['id']])
	if not unauthorized:
		calendar = Calendar('OAuth')
		calendar.login(
			oauth_consumer_key=settings.OAUTH_CONSUMER_KEY,
			oauth_consumer_secret=settings.OAUTH_CONSUMER_SECRET,
			oauth_token_access=user['oauth_token_access'],
			oauth_token_secret=user['oauth_token_secret']
		)
		events = []
		for label in entries['entries']:
			for entry in entries['entries'][label]:
				label_text = "Inbox" if label == '^inbox' else label
				try:
					UserEmail.objects.filter(user=user['id']).filter(email_id=entry['id']).get() # This email has been verified
				except UserEmail.DoesNotExist:
					user_email = UserEmail(user_id=user['id'], email_id=entry['id'])
					events.append(calendar.create(title="("+entry['author_name']+") " + entry['title'], where = label_text))
					user_email.save() # Event created save log							
		time.sleep(DELETE_EVENT_AFTER)
		for event in events: # Clean calendar from added notifications
			calendar.delete(event)
	return current_thread()
def result(res):
	print res
def main():
	pool = ThreadPool()
	while True:
		try:
			user_profiles = UserProfile.objects.select_related().filter(stop=0).exclude(oauth_token_access='').all()
			users = []
			for user_profile in user_profiles:
				user_labels = UserLabel.objects.filter(user=user_profile.pk).all()
				labels = []
				for label in user_labels:
					labels.append(label.name)
				if len(labels) == 0: # No labels, no notifications
					break
				users.append({
					'id': user_profile.user_id,
					'email': user_profile.user.email,
					'labels': labels,
					'oauth_token_access': user_profile.oauth_token_access,
					'oauth_token_secret': user_profile.oauth_token_secret,
				})
			for user in users:
				pool.add_job(run, [user, ], result)
			time.sleep(CHECK_INTERVAL)
		except KeyboardInterrupt:
			pool.shutdown()
if __name__ == "__main__":
	main()