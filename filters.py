#!/usr/bin/env python

# Copyright Jacob Bennett 11/15/16

from datetime import datetime, timedelta, date
from flask import session, Markup
import Routes.links, Routes.user, Routes.signing
from Models.models import User, Link, Point, Chain
from config import app, db
import urllib.parse as urlparse
import re

# Make the times universal and human friendly
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%b. %d at %I:%M %p'):
    now = datetime.now()
    dif = now - value
    daysdif = (datetime.date(now) - datetime.date(value)).days
    seconddif = dif.total_seconds()
    if dif.days < 1:
        if seconddif <= 10:
            format = 'moments ago'
        if seconddif > 10:
            format = str(int(seconddif)) + ' seconds ago'
        if seconddif > 60:
            format = "1 minute ago"
        if seconddif > 120:
            format = str(int(seconddif / 60)) + " minutes ago"
        if seconddif > 3600:
            format = "1 hour ago"
        if seconddif > 7200:
            format = str(int(seconddif / 3600)) + " hours ago"
    elif daysdif < 2:
        format = 'Yesterday'
    elif daysdif == 2:
        format = str(daysdif) + ' days ago'
    elif daysdif > 2 and daysdif < 30:
        format = str(daysdif) + ' days ago'
    elif daysdif >= 30 and daysdif < 60:
        format = '1 month ago'
    elif daysdif >= 60 and daysdif < 365:
        format = str(daysdif//30) + ' months ago'
    elif daysdif >= 365:
        format = '%B %d, %Y'
    else:
        format = '%b. %d'
    return value.strftime(format)

# Return time in MTN time instead of "... ago"
@app.template_filter('absolutetime')
def absolutetime(value, format='%b. %d at %I:%M %p'):
    format = '%B %d, %Y'
    return value.strftime(format)

# Keep urls from staying on domain
@app.template_filter('urlstrain')
def urlstrain(text):
    if text.startswith('http://') or text.startswith('https://'):
        return text
    else:
        return '//' + text

# Change hashtags to search links
@app.template_filter('hashtag')
def hashtag(text):
    replaced = re.sub(r'#([a-zA-Z0-9_]+)', r'<a class="hashtag" href="/search?q=%23\1">#\1</a>', text)
    return Markup(replaced)

# Get domain of link
@app.template_filter('baseurl')
def baseurl(text):
    replaced = text.split('/')[2]
    if replaced.startswith('www.'):
        replaced = replaced.split('www.')[1]
    return Markup(replaced)

# Strip special characters from image URLs going to API
@app.template_filter('safeurl')
def safeurl(text):
    if text.startswith('http://') or text.startswith('https://'):
        replaced = text
    else:
        replaced = 'http://' + text
    replaced = urlparse.quote_plus(replaced)
    return Markup(replaced)

# Change userid in template to pseudonym
@app.template_filter('userid')
def getuserid(id):
    pseudo = User.query.filter_by(id=id).first()
    if pseudo:
        return pseudo.pseudo
    else:
        return '[Deleted]'

# Change linkid in template to link
@app.template_filter('linkid')
def getlinkid(id):
    link = Link.query.filter_by(id=id).first()
    if link:
        if link.title:
            return link.title
        else:
            return link.link
    else:
        return '[Deleted]'

# Change chainid in template to chain
@app.template_filter('chainid')
def getchainid(id):
    chain = Chain.query.filter_by(id=id).first()
    if chain:
        return chain.title

# Change chainid in template to chain
@app.template_filter('chainuuid')
def getchainuuid(id):
    chain = Chain.query.filter_by(id=id).first()
    if chain:
        return chain.uuid

# Change linkid in template to linkuuid
@app.template_filter('linkuuid')
def getlinkuuid(id):
    link = Link.query.filter_by(id=id).first()
    if link:
        return link.uuid
    else:
        return '[Deleted]'

# Convert float to integer
@app.template_filter('conInt')
def converttoint(num):
    try:
        return int(num)
    except NameError:
        return num
