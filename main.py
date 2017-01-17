#!/usr/bin/env python

# Copyright Jacob Bennett 12/8/16 bV1.0.4.5
# Status: Pre-Beta Stable

# Import all the things
from flask import render_template, session, request
from math import ceil
from datetime import timedelta, datetime
import importlib
from utils import codegen, Pagination, colorgen, escapeit, loadmsgs
from Routes import admin, api, links, misc, pages, search, signing, user
import filters
from Models.models import User, Page
from config import app, db
from Routes import maintenance

reqstart = None

@app.before_request
def before_request():
    abort(404)
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=5)
    importlib.reload(maintenance)
    if maintenance.status and request.path != '/i/maintenance/on' and request.path != '/i/maintenance/off':
        return render_template('maintenance.html')
    else:
        #global reqstart
        #reqstart = datetime.now()
        if 'user' in session:
            try:
                session['points'] = int(User.query.filter_by(id=session['userid']).first().points)
            except AttributeError:
                session['points'] = '50'
            alert = Page.query.filter_by(active=1).first()
            if alert and ('alertclosed' not in session or session['alertclosed'] != alert.header):
                session['alert'] = alert.header
                session['alerturl'] = alert.url

@app.after_request
def after_request(response):
    '''
    importlib.reload(maintenance)
    if not maintenance.status:
        global reqstart
        diff = (datetime.now() - reqstart).microseconds
        reqtime = round(diff / 1000000, 2)
        print(reqtime)
    '''
    response.headers['Last-Modified'] = datetime.now()
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


@app.teardown_request
def teardown_request(exception):
    db.session.close()

# Redirect Errors to error page masterpieces
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def accessdenied(e):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internalerror(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
