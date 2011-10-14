#!/usr/bin/python
# -*- coding: utf-8 -*-
from parser import TransportStreamFile, parse_ts
import xmltv
import sys
import getopt
from constant import *

def usage():
    print '''USAGE: epgdump_py -c CHANNEL_ID -i INPUT_FILE -o OUTPUT_FILE
       epgdump_py -b -i INPUT_FILE -o OUTPUT_FILE
  -h, --help        print help message
  -b, --bs          output BS channel
  -c, --channel-id  specify channel identifier
  -d, --debug       parse all ts packet
  -f, --format      format xml
  -i, --input       specify ts file
  -o, --output      specify xml file
'''

try: 
    opts, args = getopt.getopt(sys.argv[1:], 'hbc:dfi:o:', ['help', 'bs', 'channel-id=', 'debug', 'format', 'input=', 'output='])
except IndexError, getopt.GetoptError:
    usage()
    sys.exit(1)

channel_id = None
input_file = None
output_file = None
pretty_print = False
debug = False
b_type = TYPE_DEGITAL
for o,a in opts:
    if o in ('-h', '--help'):
        usage()
        sys.exit(0)
    elif o in ('-b', '--bs'):
        b_type = TYPE_BS
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

if (b_type == TYPE_DEGITAL and channel_id == None) or input_file == None or output_file == None:
    usage()
    sys.exit(1)

tsfile = TransportStreamFile(input_file, 'rb')
(service, events) = parse_ts(b_type, tsfile, debug)
tsfile.close()
xmltv.create_xml(b_type, channel_id, service, events, output_file, pretty_print)

# for event in events:
#     print "%s %s %s" % (
#             service[event.service_id],
#             event.start_time,
#             event.desc_short.event_name)
