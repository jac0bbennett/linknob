#!/usr/bin/env python

# Copyright Jacob Bennett 10/2/16

from flask import render_template, request, session, flash, send_file, abort, redirect, url_for
from config import app, db, pepper, bsalt
from Models.models import User, Resetkey
from utils import codegen
from datetime import datetime
from hashlib import md5
import bcrypt, requests

@app.route('/i/resetkey', methods=['GET', 'POST'])
def resetkey():
    title = 'Reset Key'
    if request.args.get('resetcode'):
        if request.method == 'GET':
            return render_template('resetkey.html', title=title)
        else:
            resetcode = request.args.get('resetcode')
            usercheck = Resetkey.query.filter_by(code=resetcode).first()
            if usercheck:
                user = User.query.filter_by(id=usercheck.userid).first()
                key = request.form['key']
                if len(key) < 6: # Key can't be less than 6
                    flash('Key needs to be at least 6 characters!')
                    return render_template('resetkey.html', title=title)
                else:
                    formkey = key.encode('utf-8')
                    theemail = user.email.encode('utf-8')
                    pepperkey = pepper.encode('utf-8')
                    key = md5(theemail + formkey + pepperkey).hexdigest()
                    key = bcrypt.hashpw(key.encode('utf-8'), bsalt).decode('utf-8')
                    user.key = key
                    db.session.delete(usercheck)
                    db.session.commit()
                    flash('Key Reset!')
                    return redirect(url_for('signin'))
            else:
                abort(404)
    else:
        if request.method == 'GET':
            return render_template('resetkeyreq.html', title=title)
        else:
            email = request.form['email']
            user = User.query.filter_by(email=email).first()
            if user:
                resetcheck = Resetkey.query.filter_by(userid=user.id).first()
                if resetcheck:
                    page = {
                        'title': 'Reset link sent',
                        'header': 'Check your email!',
                        'content': 'It appears a request to reset your key as already been received. If the "Reset Key" email does not appear in your inbox, check your spam folder.',
                        'time': None
                    }
                    return render_template('document.html', page=page)
                else:
                    resetcode = codegen(size=21)
                    resetreq = Resetkey(resetcode, user.id)
                    db.session.add(resetreq)
                    db.session.commit()
                    requests.post(
                        "https://api.mailgun.net/v3/linknob.com/messages",
                        auth=("api", "key-a71d55fb1c8464d60eb06291982a0eb8"),
                        data={"from": "Linknob <noreply@linknob.com>",
                              "to": [email],
                              "subject": "Reset Key",
                              "html": '<html><h1>We have received a request to reset your key.</h1><h3>To reset your key, click the button below: <br><br><a href="https://www.linknob.com/i/resetkey?resetcode=' + resetcode +'" style="text-decoration:none;background: #2E7D32;border: none;color: #fff;font-family: Arial;font-size: 11pt;border-radius: 2px;-webkit-transition: 300ms ease;transition: 300ms ease;padding: 5px;outline: none;cursor: pointer;box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);">Reset</a></html>'})
                    page = {
                        'title': 'Reset link sent',
                        'header': 'Check your email!',
                        'content': 'An email has been sent to you with a link to reset your key.',
                        'time': None
                    }
                    return render_template('document.html', page=page)
            else:
                flash('No user is registered with that email!')
                return render_template('resetkeyreq.html', title=title)

# Basic favicon URL
@app.route('/favicon.ico')
def faviconico():
    return send_file('static/images/favicon.ico', mimetype='image/png')
