#!/usr/bin/env python

# Copyright Jacob Bennett 8/17/16
# Status: Stable

from math import ceil
from datetime import datetime
from Models.models import Link, Chain
import random, string, json, re, cgi, shortuuid

def codegen(size=7, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size)) # Return random letters and numbers for secure code

def colorgen():
    colors = ['#F44336', '#3F51B5', '#009688', '#43A047', '#FF5722', '#607D8B', '#673AB7', '#FFEB3B', '#795548']
    num = random.randint(0, (len(colors) - 1))
    return colors[num]

def escapeit(it):
    replaced = cgi.escape(it)
    return replaced

# NOTE: Check to see if uuid has been used
def genuuid():
    uuid = shortuuid.ShortUUID().random(length=11)
    checklink = Link.query.filter_by(uuid=uuid).first()
    checkchain = Chain.query.filter_by(uuid=uuid).first()
    if checklink or checkchain:
        uuid = shortuuid.ShortUUID().random(length=11)
    return uuid

# Paginate posts (Not my code. Copy and Pasted)
class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


loadmsgs = ["Obey the Dot.", "Don't look directly at the Dot.", "Communicating...", "Gathering Interwebs...",
    "This may or may not work.", "Stand By.", "Stay Tuned.", "Inserting fire mixtape...",
    "Code too Majestic. Normalizing Code...", "Importing Google...", "Waking Up Monkey Slaves...", "Fixing Broken Links...",
    "Request may or may not be too complicated.", "Writing new loading message.", "Processing Request at speed of light...",
    "Put here so you don't get bored.", "Composing Musical Masterpiece...", "Our Developers are enjoying some Cookies.",
    "Grating Cheese...", "Please Don't Drink and Drive.", "Quit Smoking", "Enhancing Algorithms...",
    "Never, never, never give up. -Winston Churchill", "Ball is Life.", "Recalculating...", "Beaming up Scotty...",
    "Sorry, this lever always gets stuck.", "Ohmmmmmmmm", "The Server is digesting data...", "This message was typed just now.", "Getting back to work..."]
