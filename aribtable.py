#!/usr/bin/python
# -*- coding: utf-8 -*-
from constant import *
import array

class Section:
    def __init__(self, idx=5, length_prev=0):
        self.length_total = 0
        self.length_current = 0
        self.length_prev = length_prev
        self.idx = idx
        self.data = array.array('B', (0xFF,0xFF,0xFF,0xFF,0xFF))

class TransportPacketHeader:
    def __init__(self, pid, payload_unit_start_indicator, adaptation_field_control, pointer_field):
        self.pid = pid
        self.payload_unit_start_indicator = payload_unit_start_indicator
        self.adaptation_field_control = adaptation_field_control
        self.pointer_field = pointer_field

class TransportPacket:
    def __init__(self, header, packet):
        self.header = header
        self.binary_data = packet
        if header.pid in SDT_PID:
            self.sdt = ServiceDescriptionTable(packet)
        else:
            self.eit = EventInfomationTable(packet)
    def __str__(self):
        return ( 
        'pid=%04X\n'
        'payload_unit_start_indicator=%i\n'
        'adaptation_field_control=%i\n'
        'pointer_field=%i\n') % (
            self.header.pid, self.header.payload_unit_start_indicator,
            self.header.adaptation_field_control, self.header.pointer_field)

class ServiceDescriptionTable:
    def __init__(self, packet):
        self.table_id = packet[5]                        # 8 uimsbf
        self.section_syntax_indicator = (packet[6] >> 7) # 1 bslbf
        # reserved_future_use                         1 bslbf
        # reserved                                    2 bslbf
        self.section_length = ((packet[6] & 0x0F) << 8) + packet[7] # 12 uimsbf
        self.transport_stream_id = (packet[8] << 8) + packet[9]     # 16 uimsbf
        # reserved                                    2 bslbf
        self.version_number = ((packet[10] >> 1) & 0x1F) # 5 uimsbf
        self.current_next_indicator = (packet[10] & 0x01)# 1 bslbf
        self.section_number = packet[11]                 # 8 uimsbf
        self.last_section_number = packet[12]            # 8 uimsbf
        self.original_network_id = (packet[13] << 8) + packet[14] # 16 uimsbf
        # reserved_future_use                         8 bslbf
        self.services = []
        crc32mpeg(packet[5:self.section_length + 8], self.table_id, self.section_length)
    def __str__(self):
        return (
                ' table_id=0x%04X\n'
                ' section_syntax_indicator=%i\n'
                ' section_length=%i\n'
                ' transport_stream_id=%i\n'
                ' version_number=%i\n'
                ' current_next_indicator=%i\n'
                ' section_number=%i\n'
                ' last_section_number=%i\n'
                ' original_network_id=%i\n'
                ) % (
                        self.table_id,
                        self.section_syntax_indicator,
                        self.section_length,
                        self.transport_stream_id,
                        self.version_number,
                        self.current_next_indicator,
                        self.section_number,
                        self.last_section_number,
                        self.original_network_id
                        )

class Service:
    def __init__(self, service_id, EIT_user_defined_flags, EIT_schedule_flag,
            EIT_present_following_flag, running_status, free_CA_mode,
            descriptors_loop_length):
        self.service_id = service_id                           # 16 uimsbf
        self.EIT_user_defined_flags = EIT_user_defined_flags   # 3 bslbf
        self.EIT_schedule_flag = EIT_schedule_flag             # 1 bslbf
        self.EIT_present_following_flag = EIT_present_following_flag # 1 bslbf
        self.running_status = running_status                   # 3 uimsbf
        self.free_CA_mode = free_CA_mode                       # 1 bslbf
        self.descriptors_loop_length = descriptors_loop_length # 12 uimsbf
        self.descriptors = []
    def __str__(self):
        return (
                '  service_id=%i\n'
                '  EIT_user_defined_flags=%i\n'
                '  EIT_schedule_flag=%i\n'
                '  EIT_present_following_flag=%i\n'
                '  running_status=%i\n'
                '  free_CA_mode=%i\n'
                '  descriptors_loop_length=%i\n'
                ) % (
                        self.service_id,
                        self.EIT_user_defined_flags,
                        self.EIT_schedule_flag,
                        self.EIT_present_following_flag,
                        self.running_status,
                        self.free_CA_mode,
                        self.descriptors_loop_length)

class ServiceDescriptor:
    def __init__(self, descriptor_tag, descriptor_length, service_type,
            service_provider_name_length, service_provider_name,
            service_name_length, service_name):
        self.descriptor_tag = descriptor_tag
        self.descriptor_length = descriptor_length
        self.service_type = service_type
        self.service_provider_name_length = service_provider_name_length
        self.service_provider_name = service_provider_name
        self.service_name_length = service_name_length
        self.service_name = service_name
    def __str__(self):
        return (
                '   descriptor_tag=0x%02X\n'
                '   descriptor_length=%i\n'
                '   service_type=0x%02X\n'
                '   service_provider_name_length=%i\n'
                '   service_provider_name=%s\n'
                '   service_name_length=%i\n'
                '   service_name=%s\n'
                ) % (
                        self.descriptor_tag,
                        self.descriptor_length,
                        self.service_type,
                        self.service_provider_name_length,
                        self.service_provider_name,
                        self.service_name_length,
                        self.service_name)

class EventInfomationTable:
    def __init__(self, packet):
        self.table_id                    = packet[5]                        # 8   uimsbf
        self.section_length              = (((packet[6] & 0x0F) << 8) + packet[7]) # 12
        self.service_id                  = ((packet[8] << 8) + packet[9])   # 16  uimsbf
        self.version_number              = ((packet[10] >> 1) & 0x1F)       # 5   uimsbf
        self.current_next_indicator      = (packet[10] & 0x01)              # 1   bslbf
        self.section_number              = packet[11]                       # 8   uimsbf
        self.last_section_number         = packet[12]                       # 8   uimsbf
        self.transport_stream_id         = ((packet[13] << 8) + packet[14]) # 16  uimsbf
        self.original_network_id         = ((packet[15] << 8) + packet[16]) # 16  uimsbf
        self.segment_last_section_number = packet[17]                       # 8   uimsbf
        self.last_table_id               = packet[18]                       # 8   uimsbf
        self.events = []
        crc32mpeg(packet[5:self.section_length + 8], self.table_id, self.section_length)
    def __str__(self):
        return (
        ' table_id=%04X\n'
        ' section_length=%i\n'
        ' service_id=%i\n'
        ' version_number=%i\n'
        ' current_next_indicator=%i\n'
        ' section_number=%i\n'
        ' last_section_number=%i\n'
        ' transport_stream_id=%i\n'
        ' original_network_id=%i\n'
        ' segment_last_section_number=%i\n'
        ' last_table_id=%04X\n') % (
            self.table_id,
            self.section_length,
            self.service_id,
            self.version_number,
            self.current_next_indicator,
            self.section_number,
            self.last_section_number,
            self.transport_stream_id,
            self.original_network_id,
            self.segment_last_section_number,
            self.last_table_id)

class Event:
    def __init__(self, transport_stream_id, service_id, event_id, start_time, duration,
            running_status, free_CA_mode, descriptors_loop_length):
        self.transport_stream_id = transport_stream_id
        self.service_id = service_id
        self.event_id = event_id
        self.start_time = start_time
        self.duration = duration
        self.running_status = running_status
        self.free_CA_mode = free_CA_mode
        self.descriptors_loop_length = descriptors_loop_length
        self.descriptors = []
        self.desc_short = None
        self.desc_content = None
        self.desc_extend = None
    def __str__(self):
        return (
        '  service_id=%i\n'
        '  event_id=%04X\n'
        '  start_time=%s\n'
        '  duration=%s\n'
        '  running_status=%02X\n'
        '  free_CA_mode=%i\n'
        '  descriptors_loop_length=%i\n') % (
            self.event_id,
            self.start_time,
            self.duration,
            self.running_status,
            self.free_CA_mode,
            self.descriptors_loop_length)

class ContentDescriptor:
    def __init__(self, descriptor_tag, descriptor_length, content_type_array):
        self.descriptor_tag = descriptor_tag
        self.descriptor_length = descriptor_length
        self.content_type_array = content_type_array
    def __str__(self):
        return (
        '   descriptor_tag=0x%02X\n'
        '   descriptor_length=%i\n') % (
                self.descriptor_tag,
                self.descriptor_length)

class ContentType:
    def __init__(self, content_nibble_level_1, content_nibble_level_2,
            user_nibble_1, user_nibble_2):
        self.content_nibble_level_1 = content_nibble_level_1
        self.content_nibble_level_2 = content_nibble_level_2
        self.user_nibble_1 = user_nibble_1
        self.user_nibble_2 = user_nibble_2
    def __str__(self):
        return (
        '    content_nibble_level_1=%s\n'
        '    content_nibble_level_2=%s\n'
        '    user_nibble_1=0x%X\n'
        '    user_nibble_2=0x%X\n') % (
                self.content_nibble_level_1,
                self.content_nibble_level_2,
                self.user_nibble_1,
                self.user_nibble_2)

class ShortEventDescriptor:
    def __init__(self, descriptor_tag, descriptor_length,
            ISO_639_language_code, event_name_length,
            event_name, text_length, text):
        self.descriptor_tag = descriptor_tag
        self.descriptor_length = descriptor_length
        self.ISO_639_language_code = ISO_639_language_code
        self.event_name_length = event_name_length
        self.event_name = event_name
        self.text_length = text_length
        self.text = text
    def __str__(self):
        return (
        '   descriptor_tag=0x%02X\n'
        '   descriptor_length=%i\n'
        '   ISO_639_language_code=%s\n'
        '   event_name_length=%i\n'
        '   event_name=%s\n'
        '   text_length=%i\n'
        '   text=%s\n') % (
                self.descriptor_tag,
                self.descriptor_length,
                self.ISO_639_language_code,
                self.event_name_length,
                self.event_name,
                self.text_length,
                self.text)

class ExtendedEventDescriptor:
    def __init__(self, descriptor_tag, descriptor_length, descriptor_number,
            last_descriptor_number, ISO_639_language_code, length_of_items,
            items, text_length, text):
        self.descriptor_tag = descriptor_tag
        self.descriptor_length = descriptor_length
        self.descriptor_number = descriptor_number
        self.last_descriptor_number = last_descriptor_number
        self.ISO_639_language_code = ISO_639_language_code
        self.length_of_items = length_of_items
        self.items = items
        self.text_length = text_length
        self.text = text
    def __str__(self):
        return (
        '   descriptor_tag=%i\n'
        '   descriptor_length=%i\n'
        '   descriptor_number=%i\n'
        '   last_descriptor_number=%i\n'
        '   ISO_639_language_code=%s\n'
        '   text_length=%i\n'
        '   text=%s\n') % (
                self.descriptor_tag,
                self.descriptor_length,
                self.descriptor_number,
                self.last_descriptor_number,
                self.ISO_639_language_code,
                self.text_length,
                self.text)

class Item:
    def __init__(self, item_description_length, item_description,
            item_length, item):
        self.item_description_length = item_description_length
        self.item_description = item_description
        self.item_length = item_length
        self.item = item
    def __str__(self):
        return (
        '    item_description_length=%i\n'
        '    item_description=%s\n'
        '    item_length=%i\n'
        '    item=%s\n') % (
                self.item_description_length,
                self.item_description,
                self.item_length,
                self.item)

class CRC32MpegError(Exception):
    pass

def crc32mpeg(data, table_id, section_length, crc=0xffffffff):
    for d in data:
        idx = (((crc >> 24) ^ d) & 0xff)
        crc = ((CRC_32_MPEG[idx] ^ (crc << 8)) & 0xffffffff)
    if (crc & 0xffffffff) != 0x0:
        raise CRC32MpegError('table_id=0x%X section_length=%i' % (table_id, section_length))
