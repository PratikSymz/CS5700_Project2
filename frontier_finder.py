#!/usr/bin/env python3

from html.parser import HTMLParser

""" Helper class inheriting and implementing the HTMLParser library methods 
    1. Parses the provided raw HTML data for 'a' and 'h2' tags for 'href' links to crawl 
        and the 'secret_flags' to detect and save, respectively
        
    2. handle_starttag(self, tag, attrs): Detect start tags and provide tag and attribute information for the corresponding tag
        In case 'a' tag is detected, it checks for the 'href' attribute and for its corresponding link value it:
            a. Checks if the link has already been crawled, if not, add it to the crawled list
            b. Checks if the link has already been added to the queue, if not, add it to the queue to crawl

    3. handle_data(self, data): Handle the 'data' part of the HTML tags.
        In this case, we keep a flag for the current tag and its corresponding attributes and check 
        if the current tag is 'h2', meaning we have found the 'secret_flag' and save these flags in a list
"""
class FrontierFinder(HTMLParser):
    frontier_queue = []
    frontier_crawled = set()
    
    flags_secret = []
    current_tag = ''
    attributes = ''

    def __init__(self):
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        FrontierFinder.current_tag = tag
        FrontierFinder.attributes = attrs

        if (tag == 'a'):
            for attr in attrs:
                if (attr[0] == 'href'):
                    if (not(attr[1] in FrontierFinder.frontier_crawled) and not(attr[1] in (FrontierFinder.frontier_queue))):
                        FrontierFinder.frontier_queue.append(attr[1])
    
    def handle_data(self, data):
        if (FrontierFinder.current_tag == 'h2'):
            for attr in FrontierFinder.attributes:
                if (attr[0] == 'class' and attr[1] == 'secret_flag'):
                    if (data != '\n    '):
                        FrontierFinder.flags_secret.append(data.split(':')[1].strip())

    def error(self, message):
        pass
