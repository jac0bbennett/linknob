#!/usr/bin/env python

# Copyright Jacob Bennett 10/4/16

from flask import render_template, request, session, flash, redirect, url_for
from config import app, db, pepper, bsalt
from Models.models import User, Invite
from utils import codegen
from datetime import datetime
from hashlib import md5
import bcrypt, re, requests

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    title = 'Sign In'
    if request.method == 'GET':
        # Return the signin page
        return render_template('signin.html', title=title)
    elif request.method == 'POST':
        pseudo = request.form['pseudonym']
        formkey = request.form['key']
        user = User.query.filter_by(pseudo=pseudo.lower()).first()
        if user is not None:
            formkey = formkey.encode('utf-8')
            theemail = user.email.encode('utf-8')
            pepperkey = pepper.encode('utf-8')
            formkey = md5(theemail + formkey + pepperkey).hexdigest() # Encrypt the key in form for checking
            key = user.key
            bcryptedkey = bcrypt.hashpw(formkey.encode('utf-8'), bsalt).decode('utf-8')
        elif user is None:
            flash('Pseudonym or Key is incorrect!') # Access denied
            return render_template('signin.html', title=title)
        if user is not None and bcryptedkey == key: # Check the encrypted form key to the user's db key
            if user.confirm != 0 and user.confirm != '0': # Check if user has verified their email
                flash('Please Confirm your Email') # Access denied
                return render_template('signin.html', title=title)
            else:
                # Set all the session variables for the user
                session['user'] = user.pseudo
                session['userid'] = user.id
                session['rank'] = user.rank
                session['name'] = user.name
                session['points'] = int(user.points)
                return redirect(url_for('main'))
        flash('Pseudonym or Key is incorrect!') # Access denied
        return render_template('signin.html', title=title)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    title = 'Sign Up'
    if request.method == 'GET':
        invitecode = request.args.get('code') # Get URL's invite code
        if invitecode == None:
            invitecode = ''
        # Put invite code into form
        return render_template('signup.html', title=title, invitecode=invitecode)
    elif request.method == 'POST':
        invitecode = request.form['invitecode']
        if invitecode is not None:
            invitecode = ''
        pseudo = request.form['pseudonym']
        pseudo = pseudo.lower()
        if re.match('^[a-z0-9_.-]+$', pseudo): # Check for unallowed characters
            key = request.form['key']
            email = request.form['email']
            name = request.form['fullname']
            invitecode = request.form['invitecode']
            if len(pseudo) < 3: # Pseudonym can't be less than 3 characters
                flash('Pseudonym must be at least 3 characters!')
                return render_template('signup.html', title=title, invitecode=invitecode)
            if len(key) < 6: # Key can't be less than 6
                flash('Key needs to be at least 6 characters!')
                return render_template('signup.html', title=title, invitecode=invitecode)
            # Validate the invite code
            invitecheck = Invite.query.filter_by(code=invitecode).first()
            if invitecheck == None or invitecheck.activated == 1:
                flash('Invalid Invite Code! If you do not have one, get one from someone who has an account.')
                return render_template('signup.html', title=title)
            elif invitecheck != None:
                saltkey = email.encode('utf-8')
                key = key.encode('utf-8')
                pepperkey = pepper.encode('utf-8')
                key = md5(saltkey + key + pepperkey).hexdigest()
                key = bcrypt.hashpw(key.encode('utf-8'), bsalt).decode('utf-8')
                confirmcode = codegen(21) # Generate a confirm code for confirming email
                user = User(pseudo, key, email, None, name, None, None, datetime.now(), None, confirmcode, datetime.now(), None)
                if not (User.query.filter_by(pseudo=pseudo).first() or User.query.filter_by(email=email).first()):
                    # Add user to DB
                    db.session.add(user)
                    db.session.commit()
                    # Set invite to Used
                    invitecheck.activated = 1
                    invitecheck.userid = User.query.filter_by(pseudo=pseudo).first().id
                    db.session.commit()
                    # Send confirmation Email
                    requests.post(
                        "https://api.mailgun.net/v3/linknob.com/messages",
                        auth=("api", "key-a71d55fb1c8464d60eb06291982a0eb8"),
                        data={"from": "Linknob <noreply@linknob.com>",
                              "to": [email],
                              "subject": "Hello, " + name,
                              "html": '<html><h1>Thanks for Joining Linknob</h1><h3>To confirm your email, click the button below. If you did not signup for an account, ignore this email.<br><br><a href="https://www.linknob.com/i/confirm/' + pseudo.lower() + '/confirm/' + confirmcode +'" style="text-decoration:none;background: #2E7D32;border: none;color: #fff;font-family: Arial;font-size: 11pt;border-radius: 2px;-webkit-transition: 300ms ease;transition: 300ms ease;padding: 5px;outline: none;cursor: pointer;box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);">Confirm</a></html>'})
                    flash('To Sign in, confirm your email. One was just sent to you.')
                    return redirect(url_for('signin'))
                else: # Probably entered used pseudonym or email
                    flash('Pseudonym or email may have already been used!')
                    return render_template('signup.html', title=title)
                return render_template('signup.html', title=title)
        else:
            flash('Some characters in pseudonym not allowed! Allowed(a-z; 0-9; _)')
            return render_template('signup.html', title=title)


# Clear session
@app.route('/i/signout')
def signout():
    session.clear()
    db.session.flush()
    db.session.close()
    return redirect(url_for('signoutpage'))
