#!/usr/bin/env python
import urllib2
from xml.etree.ElementTree import fromstring

class Gmail:
	""" Used to watch new email entries in the inbox or some labels """
	def __init__(self, email = None, password = None, labels = None):
		"""
		Gets all the new messages from Gmail labels
		If no labels are given return inbox
		"""
		self.data = {
			'error': None,
			'entries': {},
		}
		self.labels = labels
		ah = urllib2.HTTPBasicAuthHandler()
		ah.add_password('New mail feed', 'https://mail.google.com', email, password)
		op = urllib2.build_opener(ah)
		urllib2.install_opener(op)
	def entries(self):
		try:
			if self.labels:
				for label in self.labels:
					entries = self._parse_entries(label)
					self.data['entries'][label] = entries
			else:
				inbox_entries = self._parse_entries()
				self.data['entries'] = {"^inbox": inbox_entries}
		except urllib2.HTTPError:
			self.data['error'] = 'Unauthorized'
		return self.data
	def _parse_entries(self, label = None):
		"""
		Returns a entry
		"""
		if label: # get label
			res = urllib2.urlopen('https://mail.google.com/mail/feed/atom/' + label)
		else: # get inbox
			res = urllib2.urlopen('https://mail.google.com/mail/feed/atom')
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
				elif tag == 'summary':
					row['summary']  = e.text
				elif tag == 'modified':
					row['modified']  = e.text
				elif tag == 'author':
					author = e.getchildren()
					row['author_name'] = author[0].text
					row['author_email'] = author[1].text
			if len(row):
				entries_list.append(row)
		return entries_list
if __name__ == '__main__':
	gmail = Gmail('account@gmail.com', 'password', ('Photo', ))
	entries = gmail.entries() # Entries