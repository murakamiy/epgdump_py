#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import copy
import array
import aribstr
from constant import *
from aribtable import *

class TransportStreamFile(file):
    def next(self):
        try:
            sync = self.read(1)
            while ord(sync) != 0x47:
                sync = self.read(1)
        except TypeError:
            raise StopIteration
        data = self.read(187)
        packet = array.array('B', data)
        packet.insert(0, ord(sync))
        if len(packet) != 188:
            raise StopIteration
        return packet

def mjd2datetime(payload):
    mjd = (payload[0] << 8) | payload[1]
    yy_ = int((mjd - 15078.2) / 365.25)
    mm_ = int((mjd - 14956.1 - int(yy_ * 365.25)) / 30.6001)
    k = 1 if 14 <= mm_ <= 15 else 0
    day = mjd - 14956 - int(yy_ * 365.25) - int(mm_ * 30.6001)
    year = 1900 + yy_ + k
    month = mm_ - 1 - k * 12
    hour = ((payload[2] & 0xF0) >> 4) * 10 + (payload[2] & 0x0F)
    minute = ((payload[3] & 0xF0) >> 4) * 10 + (payload[3] & 0x0F)
    second = ((payload[4] & 0xF0) >> 4) * 10 + (payload[4] & 0x0F)
    return datetime.datetime(year, month, day, hour, minute, second)

def bcd2time(payload):
    hour = ((payload[0] & 0xF0) >> 4) * 10 + (payload[0] & 0x0F)
    minute = ((payload[1] & 0xF0) >> 4) * 10 + (payload[1] & 0x0F)
    second = ((payload[2] & 0xF0) >> 4) * 10 + (payload[2] & 0x0F)
    return datetime.timedelta(hours=hour, minutes=minute, seconds=second)

def parseShortEventDescriptor(idx, event, t_packet, b_packet):
    descriptor_tag = b_packet[idx]        # 8   uimsbf
    descriptor_length = b_packet[idx + 1] # 8   uimsbf
    ISO_639_language_code = (
            chr(b_packet[idx + 2]) +
            chr(b_packet[idx + 3]) +
            chr(b_packet[idx + 4]))       # 24 bslbf
    event_name_length = b_packet[idx + 5] # 8 uimsbf
    arib = aribstr.AribString(b_packet[idx + 6:idx + 6 + event_name_length])
    (event_name,symbol) = arib.convert_utf_split()
    idx = idx + 6 + event_name_length
    text_length = b_packet[idx]           # 8 uimsbf
    arib = aribstr.AribString(b_packet[idx + 1:idx + 1 + text_length])
    text = arib.convert_utf()
    text = symbol + "\n" + text
    desc = ShortEventDescriptor(descriptor_tag, descriptor_length,
            ISO_639_language_code, event_name_length, event_name,
            text_length, text)
    event.descriptors.append(desc)

def parseExtendedEventDescriptor(idx, event, t_packet, b_packet):
    descriptor_tag = b_packet[idx]        # 8 uimsbf
    descriptor_length = b_packet[idx + 1] # 8 uimsbf
    descriptor_number = (b_packet[idx + 2] >> 4)        # 4 uimsbf
    last_descriptor_number = (b_packet[idx + 2] & 0x0F) # 4 uimsbf
    ISO_639_language_code = (
            chr(b_packet[idx + 3]) +
            chr(b_packet[idx + 4]) +
            chr(b_packet[idx + 5]))       # 24 bslbf
    length_of_items = b_packet[idx + 6]   # 8 uimsbf
    idx = idx + 7
    length = idx + length_of_items
    item_list = []
    while idx < length:
        item_description_length = b_packet[idx] # 8 uimsbf
        item_description = b_packet[idx + 1:idx + 1 + item_description_length]
        idx = idx + 1 + item_description_length
        item_length = b_packet[idx]             # 8 uimsbf
        item = b_packet[idx + 1:idx + 1 + item_length]
        item_list.append(Item(item_description_length, item_description,
            item_length, item))
        idx = idx + 1 + item_length
    text_length = b_packet[idx] # 8 uimsbf
    arib = aribstr.AribString(b_packet[idx + 1:idx + 1 + text_length])
    text = arib.convert_utf()
    desc = ExtendedEventDescriptor(descriptor_tag, descriptor_length,
            descriptor_number, last_descriptor_number, ISO_639_language_code,
            length_of_items, item_list, text_length, text)
    event.descriptors.append(desc)

def parseContentDescriptor(idx, event, t_packet, b_packet):
    descriptor_tag = b_packet[idx]        # 8 uimsbf
    descriptor_length = b_packet[idx + 1] # 8 uimsbf
    idx += 2
    length = idx + descriptor_length
    content_list = []
    while idx < length:
        content_nibble_level_1 = 'UNKNOWN'
        content_nibble_level_2 = 'UNKNOWN'
        try:
            c_map = CONTENT_TYPE[(b_packet[idx] >> 4)]                # 4 uimsbf
            content_nibble_level_1 = c_map[0]
            content_nibble_level_2 = c_map[1][(b_packet[idx] & 0x0F)] # 4 uimsbf
        except KeyError:
            pass
        user_nibble_1 = (b_packet[idx + 1] >> 4)          # 4 uimsbf
        user_nibble_2 = (b_packet[idx + 1] & 0x0F)        # 4 uimsbf
        content = ContentType(content_nibble_level_1, content_nibble_level_2,
                user_nibble_1, user_nibble_2)
        content_list.append(content)
        idx += 2
    desc = ContentDescriptor(descriptor_tag, descriptor_length, content_list)
    event.descriptors.append(desc)

def parseServiceDescriptor(idx, service, t_packet, b_packet):
    descriptor_tag = b_packet[idx]        # 8 uimsbf
    descriptor_length = b_packet[idx + 1] # 8 uimsbf
    service_type = b_packet[idx + 2]      # 8 uimsbf
    service_provider_name_length = b_packet[idx + 3] # 8 uimsbf
    arib = aribstr.AribString(b_packet[idx + 4:idx + 4 + service_provider_name_length])
    service_provider_name = arib.convert_utf()
    idx = idx + 4 + service_provider_name_length
    service_name_length = b_packet[idx]   # 8 uimsbf
    arib = aribstr.AribString(b_packet[idx + 1:idx + 1 + service_name_length])
    service_name = arib.convert_utf()
    sd = ServiceDescriptor(descriptor_tag, descriptor_length, service_type,
            service_provider_name_length, service_provider_name,
            service_name_length, service_name)
    service.descriptors.append(sd)

def parseDescriptors(idx, table, t_packet, b_packet):
    iface = {
            TAG_SED:parseShortEventDescriptor,
            TAG_EED:parseExtendedEventDescriptor,
            TAG_CD :parseContentDescriptor,
            TAG_SD :parseServiceDescriptor}
    length = idx + table.descriptors_loop_length
    while idx < length:
        descriptor_tag = b_packet[idx]        # 8   uimsbf
        descriptor_length = b_packet[idx + 1] # 8   uimsbf
        if descriptor_tag in iface.keys():
            iface[descriptor_tag](idx, table, t_packet, b_packet)
        idx = idx + 2 + descriptor_length

def parseEvents(t_packet, b_packet):
    idx = 19
    length = t_packet.eit.section_length - idx
    while idx < length:
        event_id = (b_packet[idx] << 8) + b_packet[idx + 1]   # 16  uimsbf
        start_time = mjd2datetime(b_packet[idx + 2 :idx + 7]) # 40  bslbf
        duration = bcd2time(b_packet[idx + 7:idx + 10])       # 24  uimsbf
        running_status = (b_packet[idx + 10] >> 5)            # 3   uimsbf
        free_CA_mode = ((b_packet[idx + 10] >> 4) & 0x01)     # 1   bslbf
        descriptors_loop_length = ((b_packet[idx + 10] & 0x0F) << 8) + b_packet[idx + 11] # 12  uimsbf
        event = Event(event_id, start_time, duration,
                running_status, free_CA_mode, descriptors_loop_length)
        parseDescriptors(idx + 12, event, t_packet, b_packet)
        t_packet.eit.events.append(event)
        idx = idx + 12 + descriptors_loop_length

def parseService(t_packet, b_packet):
    idx = 16
    length = t_packet.sdt.section_length - idx
    while idx < length:
        service_id = (b_packet[idx] << 8) + b_packet[idx + 1] # 16 uimsbf
        # reserved_future_use 3 bslbf
        EIT_user_defined_flags = ((b_packet[idx + 2] >> 2) & 0x07) # 3 bslbf
        EIT_schedule_flag = ((b_packet[idx + 2] >> 1) & 0x01)      # 1 bslbf
        EIT_present_following_flag = (b_packet[idx + 2] & 0x01)          # 1 bslbf
        running_status = ((b_packet[idx + 3] >> 5) & 0x03)               # 3 uimsbf
        free_CA_mode = ((b_packet[idx + 3] >> 4) & 0x01)                 # 1 bslbf
        descriptors_loop_length = (((b_packet[idx + 3] & 0x0F) << 8) + b_packet[idx + 4]) # 12 uimsbf
        service = Service(service_id, EIT_user_defined_flags, EIT_schedule_flag,
                EIT_present_following_flag, running_status, free_CA_mode,
                descriptors_loop_length)
        parseDescriptors(idx + 5, service, t_packet, b_packet)
        t_packet.sdt.services.append(service)
        idx = idx + 5 + descriptors_loop_length

def add_event(event_map, t_packet):
    for event in t_packet.eit.events:
        master = event_map.get(event.event_id)
        if master == None:
            master = copy.copy(event)
            master.descriptors = None
            event_map[event.event_id] = master
        for desc in event.descriptors:
            tag = desc.descriptor_tag
            if tag == TAG_SED:
                master.desc_short = desc
            if tag == TAG_CD:
                master.desc_content = desc
            elif tag == TAG_EED:
                if master.desc_extend == None:
                    master.desc_extend = desc.items
                else:
                    master.desc_extend.extend(desc.items)

def fix_events(events):
    event_list = []
    for event in events:
        item_list = []
        item_map = {}
        if event.desc_short == None:
            continue
        if event.desc_extend != None:
            for item in event.desc_extend:
                if item.item_description_length == 0:
                    item_list[-1].item.extend(item.item)
                    item_list[-1].item_length += item.item_length
                else:
                    item_list.append(item)
            for item in item_list:
                arib = aribstr.AribString(item.item_description)
                item.item_description = arib.convert_utf()
                arib = aribstr.AribString(item.item)
                item.item = arib.convert_utf()
            for item in item_list:
                item_map[item.item_description] = item.item
            event.desc_extend = item_map
        event_list.append(event)
    return event_list

def parse_section(header, section_map, b_packet):
    sect = None
    next_packet = False
    sect = section_map.get(header.pid, Section())

    if header.payload_unit_start_indicator == 1:
        if sect.length_total == 0:
            section_length = 180
            if header.pointer_field > 179:
#                 print 'section 01 header.pointer_field > 179'
                next_packet = True
                sect = None
            else:
#                 if header.pointer_field > 0:
#                     print 'pointer_field %i' % header.pointer_field
                sect.idx += header.pointer_field
                section_length -= header.pointer_field
                sect.length_total = (((b_packet[sect.idx + 1] & 0x0F) << 8) + b_packet[sect.idx + 2]) # 12 uimsbf
                if sect.length_total < 15:
#                     print 'section 02 section_length < 15'
                    next_packet = True
                    sect = None
                elif sect.length_total <= section_length:
                    sect.data.extend(b_packet[sect.idx:sect.idx + 3 + sect.length_total])
                    sect.idx += sect.length_total + 3
                    sect.length_current += sect.length_total
                    section_map[header.pid] = sect
#                     print 'section 03 %04i %04i %04i' % (sect.length_total, sect.length_current, sect.idx)
                    next_packet = False
                else:
                    sect.data.extend(b_packet[sect.idx:])
                    sect.length_current += section_length
                    sect.idx = 5
                    section_map[header.pid] = sect
#                     print 'section 04 %04i %04i %04i' % (sect.length_total, sect.length_current, sect.idx)
                    next_packet = True
                    sect = None
        else:
            remain = sect.length_total - sect.length_current
            section_length = 180 - sect.length_prev
            if remain == 0:
                next_packet = True
                section_map[header.pid] = Section()
                section_header = 0
                if sect.idx < 182:
                    if sect.length_prev:
                        prev = 3
                    else:
                        prev = 0
                    sect = Section(sect.idx + prev, sect.idx - 5 + prev)
                    section_header = (b_packet[sect.idx] << 16) + (b_packet[sect.idx + 1] << 8) + (b_packet[sect.idx + 2])
                    if section_header != 0xFFFFFF:
                        sect.length_total = (((b_packet[sect.idx + 1] & 0x0F) << 8) + b_packet[sect.idx + 2]) # 12 uimsbf
                        section_map[header.pid] = sect
                        next_packet = False
#                 print 'section 05 %04i %04i %04i %04i %04i' % (sect.length_total, sect.length_current, sect.idx, remain, sect.length_prev)
                sect = None
            elif remain <= section_length:
                sect.data.extend(b_packet[sect.idx:sect.idx + 3 + remain])
                sect.idx += remain
                sect.length_current += remain
                section_map[header.pid] = sect
#                 print 'section 06 %04i %04i %04i %04i' % (sect.length_total, sect.length_current, sect.idx, remain)
                next_packet = False
            else:
                sect.data.extend(b_packet[sect.idx:])
                sect.length_current += section_length
                sect.length_prev = 0
                sect.idx = 5
                section_map[header.pid] = sect
#                 print 'section 07 %04i %04i %04i %04i' % (sect.length_total, sect.length_current, sect.idx, remain)
                next_packet = True
                sect = None
    else:
        # payload_unit_start_indicater set to 0b indicates that there is no pointer_field
        if sect.length_total != 0:
            sect.data.extend(b_packet[4:])
            sect.length_current += 184
            if sect.length_current >= sect.length_total:
                section_map[header.pid] = Section()
#                 print 'section 08 %04i %04i %04i' % (sect.length_total, sect.length_current, sect.idx)
                next_packet = False
            else:
                sect.length_prev = 0
#                 print 'section 09 %04i %04i %04i' % (sect.length_total, sect.length_current, sect.idx)
                sect = None
                next_packet = True
        else:
            sect.length_prev = 0
#             print 'section 10 %04i %04i %04i' % (sect.length_total, sect.length_current, sect.idx)
            sect = None
            next_packet = True
    return (next_packet, sect)

def parse_header(b_packet):
    pid = ((b_packet[1] & 0x1F) << 8) + b_packet[2]
    payload_unit_start_indicator = ((b_packet[1] >> 6) & 0x01)
    adaptation_field_control = ((b_packet[3] >> 4) & 0x03)
    pointer_field = b_packet[4]
    return TransportPacketHeader(pid, payload_unit_start_indicator, adaptation_field_control, pointer_field)

def parse_eit(service_id, tsfile, debug):
    # Event Information Table
    event_map = {}
    section_map = {}
    counter = 0
#     i = 0
    for b_packet in tsfile:
        counter += 1
        if not debug:
            if counter >= 700000:
                break
        header = parse_header(b_packet)
        if header.pid in EIT_PID and header.adaptation_field_control == 1:
#             i += 1
#             print '\neit 1 0x%X %04i' % (header.pid, i)
            (next_packet, section) = parse_section(header, section_map, b_packet)
            while not next_packet:
                if section:
                    try:
                        t_packet = TransportPacket(header, section.data)
                    except CRC32MpegError, e:
                        print 'CRC32MpegError', e
                        section_map.pop(header.pid)
                        break
#                     print 'service_id %i %i' % (service_id, t_packet.eit.service_id)
                    if t_packet.eit.service_id == service_id:
                        parseEvents(t_packet, section.data)
                        add_event(event_map, t_packet)
#                 i += 1
#                 print '\neit 2 0x%X %04i' % (header.pid, i)
                (next_packet, section) = parse_section(header, section_map, b_packet)
    event_list = event_map.values()
    event_list.sort(compare)
    event_list = fix_events(event_list)
    if debug:
        print '%i packets read' % (counter)
    return event_list

def compare(x, y):
    return int((x.start_time - y.start_time).total_seconds())

def parse_sdt(tsfile):
    # Service Description Table
    sdt_map = {}
    for b_packet in tsfile:
        header = parse_header(b_packet)
        if header.pid == SDT_PID and header.adaptation_field_control == 1 and header.payload_unit_start_indicator == 1:
            try:
                t_packet = TransportPacket(header, b_packet)
            except CRC32MpegError, e:
                print 'CRC32MpegError', e
                continue
            parseService(t_packet, b_packet)
            for service in t_packet.sdt.services:
                sdt_map[service.service_id] = service
            break
    return sdt_map[min(sdt_map.keys())]

def parse_ts(tsfile, debug):
    service = parse_sdt(tsfile)
    tsfile.seek(0)
    events = parse_eit(service.service_id, tsfile, debug)
    return (service, events)
