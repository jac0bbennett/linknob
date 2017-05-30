#!/usr/bin/env python

# Copyright Jacob Bennett 1/4/16

from flask import render_template, request, session, abort, jsonify
from config import app, db, PER_PAGE
from Models.models import User, Request, Page
from datetime import datetime
import requests

# Static pages in DB
@app.route('/d/<page>')
def pages(page):
    page = Page.query.filter_by(url=page).first()
    if page:
        return render_template('document.html', page=page, title=page.title)
    else:
        abort(404)

# Post Signout page
@app.route('/i/signedout')
def signoutpage():
    # Static page not in DB
    page = {
        'title': 'Signed Out',
        'header': 'You are signed out of Linknob',
        'content': '<img src="https://s3.amazonaws.com/crowdhoster/adblock/uploads/campaigns/facebook_images/000/000/001/original.png?1377044920" width="100" height="100" style="float:right;">Thank You for using the site! <br><br>If you are using an adblocker, please consider adding an exception for this site. The advertisements keep us in business. <br><hr><a class="genlink" href="/signin">Sign In</a>',
        'time': None
    }
    return render_template('document.html', page=page)


@app.route('/i/requestinvite', methods=['GET', 'POST'])
def requestinviteemail():
    if request.method == 'GET':
        return render_template('reqinvite.html', title='Request invite code')
    else:
        email = request.form['email']
        check = Request.query.filter_by(email=email).first()
        usercheck = User.query.filter_by(email=email).first()
        if check is None and usercheck is None: # Check if email has already requested
            req = Request(email, datetime.now(), None)
            db.session.add(req)
            db.session.commit()
            # Send comfort email to user for warm fuzzy feeling inside requests.post("https://api.mailgun.net/v3/linknob.com/messages",auth=("api","key-a71d55fb1c8464d60eb06291982a0eb8"),data={"from":"Linknob <noreply@linknob.com>","to": [email],"subject": "Your request has been received!","html": '<html><h1>Thank You for your interest!</h1><h3>When an invite is available, it will be sent to you!</h3><h4>Follow us on Twitter: <a href="https://twitter.com/thelinknob">@thelinknob</a></html>'})
            # Static 'requested' page not in DB
            page = {
                'title': 'Requested',
                'header': '<span style="color:#2E7D32">Your request has been received!</span>',
                'content': 'Thank You for requesting an invite. When one is ready, it will be sent to you.',
                'time': None
            }
        else:
            page = {
                'title': 'Already Requested',
                'header': '<span style="color:#E6B730">This email has already requested an invite!</span>',
                'content': 'The email that you submitted has already been added to the list of invite requests.',
                'time': None
            }
        return render_template('document.html', page=page)
