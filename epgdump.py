#!/usr/bin/python
# -*- coding: utf-8 -*-
from parser import TransportStreamFile, parse_ts
import xmltv
import sys
import getopt

def usage():
    print '''USAGE: epgdump_py -c CHANNEL_ID -i INPUT_FILE -o OUTPUT_FILE
  -h, --help        print help message
  -c, --channel-id  specify channel identifier
  -d, --debug       parse all ts packet
  -f, --format      format xml
  -i, --input       specify ts file
  -o, --output      specify xml file
'''

try: 
    opts, args = getopt.getopt(sys.argv[1:], 'hc:dfi:o:', ['help', 'channel-id=', 'debug', 'format', 'input=', 'output='])
except IndexError, getopt.GetoptError:
    usage()
    sys.exit(1)

channel_id = None
input_file = None
output_file = None
pretty_print = False
debug = False
for o,a in opts:
    if o in ('-h', '--help'):
        usage()
        sys.exit(0)
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

if channel_id == None or input_file == None or output_file == None:
    usage()
    sys.exit(1)

tsfile = TransportStreamFile(input_file, 'rb')
(service, events) = parse_ts(tsfile, debug)
tsfile.close()
xmltv.create_xml(channel_id, service, events, output_file, pretty_print)

# print service
# for desc in service.descriptors:
#     print desc
# 
# for event in events:
#     content = '\t' 
#     item_desc = '\t'
#     event_name = event.desc_short.event_name
#     if event.desc_content != None:
#         for ct in event.desc_content.content_type_array:
#             content += 'L1=' + ct.content_nibble_level_1 + ' ' + 'L2=' + ct.content_nibble_level_2 + '\t\t'
#     count = 1
#     for (k,v) in event.desc_extend.items():
#         item_desc += 'NAME' + str(count) + '=' + k + '\tDESC' + str(count) + '=' + v + '\t\t'
#         count += 1
# 
#     print '%i %s %s %s %s' % (
#             event.event_id, event.start_time, event_name, content, item_desc)
