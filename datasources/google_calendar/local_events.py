#!/usr/bin/env python
'''
Given my location, and some events, what is nearby?
'''

try:
    import json
except ImportError:
    import simplejson as json

try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree

import time
from urllib import urlencode, quote
import urllib2

import logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger({"__main__":None}.get(__name__, __name__))

import gdata.calendar
import gdata.calendar.service


## Utilities
def prompt(vars=None, message='# Welcome to the prompt!' ):
    ''' returns a prompt function, that uses ipython if available.
    
    usage:
    >>> p = prompt(globals(),)
    Then:  p() to call it.
    '''
    prompt_message = message
    try:
        from IPython.Shell import IPShellEmbed
        ipshell = IPShellEmbed(argv=[''],banner=prompt_message,exit_msg="# Goodbye")
        return  ipshell
    except ImportError:
        ## this doesn't quite work right, in that it doesn't go to the right env
        ## so we just fail.
        import code
        import rlcompleter
        import readline
        readline.parse_and_bind("tab: complete")
        # calling this with globals ensures we can see the environment
        print prompt_message
        if not vars:
            vars = globals()
        shell = code.InteractiveConsole(vars)
        return shell.interact

prompt_message='''type: print h for help '''
h = '''\
events: dictionary of feedname: events
events[key].entry  # list of events
events[key].entry[0].{when,where,content.text}
'''

## GEOCODING

mykey = ("ABQIAAAAXVtjfmq9Z7wk8jwIWCZ00BTgZOk5NR9Go3n4YJaFIbqsrUHaRRTpOFrFlWKKd7ImjQ29c_EWz08kbQ",
    "lind-beil.net")

def geocode_address(address,apikey=mykey[0]):
    params = dict(
        output='csv', # or json
        key=apikey,
        sensor='false',
        q=str(address),
    )
    url = "http://maps.google.com/maps/geo?" +  urlencode(params)
    logger.debug(url)
    handle = urllib2.urlopen(url)
        
    def parse_csv(body):
        code, accuracy, lat,long= body.split(",")
        return dict(code=int(code),accuracy=int(accuracy),
            lat=float(lat),long=float(long))
    
    def parse_json(body):
        return json.loads(body)

    return parse_csv(handle.read())


def distance((lat1, long1),(lat2,long2)):
    ''' assumes descartes / mercator projection, which is dumb, but okay'''
    return math.sqrt(sq_euclidean((lat1, long1),(lat2,long2)))

def sq_euclidean((lat1, long1),(lat2,long2)):
    '''returns squared euclidean distance'''
    # squared is better for the future, so that we can avoid unnecessary sqrts
    return (lat1 - lat2)**2 + (long1 - long2)**2


## CALENDAR STUFF

def email_to_feed(email):
    ''' given an email, get the google calendar feedname
    
    >>> quote('gregg.lind@example.com')
    'http://www.google.com/calendar/feeds/gregg.lind%40example.com/public/basic'
    '''
    if "@" not in email:
        email = email + "@gmail.com"
    sub = quote(email)
    return "http://www.google.com/calendar/feeds/%s/public/basic" % sub

def email_or_url(string):
    ''' true if likelier to be email. '''
    # extremely stupid/simple logic
    if "@" in string: return True
    elif string.startswith("http:") or string.startswith("https:"):
        return False
    return True


## NOTE:  no time zone handling in here at all.
# for fuller handling, cf: http://home.blarg.net/~steveha/pyfeed.html (BSD)
_format_RFC3339 = "%Y-%m-%dT%H:%M:%S"
def epoch_to_RFC3339(epoch):
    ''' convert epoch to RFC3339'''
    s = epoch
    try: 
        float(epoch)
        s = time.strftime(_format_RFC3339, time.gmtime(epoch))
    except (TypeError, ValueError):
        pass
    
    return s
    
def get_events_for_calendar(calendar, start=None, end=None):
    """
    calendar:  a string for the feed, e.g.:
        http://www.google.com/calendar/feeds/gregg.lind%40gmail.com/public/basic
    
    defaults:  30 days around time.time()
    see: http://code.google.com/apis/calendar/reference.html#Parameters"""
    
    if start is None:
        start = time.time() - 86400 * 30 # 30 days in the past-ish
    if end is None:
        end = time.time() + 86400 * 30 # 30 days in the future-ish
    
    orderby= 'starttime'  # lastmodified | starttime
    sortorder= 'd'  # a|d
    #  Use the RFC 3339 timestamp format. For example: 2005-08-09T10:57:00-08:00.
    start_min=epoch_to_RFC3339(start)      
    start_max=epoch_to_RFC3339(end)  
    
    if type(calendar) in (str,unicode):
        pass
    else:
        logger.exception(ValueError("eventaully we should be able to handle"
            "more sophisiticated feed types"))

    query = gdata.calendar.service.CalendarEventQuery('default', 'private', 
        'full')
    query.start_min = start_min
    query.start_max = start_max
    query.orderby = orderby
    query.sortder=sortorder
    query.feed=calendar
    logger.debug(query.__dict__)
    logger.debug(query.ToUri())
    client = gdata.calendar.service.CalendarService()
    try:
        feed = client.CalendarQuery(query)
    except gdata.service.RequestError:
        return None
    except Exception, exc:
        logger.exception(exc)
    
    for ii, an_event in enumerate(feed.entry):
      logger.debug( '\t%s. %s' % (ii, an_event.title.text ))
      for a_when in an_event.when:
        logger.debug( '\t\tStart time: %s ; End time: %s' % (a_when.start_time,a_when.end_time))
    return feed



def get_events(iterable_of_feeds):
    ''' get a bunch of feeds '''
    out = dict()
    for feed in iterable_of_feeds:
        out[feed] = get_events_for_calendar(feed)
    
    return out

def nearby_events():
    events = []
    return events

def read_calendar_file(fh):
    '''set of calendar feed names from a filehandle, fh
    
    fh: a filehandle
    
    can have comments (#), blank lines
    '''
    lines = (line.strip() + "#" for line in fh)
    lines = (line.split("#",1)[0] for line in lines)
    lines = set((line for line in lines if line))
    return lines



if __name__ == "__main__":
    import sys
    from optparse import OptionParser
    from __main__ import __doc__ as description ## too clever by half
    
    default_verbosity = logger.getEffectiveLevel()
    
    parser = OptionParser(description=description)
    parser.add_option('-v', action="count", dest="verbosity", default=0, help = '''more verbose [default: %i; substract 10]''' % default_verbosity)
    parser.add_option('-q', action="count", dest="quietude", default=0, help = '''quiet it down [default: %i; add 10]''' % default_verbosity)
    parser.add_option('--me', default="may day cafe, minneapolis, mn 55407", help = '''[quoted string] my location [default=%default]''')
    parser.add_option('--calfile', default="calendars.txt", help = '''file of calendars [default=%default]''')
    parser.add_option('-c','--calendar', dest="calendars", action="append", help = '''append a calendar to the list of calendars''')
    (options, args) = parser.parse_args()
    
    # verbosity!
    default_verbosity = logger.getEffectiveLevel()
    verbosity = -10 * options.verbosity + 10 * options.quietude + default_verbosity
    logger.setLevel(verbosity)
    logger.debug("logger verbosity is %i" % verbosity)
    
    logger.debug(options)

    # get calendars
    calendars = set()
    if options.calendars:  calendars |= set(options.calendars)
    if options.calfile:    
        calendars |= read_calendar_file(file(options.calfile))
    
    # convert them all to feeds
    calendars = set([[c,email_to_feed(c)][email_or_url(c)] for c in calendars])
    logger.debug("calendars are:")
    for c in calendars:
        logger.debug(c)
    
    
    # the meat....
    events = get_events(calendars)
    prompt(message=prompt_message)()
