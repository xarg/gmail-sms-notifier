#!/usr/bin/env python
#	GmailSMSNotifier Gmail library - allows OAuth and Programmatic login
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
import urllib2
import oauth
from xml.etree.ElementTree import fromstring

import time

class Gmail:
	""" Used to watch new email entries in the inbox or some labels """
	def __init__(self, type="Programmatic", labels = None):
		"""
		Gets all the new messages from Gmail labels
		If no labels are given return inbox
		"""
		self.data = {
			'error': None,
			'entries': {},
		}
		self.labels = labels
		self.type = type
		self.request = urllib2.Request('https://mail.google.com/mail/feed/atom')
	def login(self, **args):
		if self.type == 'Programmatic':
			ah = urllib2.HTTPBasicAuthHandler()
			ah.add_password('New mail feed', 'https://mail.google.com', args['email'], args['password'])
			op = urllib2.build_opener(ah)
			urllib2.install_opener(op)
		elif self.type == 'OAuth':
			self.oauth_token_access = args['oauth_token_access']
			self.oauth_token_secret = args['oauth_token_secret']
			self.oauth_consumer_key = args['oauth_consumer_key']
			self.oauth_consumer_secret = args['oauth_consumer_secret']
	def entries(self):
		try:
			if self.labels:
				for label in self.labels:
					entries = self._parse_entries(label)
					self.data['entries'][label] = entries
			else:
				inbox_entries = self._parse_entries()
				self.data['entries'] = {"^inbox": inbox_entries}
		except urllib2.HTTPError, e:
			self.data['error'] = 'Unauthorized'
		return self.data
	def _parse_entries(self, label = None):
		"""
		Returns a entry
		"""
		if label: # get label
			self.request = urllib2.Request(self.request.get_full_url() + '/' + label)
			if self.type == 'OAuth': self._set_header(label)
		else:
			if self.type == 'OAuth': self._set_header()
		#opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1))
		opener = urllib2.build_opener(urllib2.HTTPHandler())
		res = opener.open(self.request)

		lines = ''.join(res.readlines())
		e = fromstring(lines)
		entries =  e.findall('{http://purl.org/atom/ns#}entry')
		entries_list = []
		for entry in entries:
			row = {}
			for e in entry:
				tag = str(e.tag).split('{http://purl.org/atom/ns#}')[1]
				if tag == 'id':
					row['id'] = e.text.split(':')[2]
				elif tag == 'title':
					row['title']  = e.text
				elif tag == 'modified':
					row['modified']  = e.text
				elif tag == 'author':
					author = e.getchildren()
					row['author_name'] = author[0].text
			if len(row):
				entries_list.append(row)
		return entries_list
	def _set_header(self, label = ''):
		if label != '': label = '/' + label
		token = oauth.OAuthToken(self.oauth_token_access, self.oauth_token_secret)
		consumer = oauth.OAuthConsumer(self.oauth_consumer_key, self.oauth_consumer_secret)

		oauth_request = oauth.OAuthRequest.from_consumer_and_token(
			consumer,
			token=token,
			http_method='GET',
			http_url='https://mail.google.com/mail/feed/atom' + label ,
		)
		oauth_request.sign_request(
			oauth.OAuthSignatureMethod_HMAC_SHA1(),
			consumer,
			token
		)
		authorization_header = oauth_request.to_header()
		self.request.add_header('Authorization', authorization_header['Authorization'])
		self.request.add_header('User-Agent', 'Google_SMS_Notifier_1_0 GData-Python/1.2.2')
		self.request.add_header('Content-Type', 'application/atom+xml')
if __name__ == '__main__':
	gmail = Gmail('OAuth', labels = ('Work', ))
	gmail.login(
		oauth_consumer_key='',
		oauth_consumer_secret='',
		oauth_token_access='',
		oauth_token_secret='',
	)
	#gmail = Gmail('Programmatic', labels = ('Important', ))
	#gmail.login(email='account@gmail.com', password='password')
	entries = gmail.entries() # Entries
	print entries