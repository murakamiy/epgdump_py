#!/usr/bin/python
# -*- coding: utf-8 -*-
from parser import TransportStreamFile, parse_ts
import xmltv
import sys
import getopt
import time
from constant import *

def usage():
    print >> sys.stderr, '''USAGE: epgdump_py -c CHANNEL_ID -i INPUT_FILE -o OUTPUT_FILE
       epgdump_py -b -i INPUT_FILE -o OUTPUT_FILE
       epgdump_py -s -i INPUT_FILE -o OUTPUT_FILE
       epgdump_py [-b|-s] -p TRANSPORT_STREAM_ID:SERVICE_ID:EVENT_ID -i INPUT_FILE
  -h, --help        print help message
  -b, --bs          input file is BS channel
  -s, --cs          input file is CS channel
  -c, --channel-id  specify channel identifier
  -d, --debug       parse all ts packet
  -f, --format      format xml
  -i, --input       specify ts file
  -o, --output      specify xml file
  -p, --print-time  print start time, and end time of specifeid id
  -e, --event-id    output transport_stream_id, servece_id and event_id
'''

try: 
    opts, args = getopt.getopt(sys.argv[1:], 'hbsc:dfi:o:p:e', ['help', 'bs', 'cs', 'channel-id=', 'debug', 'format', 'input=', 'output=', 'print-time=', 'event-id'])
except IndexError, getopt.GetoptError:
    usage()
    sys.exit(1)

channel_id = None
input_file = None
output_file = None
pretty_print = False
debug = False
b_type = TYPE_DEGITAL
transport_stream_id = None
service_id = None
event_id = None
output_eid = False
for o,a in opts:
    if o in ('-h', '--help'):
        usage()
        sys.exit(0)
    elif o in ('-b', '--bs'):
        b_type = TYPE_BS
    elif o in ('-s', '--cs'):
        b_type = TYPE_CS
    elif o in ('-c', '--channel-id'):
        channel_id = a
    elif o in ('-d', '--debug'):
        debug = True
    elif o in ('-f', '--format'):
        pretty_print = True
    elif o in ('-i', '--input'):
        input_file = a
    elif o in ('-o', '--output'):
        output_file = a
    elif o in ('-p', '--print-time'):
        arr = a.split(':')
        transport_stream_id = int(arr[0])
        service_id = int(arr[1])
        event_id = int(arr[2])
    elif o in ('-e', '--event-id'):
        output_eid = True

if service_id == None and (
        (b_type == TYPE_DEGITAL and channel_id == None) or input_file == None or output_file == None):
    usage()
    sys.exit(1)
elif input_file == None:
    usage()
    sys.exit(1)

tsfile = TransportStreamFile(input_file, 'rb')
(service, events) = parse_ts(b_type, tsfile, debug)
tsfile.close()
if service_id == None:
    xmltv.create_xml(b_type, channel_id, service, events, output_file, pretty_print, output_eid)
else:
    start_time = None
    end_time = None
    for event in events:
        if (event.transport_stream_id == transport_stream_id and
            event.service_id == service_id and
            event.event_id == event_id):
            start_time = event.start_time
            end_time = event.start_time + event.duration
            break
    if start_time == None:
        print >> sys.stderr, "not found: transport_stream_id=%d service_id=%d event_id=%d" % (transport_stream_id, service_id, event_id)
        sys.exit(1)
    else:
        print int(time.mktime(start_time.timetuple())), int(time.mktime(end_time.timetuple()))
