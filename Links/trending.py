#!/usr/bin/env python
from sqlalchemy import Date, cast
from collections import Counter
from Models.models import Link
import re

class trend:
    def urls(top=3, count=False):
        urls = ''
        links = Link.query.order_by(Link.time.desc()).limit(50) # Get recent posts
        for link in links:
            url = link.link
            # Get link's base url e.g example.com
            try:
                baseurl = url.split('/')[2]
            except IndexError:
                baseurl = url.split('/')[0]
            # Remove www.
            if baseurl.startswith('www.'):
                baseurl = baseurl.split('www.')[1]
            urls = urls + ' ' + baseurl
        mostcommon = Counter(urls.split()).most_common() # Get most common baseurls
        if count:
            mostcommon = [i for i in mostcommon[:top]] # If count==True, get the number of links with baseurl
        else:
            mostcommon = [i[0] for i in mostcommon[:top]] # If count==False, show just the baseurl
        return mostcommon
