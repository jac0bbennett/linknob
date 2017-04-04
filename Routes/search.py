#!/usr/bin/env python

# Copyright Jacob Bennett 4/4/16

from flask import render_template, request, session, flash
from sqlalchemy import or_, func
from config import app, db, PER_PAGE
from Models.models import User, Chain
from Links.search import search_query
from misc import EasterEgg

@app.route('/search')
def search():
    if 'user' in session:
        sessuserid = session['userid']
    else:
        sessuserid = 0

    # Get user's query
    search = request.args.get('q')

    # Check for easter egg
    egg = EasterEgg().runEgg(search)

    searches = search.split(' ') # Split query up into individual words
    searches = [x.lower() for x in searches] # Make all words lowercase
    title = 'Linknob | Search | ' + search
    # Some beast code to get link posts and user accounts similar to query
    accounts = search_query.getusers(search, 3)
    chains = search_query.getchains(search, 3)
    links = search_query.getlinks(search, 20)
    count = len(links)
    return render_template('search.html', title=title, links=links, search=search, accounts=accounts, chains=chains, count=count, egg=egg)
