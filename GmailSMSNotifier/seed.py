import MySQLdb
import logging
from threading import Thread, Lock
import time
from ConfigParser import ConfigParser
import sys

from libs.gcal import Calendar # Access Google Calendar
from libs.gmail import Gmail # Access Gmail via RSS Feed

LOG_FILENAME = 'seed.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

MAX_THREADS = 2
FAIL_ATTEMPTS = 5 #No. of failed attempts to authenticate
UNAUTHORIZED_ACCESS = {}
DELETE_EVENT_AFTER = 180 #Delete event after 180s
CHECK_INTERVAL = 5

def config_(config_file, new_config=None):
    """Read or write new configuration"""
    if new_config is None:
        parser = ConfigParser()
        parser.readfp(open(config_file))
        return parser
    else:
        with open(config_file, 'wb') as configfile:
            new_config.write(self.configfile)

def get_db(config):
    """ Return cursor """
    try:
        return MySQLdb.connect(**dict(config.items('mysql')))
    except:
        logging.exception("Failed connection")
        time.sleep(5)
        return get_db(config)

class Seed(Thread):
    def __init__(self, user, config):
        super(Seed, self).__init__()
        self.user = user
        self.config = config
        self.db = get_db(config)
        self.cursor = self.db.cursor()

    def new_email(self, email_dict):
        """ Save a new email """
        self.cursor.execute("""
            INSERT INTO `accounts_userprofileemail` (
                            `user_profile_id`, `email_id`, `datetime_sent`)
                       VALUES (%s, %s, NOW())""", (email_dict['user_id'],
                                                   email_dict['id'],))
        self.db.commit()

    def email_exists(self, id):
        """ Get all e-mails or just of some users"""

        self.cursor.execute("""
            SELECT COUNT(`id`) FROM `accounts_userprofileemail`
            WHERE `email_id` = %s""", id)
        return False if int(self.cursor.fetchone()[0]) == 0 else True

    def run(self):
        """ Read new jobs from manager.
        Read through

        """
        #logging.info("Start checking %s %s", self.user['id'],
        #             self.user['labels'])
        unauthorized = False
        gauth = dict(
            oauth_consumer_key=self.config.get('oauth', 'oauth_consumer_key'),
            oauth_consumer_secret=self.config.get('oauth', 'oauth_consumer_secret'),
            oauth_token_access=self.user['oauth_token_access'],
            oauth_token_secret=self.user['oauth_token_secret']
        )
        gmail = Gmail('OAuth', labels=self.user['labels'])
        gmail.login(**gauth)
        entries = gmail.entries()
        if entries['error'] == 'Unauthorized':
            unauthorized = True
            if self.user['id'] not in UNAUTHORIZED_ACCESS:
                UNAUTHORIZED_ACCESS[self.user['id']] = 1
            elif UNAUTHORIZED_ACCESS[self.user['id']] >= FAIL_ATTEMPTS:
                self.cursor.execute("""UPDATE `accounts_userprofile` SET
                                    `oauth_token_access` = '',
                                    `oauth_token_secret` = '',
                                    `authorization_failed` = 1
                                    WHERE `id` = %s""", self.user['id'])
                self.db.commit()
            else:
                UNAUTHORIZED_ACCESS[self.user['id']] +=1
                time.sleep(2)
        else:
            if self.user['id'] in UNAUTHORIZED_ACCESS:
                del(UNAUTHORIZED_ACCESS[self.user['id']])

        #Add event to calendar
        events = []
        if not unauthorized:
            #logging.info("Found entries for %s", self.user['id'])
            calendar = Calendar('OAuth')
            calendar.login(**gauth)

            for label in entries['entries']:
                for entry in entries['entries'][label]:
                    label_text = "Inbox" if label == '^inbox' else label
                    if not self.email_exists(entry['id']):
                        #logging.info("Found entry (%s) for %s", entry,
                        #             self.user['id'])
                        self.new_email({'id': entry['id'],
                                        'user_id': self.user['id']})
                        events.append(calendar.create(
                            title="("+entry['author_name']+") " +
                            entry['title'], where=label_text))
        self.db.close()#Close db connection first

        if len(events):
            time.sleep(DELETE_EVENT_AFTER)
            for event in events: # Clean calendar from added notifications
                calendar.delete(event)
def main():
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:", ["config"])
    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2)

    config_file = 'config.ini'
    for o, a in opts:
        if o in ("-c", "--config"):
            config_file = a
        else:
            assert False, "unhandled option"
    threads = []
    config = config_(config_file)
    db = get_db(config)
    try:
        cursor = db.cursor()
        while True:
            cursor.execute("""SELECT `id`,
                           `oauth_token_access`,
                           `oauth_token_secret`
                           FROM `accounts_userprofile`
                           WHERE `stop` = 0 AND
                                 `oauth_token_access` <> '' AND
                                 `oauth_token_secret` <> '' AND
                                 `seed` = %s""",
                           config.get('seed', 'id'))
            for row in cursor.fetchall():
                user = {'id': row[0], 'oauth_token_access': row[1],
                                'oauth_token_secret': row[2], 'labels': []}
                cursor.execute("""SELECT `name` FROM `accounts_userprofilelabel`
                               WHERE `user_profile_id` = %s""", user['id'])
                user['labels'].extend([row[0] for row in cursor.fetchall()])
                if len(user['labels']):
                    thread = Seed(user, config)
                    thread.start()
                    threads.append(thread)
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print "Wait to kill all threads"
        db.close()
        for thread in threads:
            thread.join(1)
        sys.exit(1)

if __name__ == '__main__':
    main()
