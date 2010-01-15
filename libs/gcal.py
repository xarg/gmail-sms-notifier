#!/usr/bin/env python

from xml.etree import ElementTree
import gdata.calendar.service
import gdata.service
import atom.service
import gdata.calendar
import atom
import getopt
import sys
import string
import time

class Calendar:
    def __init__(self, email, password):
        self.cal_client = gdata.calendar.service.CalendarService()
        self.cal_client.email = email
        self.cal_client.password = password
        self.cal_client.source = 'Google-Calendar_SMS_Notifier_1_0'
        self.cal_client.ProgrammaticLogin()
    def send(self, title):
        pass

    def _InsertEvent(self, title='Testing 1,2,3',
                     content='No content', where='On the moon',
                     start_time=None, end_time=None, recurrence_data=None):
        """Inserts a basic event using either start_time/end_time definitions
        or gd:recurrence RFC2445 icalendar syntax.  Specifying both types of
        dates is not valid.  Note how some members of the CalendarEventEntry
        class use arrays and others do not.  Members which are allowed to occur
        more than once in the calendar or GData "kinds" specifications are stored
        as arrays.  Even for these elements, Google Calendar may limit the number
        stored to 1.  The general motto to use when working with the Calendar data
        API is that functionality not available through the GUI will not be
        available through the API.  Please see the GData Event "kind" document:
        http://code.google.com/apis/gdata/elements.html#gdEventKind
        for more information"""

        event = gdata.calendar.CalendarEventEntry()
        event.title = atom.Title(text=title)
        event.content = atom.Content(text=content)
        event.where.append(gdata.calendar.Where(value_string=where))

        if recurrence_data is not None:
          # Set a recurring event
          event.recurrence = gdata.calendar.Recurrence(text=recurrence_data)
        else:
          if start_time is None:
            # Use current time for the start_time and have the event last 1 hour
            start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() + 6*60))
            end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z',
                time.gmtime(time.time() + 3600))
          event.when.append(gdata.calendar.When(start_time=start_time,
              end_time=end_time))

        new_event = self.cal_client.InsertEvent(event, '/calendar/feeds/default/private/full')
        return new_event

    def _AddReminder(self, event, minutes=5):
        """Adds a reminder to the event.  This uses the default reminder settings
        for the user to determine what type of notifications are sent (email, sms,
        popup, etc.) and sets the reminder for 'minutes' number of minutes before
        the event.  Note: you can only use values for minutes as specified in the
        Calendar GUI."""

        for a_when in event.when:
          if len(a_when.reminder) > 0:
            a_when.reminder[0].minutes = minutes
          else:
            a_when.reminder.append(gdata.calendar.Reminder(minutes=minutes))

        print 'Adding %d minute reminder to event' % (minutes,)
        return self.cal_client.UpdateEvent(event.GetEditLink().href, event)

    def _DeleteEvent(self, event):
        """Given an event object returned for the calendar server, this method
        deletes the event.  The edit link present in the event is the URL used
        in the HTTP DELETE request."""

        self.cal_client.DeleteEvent(event.GetEditLink().href)
if __name__ == '__main__':
    message = "Hello world"
    calendar = Calendar('x', 'y')
    event = calendar._InsertEvent(title = message)
    calendar._AddReminder(event)