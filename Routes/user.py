#!/usr/bin/env python

# Copyright Jacob Bennett 1/6/16

from flask import render_template, request, session, flash, abort, redirect, url_for
from sqlalchemy import or_, func
from config import app, db, PER_PAGE, pepper, bsalt
from Models.models import User, Link, Follow, Invite, Point, Chain, Comment, FreePoint
from utils import Pagination, escapeit
from datetime import datetime
from hashlib import md5
import bcrypt, re

@app.route('/<pseudo>')
def profile(pseudo):
    user = User.query.filter_by(pseudo=pseudo).first()
    if user:
        try:
            page = int(request.args.get('page'))
        except TypeError:
            page = 1

        catg = request.args.get('catg')
        if not catg:
            catg = 'new'

        if catg == 'new':
            title = pseudo + ' | Linknob'
        elif catg == 'top':
            title = pseudo + ' | Top | Linknob'

        linkcount = Link.query.filter_by(userid=user.id).filter(Link.visibility == 1).limit(200).count()

        if request.args.get('after'):
            after = request.args.get('after')
            if catg == 'new':
                links = Link.query.filter_by(userid=user.id).filter((Link.visibility == 1) & (Link.id <= after)).order_by(Link.time.desc()).paginate(page, PER_PAGE, linkcount).items
            elif catg == 'top':
                links = Link.query.filter_by(userid=user.id).filter((Link.visibility == 1) & (Link.points <= after)).order_by(Link.points.desc()).paginate(page, PER_PAGE, linkcount).items
        else:
            if catg == 'new':
                after = Link.query.filter_by(userid=user.id).filter(Link.visibility == 1).order_by(Link.time.desc()).first()
                if after:
                    after = after.id
                links = Link.query.filter_by(userid=user.id).filter(Link.visibility == 1).order_by(Link.time.desc()).paginate(page, PER_PAGE, linkcount).items
            elif catg == 'top':
                after = Link.query.filter_by(userid=user.id).filter(Link.visibility == 1).order_by(Link.points.desc()).first()
                if after:
                    after = after.points
                links = Link.query.filter_by(userid=user.id).filter(Link.visibility == 1).order_by(Link.points.desc()).paginate(page, PER_PAGE, linkcount).items

        pagination = Pagination(page, PER_PAGE, linkcount)
        return render_template('profile.html', user=user, links=links, title=title, catg=catg, pagination=pagination, after=after)
    else:
        abort(404)


@app.route('/<pseudo>/trailing')
def usertrailing(pseudo):
    title = 'Linknob | Who ' + pseudo + ' is Trailing'
    user = User.query.filter_by(pseudo=pseudo).first()
    if user:
        stats = Follow.query.filter_by(follower=user.id).order_by(Follow.time.desc()).limit(50)
        statname = 'Trailing'
        return render_template('stat.html', stats=stats, user=user, title=title, statname=statname)
    else:
        abort(404)


@app.route('/<pseudo>/trailers')
def usertrailers(pseudo):
    title = 'Linknob | Who trails ' + pseudo
    user = User.query.filter_by(pseudo=pseudo).first()
    if user:
        stats = Follow.query.filter_by(followed=user.id).order_by(Follow.time.desc()).limit(50)
        statname = 'Trailers'
        return render_template('stat.html', stats=stats, user=user, title=title, statname=statname)
    else:
        abort(404)

@app.route('/<pseudo>/chains')
def userchains(pseudo):
    title = 'Linknob | Chains by ' + pseudo
    user = User.query.filter_by(pseudo=pseudo).first()
    if user:
        if 'user' in session and session['userid'] == user.id:
            chains = Chain.query.filter_by(userid=user.id).order_by(Chain.title).limit(50)
        else:
            chains = Chain.query.filter((Chain.visibility == 1)&(Chain.userid==user.id)).order_by(Chain.title).limit(50)
        return render_template('userchains.html', chains=chains, user=user, title=title)
    else:
        abort(404)

@app.route('/i/settings', methods=['GET', 'POST'])
def usersettings():
    title = 'Linknob | Settings'
    user = User.query.filter_by(id=session['userid']).first()
    if user:
        if request.method == 'GET':
            return render_template('settings.html', user=user, title=title)
        else:
            name = request.form['name']
            pseudo = request.form['pseudo']
            email = request.form['email']
            bio = request.form['bio']
            flair = request.form['flair']
            curkey = request.form['curkey']
            newkey = request.form['newkey']
            if curkey:
                formkey = curkey.encode('utf-8')
                theemail = user.email.encode('utf-8')
                pepperkey = pepper.encode('utf-8')
                formkey = md5(theemail + formkey + pepperkey).hexdigest() # Encrypt the key in form for checking
                bcryptedkey = bcrypt.hashpw(formkey.encode('utf-8'), bsalt).decode('utf-8')
                if bcryptedkey == user.key:
                    if name:
                        if len(name) > 24:
                            flash('Name is too long')
                        else:
                            name = escapeit(name)
                            user.name = name
                            session['name'] = name
                    if pseudo:
                        if len(pseudo) < 3:
                            flash('Pseudonym must be at least 3 characters')
                        else:
                            pseudo = pseudo.lower()
                            if not re.match('^[a-z0-9_.-]+$', pseudo): # Check for unallowed characters
                                flash('Some characters in pseudonym not allowed! Allowed(a-z 0-9 ._-)')
                                return render_template('settings.html', title=title, user=user)
                            pseudocheck = User.query.filter_by(pseudo=pseudo).first()
                            if not pseudocheck or pseudocheck.id == session['userid']:
                                user.pseudo = pseudo
                                session['user'] = pseudo
                            else:
                                flash('Pseudonym is not available!')
                    if newkey:
                        if len(newkey) < 6:
                            flash('Key must be at least 6 characters')
                        else:
                            curkey = newkey
                            newkey = newkey.encode('utf-8')
                            theemail = user.email.encode('utf-8')
                            pepperkey = pepper.encode('utf-8')
                            formkey = md5(theemail + newkey + pepperkey).hexdigest() # Encrypt the key in form for checking
                            bcryptedkey = bcrypt.hashpw(formkey.encode('utf-8'), bsalt).decode('utf-8')
                            user.key = bcryptedkey
                    if email:
                        if email != user.email:
                            emailcheck = User.query.filter_by(email=email).first()
                            if not emailcheck or emailcheck.id == session['userid']:
                                user.email = email
                                curkey = curkey.encode('utf-8')
                                theemail = email.encode('utf-8')
                                pepperkey = pepper.encode('utf-8')
                                formkey = md5(theemail + curkey + pepperkey).hexdigest() # Encrypt the key in form for checking
                                bcryptedkey = bcrypt.hashpw(formkey.encode('utf-8'), bsalt).decode('utf-8')
                                user.key = bcryptedkey
                            else:
                                flash('Email is already used by another account!')
                    else:
                        flash('Email cannot be blank!')
                    if bio:
                        bio = escapeit(bio)
                        if len(bio) > 200:
                            flash('Your bio must be less than 200 characters')
                        else:
                            user.bio = bio
                    else:
                        user.bio = ''
                    if flair:
                        flair = escapeit(flair)
                        if len(flair) > 11:
                            flash('Your flair must be less than 12 characters')
                        else:
                            user.flair = flair
                    else:
                        user.flair = 'Cool'
                    db.session.commit()
                    flash('<span style="color:#2E7D32;">Saved!</span>')
                else:
                    flash('Incorrect current key!')
                return render_template('settings.html', title=title, user=user)
            else:
                flash('Please enter your current key to allow changes!')
                return render_template('settings.html', user=user, title=title)
    else:
        return redirect(url_for('signin'))

@app.route('/i/interactions')
def viewinteractions():
    if 'user' in session:
        user = User.query.filter_by(id=session['userid']).first()
        checkinttime = user.checkint
        trailcount = Follow.query.filter_by(followed=session['userid']).filter(Follow.time > checkinttime).count()
        pointcount = Point.query.join(Link, (Point.link == Link.id)).filter(Link.userid == session['userid']).filter(Point.time > checkinttime).order_by(Point.time.desc()).count()
        commentcount = Comment.query.join(Link, (Comment.link == Link.id)).filter((Link.userid == session['userid']) & (Comment.userid != session['userid'] or Comment.userid != 0) & (Comment.time > checkinttime)).order_by(Comment.time.desc()).count()
        lastfreept = FreePoint.query.filter_by(userid=session['userid']).order_by(FreePoint.time.desc()).first()
        if lastfreept:
            freeptcheck = (datetime.now() - lastfreept.time).total_seconds()
            if freeptcheck >= 86400:
                freepts = True
            else:
                freepts = False
        else:
            freepts = True

        user.checkint = datetime.now()
        db.session.commit()
        catg = request.args.get('catg')
        if not catg:
            catg = 'points'
        if catg == 'trails':
            points = None
            comments = None
            trails = Follow.query.filter_by(followed=session['userid']).order_by(Follow.time.desc()).limit(40).all()
        elif catg == 'points':
            trails = None
            comments = None
            points = Point.query.join(Link, (Point.link == Link.id)).filter(Link.userid == session['userid']).order_by(Point.time.desc()).limit(40).all()
        elif catg == 'comments':
            trails = None
            points = None
            comments = Comment.query.join(Link, (Comment.link == Link.id)).filter((Link.userid == session['userid']) & (Comment.userid != session['userid'] or Comment.userid != 0)).order_by(Comment.time.desc()).limit(40).all()
        return render_template('interactions.html', title='Linknob | Interactions', catg=catg, catgpage='interactions', trails=trails, points=points, comments=comments, pointcount=pointcount, trailcount=trailcount, commentcount=commentcount, freepts=freepts)
    return redirect(url_for('signin'))



# Generate invites page
@app.route('/i/invite')
def invitepage():
    title = 'Linknob | Invites'
    if 'user' in session:
        user = User.query.filter_by(id=session['userid']).first()
        if user.rank >= 2 or user.verified == 1:
            # Get all the user's invites already generated
            invites = Invite.query.filter_by(sender=session['userid'])
            remain = 5 - invites.count()
            if session['rank'] == 3:
                remain = '∞'
            invites = invites.order_by(Invite.timegen.desc()).all()
            # Display them
            return render_template('invite.html', title=title, remain=remain, invites=invites)
        else:
            abort(404)
    else:
        return redirect(url_for('signin'))
