#!/usr/bin/python
# -*- coding: utf-8 -*-
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element
import xml.etree.ElementTree
import xml.dom.minidom
from constant import *

def get_text(text):
    return text.decode('utf-8') if text != None else ""

def create_xml(b_type, channel_id, service, events, filename, pretty_print):


    channel_el_list = create_channel(b_type, channel_id, service)
    programme_el_list = create_programme(channel_id, events)
    attr = {
            'generator-info-name':'epgdump_py',
            'generator-info-url':'mailto:epgdump_py@gmail.com'}
    tv_el = Element('tv', attr)

    for el in channel_el_list:
        tv_el.append(el)
    for el in programme_el_list:
        tv_el.append(el)

    fd = open(filename, 'w')
    if pretty_print:
        xml_str = xml.etree.ElementTree.tostring(tv_el)
        xml_str = xml.dom.minidom.parseString(xml_str).toprettyxml(indent='  ', encoding='utf-8')
        fd.write(xml_str)
    else:
        xml.etree.ElementTree.ElementTree(tv_el).write(fd, 'utf-8', ' ')
    fd.close()

def create_channel(b_type, channel_id, service):
    el_list = []
    for (service_id, service_name) in service.items():
        ch = str(service_id) if channel_id == None else channel_id
        attr = {'id':ch}
        channel_el = Element('channel', attr)
        attr = {'lang':'ja'}

        display_el = Element('display-name', attr)
        display_el.text = get_text(service_name)
        channel_el.append(display_el)

        display_el = Element('display-name', attr)
        display_el.text = ch
        channel_el.append(display_el)

        display_el = Element('display-name', attr)
        display_el.text = ch + ' ' + get_text(service_name)
        channel_el.append(display_el)

        el_list.append(channel_el)

    return el_list

def create_programme(channel_id, events):
    t_format = '%Y%m%d%H%M%S +0900'
    el_list = []
    for event in events:

        ch = str(event.service_id) if channel_id == None else channel_id
        start = event.start_time.strftime(t_format)
        stop = (event.start_time + event.duration).strftime(t_format)
        attr = {'start':start, 'stop':stop, 'channel':ch}
        programme_el = Element('programme', attr)

        attr = {'lang':'ja'}

        title_el = Element('title', attr)
        title_el.text = get_text(event.desc_short.event_name)
        programme_el.append(title_el)

        eed_text = ''
        if event.desc_extend != None:
            for (k,v) in event.desc_extend.items():
                eed_text += '\n' + get_text(k) + '\n' + get_text(v) + '\n'

        desc_el = Element('desc', attr)
        desc_el.text = get_text(event.desc_short.text) + '\n' + eed_text
        programme_el.append(desc_el)

        if event.desc_content != None:
            for ct in event.desc_content.content_type_array:
                category_el_1 = Element('category', attr)
                category_el_1.text = get_text(ct.content_nibble_level_1)
                programme_el.append(category_el_1)
                category_el_2 = Element('category', attr)
                category_el_2.text = get_text(ct.content_nibble_level_2)
                programme_el.append(category_el_2)
                break

        el_list.append(programme_el)

    return el_list
