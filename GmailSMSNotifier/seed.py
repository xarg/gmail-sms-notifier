import sys
import logging
import beanstalkc
import json
from threading import Thread, Lock
import cPickle
from ConfigParser import ConfigParser

from libs.gcal import Calendar # Access Google Calendar
from libs.gmail import Gmail # Access Gmail via RSS Feed

LOG_FILENAME = 'seed.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

FAIL_ATTEMPTS = 2 #No. of failed attempts to authenticate
UNAUTHORIZED_ACCESS = {}
DELETE_EVENT_AFTER = 180 #Delete event after 180s

def beanstalk_connection(conn):
    """ Return a beanstackc connection """
    try:
        return beanstalkc.Connection(host=conn['host'], port=int(conn['port']))
    except:
        logging.exception("Beanstalk connection failed")
        sys.exit(2)

class User(object):
    """Dummy object used to save user info into a pickled file"""
    def __init__(self, kw):
        for key, val in kw.items():
            setattr(self, key, val)

class Seed(Thread):
    """Handles info passed from the manager. """
    def __init__(self, config_file):
        super(Seed, self).__init__()
        self.config_file = config_file
        config = self.config()
        self.beanstalk = beanstalk_connection(dict(config.items('beanstalk')))
        self.beanstalk.watch(config.get('seed', 'id'))

    def notify(self, user):
        """Create notifications for a user. Try to login using it's credentials"""
        config = self.config()
        unauthorized = False
        gauth = dict(
            oauth_consumer_key=config.get('oauth', 'oauth_consumer_key'),
            oauth_consumer_secret=config.get('oauth', 'oauth_consumer_secret'),
            oauth_token_access=user.oauth_token_access,
            oauth_token_secret=user.oauth_token_secret
        )
        gmail = Gmail('OAuth', labels=user.labels)
        gmail.login(**gauth)
        import pdb; pdb.set_trace()
        entries = gmail.entries()

        if entries['error'] == 'Unauthorized':
            unauthorized = True
            if user.id not in UNAUTHORIZED_ACCESS:
                UNAUTHORIZED_ACCESS[user.id] = 1
            elif UNAUTHORIZED_ACCESS[user.id] >= FAIL_COUNT:
                pass
            else:
                UNAUTHORIZED_ACCESS[user.id] +=1
        else:
            if user.id in UNAUTHORIZED_ACCESS:
                del(UNAUTHORIZED_ACCESS[user.id])

        #Add event to calendar
        if not unauthorized:
            calendar = Calendar('OAuth')
            calendar.login(**gauth)
            events = []
            for label in entries['entries']:
                for entry in entries['entries'][label]:
                    label_text = "Inbox" if label == '^inbox' else label
                    try:
                        #This email has been verified
                        UserEmail.objects.filter(user=user.id).filter(
                            email_id=entry['id']).get()
                    except UserEmail.DoesNotExist:
                        user_email = UserEmail(user_id=user.id,
                                               email_id=entry['id'])
                        events.append(calendar.create(
                            title="("+entry['author_name']+") " +
                            entry['title'], where = label_text))
                        user_email.save() # Event created save log
            time.sleep(DELETE_EVENT_AFTER)
            for event in events: # Clean calendar from added notifications
                calendar.delete(event)

    def config(self, new_config=None):
        """Read or write new configuration"""
        if new_config is None:
            parser = ConfigParser()
            parser.readfp(open(self.config_file))
            return parser
        else:
            with open(config_file, 'wb') as configfile:
                new_config.write(self.configfile)

    def new_user(self, user_dict):
        "Handle new users"
        users = self.users()
        users.append(User(user_dict))
        self.users(users)

    def users(self, users=[]):
        """ Read or write users logfile"""
        users_file = self.config().get('seed', 'users')
        if users == []:
            try:
                return cPickle.load(open(users_file))
            except IOError:
                return []
        else:
            pickler = cPickle.Pickler(open(users_file, 'wb'))
            pickler.dump(users)

    def run(self):
        """ Read new jobs from manager.
        Read through

        """
        while True:
            job = self.beanstalk.reserve()
            data = json.loads(job.body)

            #Parsing operations
            if data['op'] == 'new':
                self.new_user(data['data'])
            elif data['op'] == 'del':
                self.del_user(data['data'])

            users = self.users()
            for user in users:
                self.notify(user)
            #job.delete()
def main():
    import getopt, sys
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c", ["config"])
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2)

    config_file = 'config.ini'
    for o, a in opts:
        if o in ("-c", "--config"):
            config_file = a
        else:
            assert False, "unhandled option"
    try:
        main_thread = Seed(config_file)
        main_thread.start()

    except KeyboardInterrupt:
        print "Wait to kill all threads"
        main_thread.join(1)
        sys.exit(1)

if __name__ == '__main__':
    main()
