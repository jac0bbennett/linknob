#!/usr/bin/env python

# Copyright Jacob Bennett 11/14/15
# Status: Beta

from sqlalchemy import or_, func
from flask import session
from Models.models import Link, User, Chain

class search_query():

    def getlinks(search, amt):

        searches = search.split() # Split query up into individual words
        searches = [x.lower() for x in searches] # Make all words lowercase

        # Get user's query
        initquery = Link.query.filter_by(visibility=1).filter(or_(*[(func.lower(Link.title).contains(word) | func.lower(Link.comment).contains(word)) for word in searches])).all()

        if initquery != None:

            results = {}
            for link in initquery:
                count = 0
                for word in searches:
                    if link.title != None and link.title != 'None':
                        count = count + link.title.lower().count(word)
                    if link.comment != None and link.comment != 'None':
                        count = count + link.comment.lower().count(word)
                results[link.id] = count

            resultlist = sorted(results, key=results.get, reverse=True)
            results = Link.query.filter(or_(*[Link.id == res for res in resultlist[:amt]])).all() # Query top 20 links in resultlist
            results = [next(l for l in results if l.id == id) for id in resultlist[:amt]] # Sort the queried links back into correct order

            return results

    def getusers(search, amt):
        searches = search.split() # Split query up into individual words
        searches = [x.lower() for x in searches] # Make all words lowercase
        results = User.query.filter(or_(*[((func.lower(User.pseudo).startswith(word)) | (func.lower(User.name).like(word+'%')) | (func.lower(User.name).like('% '+word+'%')) )for word in searches])).order_by(User.verified.desc(), User.points.desc()).limit(amt)

        return results

    def getchains(search, amt):
        if 'userid' in session:
            sessuserid = session['userid']
        else:
            sessuserid = 0
        searches = search.split() # Split query up into individual words
        searches = [x.lower() for x in searches] # Make all words lowercase
        results = Chain.query.filter((or_(Chain.visibility == 1, Chain.userid == sessuserid)) & (or_(*[((func.lower(Chain.title).startswith(search)) | (func.lower(Chain.title).like(word+'%')) | (func.lower(Chain.title).like('% '+word+'%')))for word in searches]))).limit(amt)

        return results
