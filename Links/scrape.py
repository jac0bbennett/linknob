#!/usr/bin/env python

# Copyright Jacob Bennett 9/22/17
# Status: Stable

import requests, lxml.html, json, re

# Unique user-agent for crawling
headers = {'user-agent': 'Linknob server'}

class scrape_link:
    def __init__(self, url, t):
        linksplit = url.split('/') # Split link up into sections

        try:
            # Tries for meta title first
            self.title = t.xpath('//meta[@property="og:title"]/@content')[0]
        except Exception:
            try:
                # Otherwise gets it from title tag
                self.title = t.xpath('//title/text()')[0]
            except Exception:
                self.title = 'None'
        try:
            # Checks for meta image and retrieves it's URL
            self.image = t.xpath('//meta[@property="og:image"]/@content')[0].split('//')[0]
            # Makes sure it's not just getting blank or protocol
            if self.image == '' or self.image == 'http:' or self.image == 'https:':
                self.image = t.xpath('//meta[@property="og:image"]/@content')[0].split('//')[1]
            try:
                self.image = self.image + '//' + t.xpath('//meta[@property="og:image"]/@content')[0].split('//')[2]
            except IndexError:
                pass
            self.image = re.sub(r':/', r'://', self.image)
        except Exception:
            self.image = 'None'
        try:
            self.description = t.xpath('//meta[@property="og:description"]/@content')[0]
        except Exception:
            self.description = 'None'

        # Check if protocol is http or https
        if url.startswith('http://'):
            proto = 'http://'
        elif url.startswith('https://'):
            proto = 'https://'
        else:
            proto = ''

        try:
            # Initial check for favicon URL
            self.favicon = t.xpath('//link[@rel="icon" or @rel="shortcut icon" or @rel="icon shortcut"]/@href')[0].split('//')[0]
            # Make sure it isn't just getting a protocol
            if self.favicon == '' or self.favicon == 'http:' or self.favicon == 'https:':
                # If it is, get the real URL
                self.favicon = t.xpath('//link[@rel="icon" or @rel="shortcut icon" or @rel="icon shortcut"]/@href')[0].split('//')[1]
            try:
                # If its found it, check if it is a live page
                a = requests.get('http://' + self.favicon, headers=headers)
                if a.status_code != 200:
                    raise Exception
            except Exception:
                try:
                    # If the request fails, try a different approach
                    # See if URL is on same domain
                    a = requests.get('http://' + linksplit[2] + '/' + self.favicon, headers=headers)
                    if a.status_code != 200:
                        self.favicon = 'None'
                    else:
                        self.favicon = linksplit[2] + '/' + self.favicon
                except Exception:
                    self.favicon = 'None'
        except Exception:
            # If it's not found in HTML, check the general "domain.com/favicon.ico"
            try:
                a = requests.get('http://' + linksplit[2] + '/favicon.ico', headers=headers)
                if a.status_code != 200:
                    self.favicon = 'None'
                else:
                    # If the request is successful, it's probably the favicon
                    self.favicon = linksplit[2] + '/favicon.ico'
            except Exception:
                self.favicon = 'None'

        if self.favicon != 'None':
            # Return favicon with protocol
            self.favicon = proto + self.favicon

            # Check to make sure it's an image
            test = requests.get(self.favicon)
            contype = test.headers['Content-Type']
            contype = re.match('image/', contype)
            if not contype:
                self.favicon = 'http://' + linksplit[2] + '/favicon.ico'


# Check for valid linkid
def check_link(link):
    if link.startswith('http://') or link.startswith('https://'):
        if '.' in link and '<' not in link and '>' not in link and ';' not in link:
            return True
        else:
            return False
