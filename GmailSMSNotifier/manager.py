#!/usr/bin/env python
__doc__ = """ Distributes work accross multiple seed clients. """

import time
import copy
import beanstalkc
import json
import os
import sys
from threading import Thread, Lock
import logging

LOG_FILENAME = 'manager.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

#Django
from django.core.management import setup_environ
from django.core.mail import mail_admins

DJANGO_PATH = '/home/sasha/django/gmailsms'
sys.path.append(DJANGO_PATH)
import settings
setup_environ(settings)

from settings import BEANSTALKD_SERVER, BEANSTALKD_TUBES
from accounts.models import UserProfile, UserProfileLabel, UserProfileEmail

profiles = [] # User profiles list
users_lock = Lock()

seeds = dict() # Stores which user on which seed is located
for tube in BEANSTALKD_TUBES:
    seeds.setdefault(tube, [])

users_no_seed = []

def beanstalk_connection():
    """ Return a beanstackc connection """
    try:
        return beanstalkc.Connection(**BEANSTALKD_SERVER)
    except Exception, e:
        mail_admins("Gmail-SMS Error (manager)", "Beankstalk connection\n%s" % e)
        sys.exit(2)

class DjangoHandler(Thread):
    """ Handles work from Django
    If a new user is created then assign it to a free seed
    If some user data is modified notify the seed of it.

    """
    def __init__(self):
        Thread.__init__(self)
        self.beanstalk_connection = beanstalk_connection()
        self.beanstalk_connection.watch('default')

    def run(self):
        notification = json.loads(self.beanstalk_connection.reserve().body)

class SeedHandler(Thread):
    """ Processing data received from seeds. Confirmations, Notifications stats

    """
    def __init__(self):
        Thread.__init__(self)
        self.beanstalk_connection = beanstalk_connection()
        self.beanstalk_connection.watch('manager')

    def run(self):
        while True:
            notification = json.loads(self.beanstalk_connection.reserve().body)

class MainThread(Thread):
    """ Getting userdata (labels, seed location, etc.) from django
    Allocating users to seeds using beanstalkd

    """
    def run(self):
        while True:
            #Reading all users from the DB
            user_profiles = UserProfile.objects.select_related().filter(stop=0).\
                            exclude(oauth_token_access='').filter(user=1).all()
            for user_profile in user_profiles:
                user_labels = user_profile.userprofilelabel_set.values()
                labels = [label['name'] for label in user_labels
                          if label.get('name', None)]
                if not labels: # No labels == no notifications
                    break

                profiles.append(user_profile)
                if user_profile.seed is not None:
                    seeds[user_profile.seed] = user_profile.user_id
                else:
                    #Setting a list of users with no seed
                    users_no_seed.append(user_profile)

            # Lock users list for now just to make sure the other threads are
            # working with a complete user list
            if users_no_seed:
                users_lock.acquire()
                #Assign free users to seeds in a *balanced way*
                while users_no_seed:
                    profile = users_no_seed.pop()
                    sorted(seeds, cmp=lambda x, y: cmp(len(x), len(y)))
                    seed_id = seeds.keys()[-1]
                    seeds[seed_id].append(profile.user_id)

                    #Notifying the seed of the assigned user using it's channel
                    self.beanstalk_connection.use(seed_id)
                    self.beanstalk_connection.put(json.dumps({
                        'op': 'new',
                        'data': {
                            'id': profile.user_id,
                            'email': profile.user.email,
                            'labels': labels,
                            'oauth_token_access':
                                user_profile.oauth_token_access,
                            'oauth_token_secret':
                                user_profile.oauth_token_secret
                        }
                    }))
                    user_profile.seed = seed_id
                    user_profile.save()
                users_lock.release()
            time.sleep(5)

if __name__ == "__main__":
    try:
        main_thread = MainThread()
        main_thread.start()

        seed_thread = SeedHandler()
        seed_thread.start()

        django_thread = DjangoHandler()
        django_thread.start()

    except KeyboardInterrupt:
        print "Wait to kill all threads"
        main_thread.join(1)
        seed_thread.join(1)
        django_thread.join(1)
        sys.exit(1)
