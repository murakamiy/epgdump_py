#!/usr/bin/python
# -*- coding: utf-8 -*-
from parser import TransportStreamFile, parse_ts
import xmltv
import sys
import getopt
import time
from constant import *

def usage():
    print '''USAGE: epgdump_py -c CHANNEL_ID -i INPUT_FILE -o OUTPUT_FILE
       epgdump_py -b -i INPUT_FILE -o OUTPUT_FILE
       epgdump_py -s -i INPUT_FILE -o OUTPUT_FILE
       epgdump_py -p SERVICE_ID:EVENT_ID -i INPUT_FILE
  -h, --help        print help message
  -b, --bs          output BS channel
  -s, --cs          output CS channel
  -c, --channel-id  specify channel identifier
  -d, --debug       parse all ts packet
  -f, --format      format xml
  -i, --input       specify ts file
  -o, --output      specify xml file
  -p, --print-time  print start time, and end time of specifeid id
  -e, --event-id    output servece_id and event_id
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
        service_id = int(arr[0])
        event_id = int(arr[1])
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
        if event.service_id == service_id and event.event_id == event_id:
            start_time = event.start_time
            end_time = event.start_time + event.duration
            break
    if start_time == None:
        print "not found: service_id=%d event_id=%d" % (service_id, event_id)
    else:
        print int(time.mktime(start_time.timetuple())), int(time.mktime(end_time.timetuple()))

# for event in events:
#     print "%s %s %s" % (
#             service[event.service_id],
#             event.start_time,
#             event.desc_short.event_name)
