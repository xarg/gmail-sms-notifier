#!/usr/bin/env python
__doc__ = """ This is the manager code. It distributes work accross multiple
seed clients. Initialy it reads all user-data from the DB. Then using django
signals updates it's list.

"""

import beanstalkc
import json
import os
import sys
from threading import Thread, Lock

#Django
from django.core.management import setup_environ
from django.core.mail import mail_admins

DJANGO_PATH = '/home/sasha/django/gmailsms'
sys.path.append(DJANGO_PATH)
import settings
setup_environ(settings)

from settings import BEANSTALKD_SERVER, BEANSTALKD_TUBES
from accounts.models import UserProfile, UserProfileLabel, UserProfileEmail

from libs.gcal import Calendar # Access Google Calendar
from libs.gmail import Gmail # Access Gmail via RSS Feed

try:
    beanstalk_connection = beanstalkc.Connection(**BEANSTALKD_SERVER)
except Exception, e:
    mail_admins("Gmail-SMS Error (manager)", "Beankstalk connection\n%s" % e)
    sys.exit(2)

users = [] # Users list
users_lock = Lock()

seeds = dict() # Stores which user on which seed is located
for tube in BEANSTALKD_TUBES:
    seeds.setdefault(tube, [])

users_no_seed = []

class DjangoHandler(Thread):
    """ Handles work from Django
    If a new user is created then assign it to a free seed
    If some user data is modified notify the seed of it.

    """
    def __init__(self):
        Thread.__init__(self)
        self.beanstalk_connection = beanstalk_connection
        self.beanstalk_connection.watch('default')

    def run(self):
        notification = json.loads(self.beanstalk_connection.reserve().body)

class SeedHandler(Thread):
    """ Processing data received from seeds. Confirmations, Notifications stats

    """
    def __init__(self):
        Thread.__init__(self)
        self.beanstalk_connection = beanstalk_connection
        self.beanstalk_connection.watch('manager')
    def run(self):
        while True:
            notification = json.loads(self.beanstalk_connection.reserve().body)

class MainThread(Thread):
    """ Getting userdata (labels, seed location, etc.) from django
    Allocating users to seeds using beanstalk

    """
    def __init__(self):
        Thread.__init__(self)
        self.beanstalk_connection = beanstalk_connection
        self.beanstalk_connection.watch('manager')

    def run(self):
        #Reading all users from the DB
        user_profiles = UserProfile.objects.select_related().filter(stop=0).\
                        exclude(oauth_token_access='').all()
        for user_profile in user_profiles:
            user_labels = user_profile.userprofilelabel_set.values()
            labels = [label['name'] for label in user_labels
                      if label.get('name', None)]
            if not labels: # No labels == no notifications
                break
            user_data = {
                'id': user_profile.user_id,
                'email': user_profile.user.email,
                'labels': labels,
                'oauth_token_access': user_profile.oauth_token_access,
                'oauth_token_secret': user_profile.oauth_token_secret,
                'seed': user_profile.seed,
            }
            users.append(user_data)
            if user_profile.seed:
                seeds[user_profile.seed] = user_profile.user_id
            else:
                #Setting a list of users with no seed
                users_no_seed.append(user_data)
        # Lock users list for now just to make sure the other threads are
        # working with a complete user list
        if users_no_seed: users_lock.acquire(); release_lock = True
        while users_no_seed: #Assign free users to seeds in a *balanced way*
            user_data = users_no_seed.pop()
            sorted(seeds, cmp=lambda x, y: cmp(len(x), len(y)))
            seed_id = seeds.keys()[-1]
            seeds[seed_id].append(user_data['id'])

            #Notifying the seed of the assigned user
            self.beanstalk_connection.use(seed_id)
            self.beanstalk_connection.put(json.dumps({
                'op': 'new',
                'data': user_data
            }))
        if release_lock: users_lock.release()

if __name__ == "__main__":
    try:
        main_thread = MainThread()
        main_thread.start()

        seed_thread = SeedHandler()
        seed_thread.setDaemon(True)
        seed_thread.start()

        django_thread = DjangoHandler()
        django_thread.setDaemon(True)
        django_thread.start()

    except KeyboardInterrupt:
        print "Wait to kill all threads"
        seed_thread.join(1)
        django_thread.join(1)
        sys.exit(1)
