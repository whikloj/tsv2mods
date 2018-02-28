#!/usr/bin/env python3
# encoding: utf-8
"""
TSV to MODS converter

Created by Jared Whiklo on 2016-05-04. (Luke, I am your father)
Copyright (c) 2016 University of Manitoba Libraries. All rights reserved.

This tool works on a tab-delimited file where the first row is mods:element definitions.

Column 1 = the output filename + '.mods'

Other columns beginning with / are expected to be mods elements prefixed with mods:.

Simple examples are:

   /mods:name/mods:namePart
   /mods:physicalDescription/mods:form@type=medium

More complex are:

   /mods:relatedItem@xlink:href=%value%>Libraries Search

If row 1 contains %value% the element value is put there instead of in the text of the element.
If row 1 contains > then it is assumed that the text to the right of the > is added as the element text.

So the above example with an element value of "bob" would create
<mods:mods>
  <mods:relatedItem xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="bob">UM Libraries Search</mods:relatedItem>
</mods:mods>

Rows 2 through whatever hold the element values.

If the element value contains %blank% then the blank element is added, even without --include-empty-tags

"""
import os
import argparse
import codecs
import time
import logging
import logging.config
try:
    import lxml.etree as ET
except ImportError:
    import xml.etree.ElementTree as ET

logger = None
data_mapping = None
namespaces = {
    'mods': 'http://www.loc.gov/mods/v3',
    'xlink': 'http://www.w3.org/1999/xlink'
}
include_empty_tags = None
overwrite = False


def load_column_defs(line):
    """Load the MODS Xpaths from the row of data provided

    Positional arguments
    line : The row of tab separated values
    """
    global data_mapping
    columns = line.split('\t')
    # Remove filename element
    columns.pop(0)
    data_mapping = []
    for data in columns:
        if len(data) > 0 and data[0] == '/':
            '''Starts with / so assume a XPath'''
            paths = data.split('/')
            path_arr = []
            for path_part in paths:
                if len(path_part) > 0:
                    path_arr.append(path_part)
            if len(path_arr) > 0:
                data_mapping.append(path_arr)
        else:
            # Its a literal placeholder
            data_mapping.append("placeholder: {}".format(data))


def process_data(line):
    """Process a row of spreadsheet data

    Positional arguments
    line : The row of tab separated values
    """
    # Create a starting mods
    root = ET.Element(add_namespaces('mods:mods'))
    mods = ET.ElementTree(root)
    # Split data on tabs
    data = line.split('\t')
    # Take the filename in column one to make the output file name
    filename = os.path.splitext(os.path.split(data.pop(0))[1])[0] + ".mods"
    if os.path.exists(os.path.join(os.getcwd(), filename)) and not overwrite:
        return
    column_num = 0
    logger.debug("\nCurrent Filename is {}".format(filename))
    try:
        for column in data:
            column = column.strip('"')
            working_map = data_mapping[column_num]
            logger.debug("working_map is {}".format(working_map))
            if working_map[0:11] != "placeholder" and (len(column) > 0 or include_empty_tags):
                element = working_map[len(working_map)-1]
                logger.debug("trying to add {} to parents {}".format(element, working_map))
                the_element = find_element(working_map, mods, column)
                logger.debug("Got back the_element {} adding value {}".format(the_element, column))
            column_num += 1
    except IndexError:
        # No more elements
        logger.debug("No more elements in working maps")
        pass
    mods.write(filename, encoding="utf-8", xml_declaration=True, method='xml')

     
def find_element(element, mods, element_value=None):
    """Find the mods Xpath in the existing document

    Positional arguments
    element : the list of elements to search for
    mods : the ElementTree object
    """
    search_term = '/'.join(make_searchable(element[:]))
    if search_term[0] == '/':
        search_term = search_term[1:]
    logger.debug("Search for {}".format(search_term))
    search = mods.find(search_term, namespaces=namespaces)
    if search is None:
        try:
            logger.debug("Length of element {}".format(len(element)))
            # Toss the last element
            logger.debug("element is {}".format(element))
            this_element = element[-1]
            if len(element[:-1]) > 0:
                logger.debug("element has {} elements".format(len(element[:-1])))
                parent = find_element(element[:-1], mods)
            else:
                logger.debug("There is nothing left, adding to root")
                parent = mods.getroot()
            return add_element(this_element, parent, element_value=element_value)
        except IndexError:
            parent = mods.getroot()
            return add_element(element, parent)
    else:
        return search


def add_element(element_def, parent, element_value=None):
    """Add an element a parent
        
    Arguments:
    element_def : the string of the element to add
    element_value : value to add to the element or None.
    parent : the parent to append this element to.
    """
    attributes = {}
    common_element_value = None
    if element_value is not None:
        element_value = element_value.lstrip(' ').rstrip(' ')
    # If we want to force a blank element.
    if element_value == '%blank%':
        element_value = None
    if element_def.find('>') > -1:
        # We have a common element value, probably using the value in an attribute
        element_def, common_element_value = element_def.split('>')
    if element_def.find("@") > -1:
        element_def, attrib = element_def.split("@")
        key, val = attrib.split("=")
        key = add_namespaces(key)
        val = val.rstrip('"\'').lstrip('"\'')
        if '%value%' in val:
            attributes[key] = element_value
            element_value = None
            if common_element_value is not None:
                element_value = common_element_value
        else:
            attributes[key] = val
    ele = ET.SubElement(parent, add_namespaces(element_def), attributes)
    if element_value is not None:
        ele.text = element_value
    return ele


def make_searchable(terms):
    """Change the element creation string into a XPath searchable one.
    
    Examples:   /foo/bar => /mods:foo/mods:bar
                /foo/bar@kids=2 => /mods:foo/mods:bar[@kids="2"]
    Arguments:
    terms : the list of elements to search for, the element argument from find_element
    """
    try:
        logger.debug("make_searchable: terms is {}".format(terms))
        this_term = terms.pop()
        if this_term.find("@") > -1:
            x, y = this_term.split("@")
            a, b = y.split("=")
            b = b.lstrip('\'"').rstrip('\'"')
            a = add_namespaces(a)
            if '%value%' in b:
                y = "[" + a + "]"
            else:
                y = "[" + a + "=\"" + b + "\"]"
            this_term = add_namespaces(x) + y
        else:
            this_term = add_namespaces(this_term)
        logger.debug("this_term is now {}".format(this_term))
        search_terms = make_searchable(terms)
        search_terms.append(this_term)
        logger.debug("make_searchable: l is {}".format(search_terms))
        return search_terms
    except IndexError:
        return list()


def add_namespaces(object):
    """Adds expanded namespace, assumes mods if not defined"""
    if ':' in object:
        key, element = object.split(':')
        key_namespace = namespaces[key]
        return '{' + key_namespace + '}' + element
    return object


def process_file(filename):
    """Process a spreadsheet"""
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)
    if os.path.exists(filename):
        try:
            with codecs.open(filename, 'r', encoding='utf8') as fp:
                load_column_defs(fp.readline().rstrip("\r\n"))
                try:
                    # Start counter on the next line.
                    line_number = 2
                    for line in fp:
                        logger.debug("Operate on line {}".format(line.rstrip("\r\n")))
                        process_data(line.rstrip("\r\n"))
                        line_number += 1
                except UnicodeDecodeError as e:
                    print("Error decoding character on line {}: {}".format(line_number, str(e)))
        except IOError as e:
            print("Error reading file {} : {}".format(filename, str(e)))


def format_time(seconds):
    """Format seconds"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


def setup_log(level):
    """Setup logging"""
    global logger
    logger = logging.getLogger('tsv2mods')
    logger.propogate = False
    # Logging Level 
    eval('logger.setLevel(logging.{})'.format(level))
    fh = logging.FileHandler(os.path.join(os.getcwd(), 'tsv2mods.log'), 'w', 'utf-8')
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


if __name__ == '__main__':
    start_time = time.perf_counter()
    
    parser = argparse.ArgumentParser(description='Turn a Tab Seperated Value file of MODS data into a bunch of '
                                                 'MODS files.')
    parser.add_argument('files', help="A TSV file to process")
    parser.add_argument('-e', '--include-empty-tags', dest="empty_tags", action='store_true', default=False,
                        help='Include empty XML elements in the output document. Defaults to skip them.')
    parser.add_argument('-d', '--debug', dest="debug_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='ERROR', help='Set logging level, defaults to ERROR.')
    parser.add_argument('-w', '--overwrite', dest="overwrite", action='store_true', default=False,
                        help="Overwrite existing files with the same name, defaults to skipping")
    args = parser.parse_args()
    
    if not args.files[0] == '/':
        # Relative filepath
        args.files = os.path.join(os.getcwd(), args.files)
    
    include_empty_tags = args.empty_tags
    if os.path.isfile(args.files) and os.path.splitext(args.files)[1] == '.tsv':
        overwrite = args.overwrite
        setup_log(args.debug_level)
        process_file(args.files)
    else:
        parser.error("{} could not be resolved to a TSV file".format(args.files))
    
    total_time = time.perf_counter() - start_time
    message = "Finished in {}".format(format_time(total_time))
    logger.info(message)
    print(message)
