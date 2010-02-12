#!/usr/bin/env python
from distutils.core import setup

setup(
    name='GmailSMSNotifier',
    version='0.1',
    description='Gmail SMS notifier is used to watch your inbox and submit \
Google Calendar events',
    author='Alexandru Plugaru',
    author_email='alexandru.plugaru@gmail.com',
    url='http://github.com/humanfromearth/gmail-sms-notifier',
    license='GPLv2',
    packages=['GmailSMSNotifier'],
    requires=['gdata'],
)
