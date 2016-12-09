#!/usr/bin/env python

# Copyright Jacob Bennett 11/15/16

from flask import render_template, request, session, flash, redirect, url_for, abort, jsonify
from sqlalchemy import Date, cast, func, or_
from Links.trending import trend
from Links.score import score
from config import app, db, PER_PAGE
from Models.models import User, Link, ReferenceLink, Point, Monthupdate, Chain, Chainlink, Comment
from utils import Pagination, colorgen, escapeit
from datetime import datetime, timedelta, date
import re

@app.route('/')
def main():
    # If the user is signed in redirect them to their path, otherwise send to homepage
    if 'user' in session:
        return redirect(url_for('path'))
    else:
        title = 'Linknob'
        toplinks = Link.query.join(Point, (Point.link == Link.id)).group_by(Link.id).filter((Link.visibility == 1) & (Link.points > 0) & (Link.age >= 60)).order_by((score(Link.points, Link.time, func.count(Point.id))).desc()).limit(2)
        return render_template('homepage.html', title=title, toplinks=toplinks)


@app.route('/i/<catg>')
def new(catg):
    PER_PAGE = 20
    try:
        page = int(request.args.get('page'))
    except TypeError:
        page = 1

    if catg == 'new':
        title = 'Linknob'
        # Check if time for monthly point bump
        lastupdate = Monthupdate.query.order_by(Monthupdate.time.desc()).first()
        timenow = datetime.now()
        daysdif = (datetime.date(timenow) - datetime.date(lastupdate.time)).days
        if daysdif >= 30:
            allusers = User.query.all()
            users = User.query.count()
            links = Link.query.count()
            newupdate = Monthupdate(users, links, timenow)
            db.session.add(newupdate)
            for user in allusers:
                # Give all the users 10 more points
                user.points += 10
            db.session.commit()
    elif catg == 'top':
        title = 'Linknob | Top'
    elif catg == 'scored':
        title = 'Linknob | Scored (alpha)'
    else:
        abort(404)


    # Query links and paginate them for a max of 200
    linkcount = Link.query.filter(Link.visibility == 1).limit(200).count()

    if request.args.get('after'):
        after = request.args.get('after')
        if catg == 'new':
            links = Link.query.filter((Link.visibility == 1) & (Link.id <= after)).order_by(Link.time.desc()).paginate(page, PER_PAGE, linkcount).items
        elif catg == 'top':
            links = Link.query.filter((Link.visibility == 1) & (Link.points <= after)).order_by(Link.points.desc()).paginate(page, PER_PAGE, linkcount).items
    else:
        if catg == 'new':
            after = Link.query.filter(Link.visibility == 1).order_by(Link.time.desc()).first().id
            links = Link.query.filter(Link.visibility == 1).order_by(Link.time.desc()).paginate(page, PER_PAGE, linkcount).items
        elif catg == 'top':
            after = Link.query.filter(Link.visibility == 1).order_by(Link.points.desc()).first().points
            links = Link.query.filter(Link.visibility == 1).order_by(Link.points.desc()).paginate(page, PER_PAGE, linkcount).items
        elif catg == 'scored':
            # NOTE: change name
            after = None
            PER_PAGE = 50
            linkcount = Link.query.filter(Link.visibility == 1).limit(50).count()
            links = Link.query.join(Point, (Point.link == Link.id)).group_by(Link.id).filter((Link.visibility == 1) & (Link.points > 0) & (Link.age >= 60)).order_by((score(Link.points, Link.time, func.count(Point.id))).desc()).limit(50)
    pagination = Pagination(page, PER_PAGE, linkcount)
    return render_template('linknob.html', title=title, links=links, catg=catg, pagination=pagination, catgpage='global', after=after, trendingurls=trend.urls())


@app.route('/i/path')
def path():
    PER_PAGE = 20
    if 'user' in session:
        try:
            page = int(request.args.get('page'))
        except TypeError:
            page = 1

        catg = request.args.get('catg')
        if not catg:
            catg = 'new'

        if catg == 'new':
            title = 'Linknob | Path'
        elif catg == 'top':
            title = 'Linknob | Path | Top'
        elif catg == 'scored':
            title = 'Linknob | Path | Scored (alpha)'
        else:
            abort(404)


        # Query links and paginate them for a max of 200 in their Path
        linkcount = User.followed_posts(session['userid']).limit(200).count()

        if request.args.get('after'):
            after = request.args.get('after')
            if catg == 'new':
                links = User.followed_posts(session['userid']).filter((Link.id <= after)).paginate(page, PER_PAGE, linkcount).items
            elif catg == 'top':
                links = User.followed_posts_top(session['userid']).filter((Link.points <= after)).paginate(page, PER_PAGE, linkcount).items
        else:
            if catg == 'new':
                after = User.followed_posts(session['userid']).first()
                if after:
                    after = after.id
                links = User.followed_posts(session['userid']).paginate(page, PER_PAGE, linkcount).items
            elif catg == 'top':
                after = User.followed_posts_top(session['userid']).first()
                if after:
                    after = after.points
                links = User.followed_posts_top(session['userid']).paginate(page, PER_PAGE, linkcount).items
            elif catg == 'scored':
                abort(404)
                after = None
                PER_PAGE = 50
                linkcount = User.followed_posts(session['userid']).limit(50).count()
                links = User.followed_posts_scored(session['userid']).limit(50)
        pagination = Pagination(page, PER_PAGE, linkcount)
        return render_template('path.html', title=title, links=links, catg=catg, pagination=pagination, catgpage='path', after=after)
    else:
        return redirect(url_for('signin'))

# Single link view
@app.route('/link/<linkid>')
def singlelink(linkid):
    link = Link.query.filter_by(uuid=linkid).first()
    if link:
        color = colorgen() # Random color for imageless background
        if 'user' in session:
            point = Point.query.filter((Point.link == link.id) & (Point.userid == session['userid'])).first()
        else:
            point = None
        if not link.title:
            linktitle = link.link
        else:
            linktitle = link.title
        title = 'Linknob | Link | ' + linktitle
        user = User.query.filter_by(id=link.userid).first()
        points = Point.query.filter_by(link=link.id).order_by(Point.time.desc()).limit(10)
        reflinks = ReferenceLink.query.filter_by(linkid=link.id).all()
        chainlist = []
        chainlinks = Chainlink.query.filter_by(link=link.id).all()
        for i in chainlinks:
            chainlist.append(i.chain)
        if 'user' in session:
            sessuserid = session['userid']
        else:
            sessuserid = 0
        if chainlist:
            chains = Chain.query.filter((or_(Chain.visibility == 1, Chain.userid == sessuserid)) & (or_(*[Chain.id == chain for chain in chainlist]))).limit(5)
        else:
            chains = None
        comments = Comment.query.filter((Comment.link==link.id) & (Comment.chain==0)).order_by(Comment.time.desc()).limit(25)
        if chains is None or chains.first() is None:
            chains = None
        return render_template('lnc.html', title=title, user=user, link=link, point=point, points=points, reflinks=reflinks, color=color, chains=chains, comments=comments)
    else:
        abort(404)

@app.route('/i/chains')
def globalchains():
    title = 'Chains | Linknob'
    catgpage = 'chains'
    chains = Chain.query.filter_by(visibility=1).order_by(Chain.title).limit(200)
    try:
        page = int(request.args.get('page'))
    except TypeError:
        page = 1

    chaincount = chains.count()
    if request.args.get('after'):
        after = request.args.get('after')
        chains = Chain.query.filter_by(visibility=1).order_by(Chain.title).paginate(page, PER_PAGE, chaincount).items
    else:
        after = Chain.query.filter_by(visibility=1).order_by(Chain.title).first()
        if after:
            after = after.id
        chains = Chain.query.filter_by(visibility=1).order_by(Chain.title).paginate(page, PER_PAGE, chaincount).items
    pagination = Pagination(page, PER_PAGE, chaincount)
    return render_template('chains.html', title=title, chains=chains, catgpage=catgpage, pagination=pagination, after=after)


@app.route('/c/<chainuuid>')
def viewchain(chainuuid):
    PER_PAGE = 20
    chain = Chain.query.filter_by(uuid=chainuuid).first()
    if chain:
        catg = request.args.get('catg')
        if not catg:
            catg = 'new'

        if catg == 'new':
            title = chain.title + ' | Linknob'
        elif catg == 'scored':
            title = chain.title + ' | Linknob | Scored (alpha)'
        else:
            abort(404)

        try:
            page = int(request.args.get('page'))
        except TypeError:
            page = 1

        linkcount = Link.query.join(Chainlink, (Chainlink.link == Link.id)).filter(Chainlink.chain==chain.id).limit(200).count()
        if request.args.get('after'):
            after = request.args.get('after')
            links = Link.query.join(Chainlink, (Chainlink.link == Link.id)).filter((Chainlink.chain==chain.id) and (Chainlink.id <= after)).order_by(Chainlink.added.desc()).paginate(page, PER_PAGE, linkcount).items
        else:
            if catg == 'new':
                after = Link.query.join(Chainlink, (Chainlink.link == Link.id)).filter(Chainlink.chain==chain.id).order_by(Chainlink.added.desc()).first()
                if after:
                    after = after.id
                links = Link.query.join(Chainlink, (Chainlink.link == Link.id)).filter(Chainlink.chain==chain.id).order_by(Chainlink.added.desc()).paginate(page, PER_PAGE, linkcount).items
            elif catg == 'scored':
                after = None
                PER_PAGE = 50
                linkcount = Link.query.limit(50).count()
                links = Link.query.join(Point, (Point.link == Link.id)).group_by(Link.id).filter((Link.points > 0) & (Link.age >= 60)).join(Chainlink, (Chainlink.link == Link.id)).filter(Chainlink.chain==chain.id).order_by((score(Link.points, Link.time, func.count(Point.id))).desc()).limit(50)
        pagination = Pagination(page, PER_PAGE, linkcount)
        return render_template('chain.html', title=title, chain=chain, links=links, pagination=pagination, after=after, catg=catg)
    else:
        abort(404)

@app.route('/c/<chainuuid>/<linkuuid>')
def singlelinkinchain(chainuuid, linkuuid):
    chain = Chain.query.filter_by(uuid=chainuuid).first()
    link = Link.query.filter_by(uuid=linkuuid).first()
    if chain:
        linkchain = Chainlink.query.filter((Chainlink.chain==chain.id) & (Chainlink.link==link.id)).first()
    else:
        linkchain = None
    if linkchain:
        color = colorgen() # Random color for imageless background
        if 'user' in session:
            point = Point.query.filter((Point.link == link.id) & (Point.userid == session['userid'])).first()
        else:
            point = None
        if not link.title:
            linktitle = link.link
        else:
            linktitle = link.title
        title = 'Linknob | Link | ' + linktitle
        user = User.query.filter_by(id=link.userid).first()
        points = Point.query.filter_by(link=link.id).order_by(Point.time.desc()).limit(10)
        reflinks = ReferenceLink.query.filter_by(linkid=link.id).all()
        comments = Comment.query.filter((Comment.link==link.id) & (Comment.chain==chain.id)).order_by(Comment.time.desc()).limit(25)
        return render_template('chainlink.html', title=title, user=user, link=link, point=point, points=points, reflinks=reflinks, color=color, chain=chain, linkchain=linkchain, comments=comments)
    else:
        abort(404)

@app.route('/c/<chainuuid>/settings', methods=['GET', 'POST'])
def chainsettings(chainuuid):
    title = 'Chain | Settings | Linknob'
    chain = Chain.query.filter_by(uuid=chainuuid).first()
    if 'user' in session and (session['userid'] == chain.userid or session['rank'] >= 2) and chain is not None:
        if request.method == 'GET':
            return render_template('chainsettings.html', chain=chain, title=title)
        else:
            chaintitle = request.json['chaintitle'].strip()
            chaindesc = request.json['chaindesc']
            chainvis = request.json['chainvis']
            if chaintitle.isspace():
                return jsonify({ 'error': 'Title cannot be blank!'})
            if re.match("^[a-zA-Z0-9 #_.'-]+$", chaintitle):
                check = Chain.query.filter(func.lower(Chain.title)==func.lower(chaintitle)).first()
                if check == None or (check != None and check.id == chain.id):
                    if len(chaintitle) > 50:
                        return jsonify({ 'error': 'Chain title must be 50 characters or less!'})
                    elif len(chaindesc) > 300:
                        return jsonify({ 'error': 'Chain description must be 300 characters or less!'})
                    else:
                        chain.title = chaintitle
                        chain.description = escapeit(chaindesc)
                        chain.visibility = chainvis
                        db.session.commit()
                        return jsonify()
                else:
                    return jsonify({ 'error': 'There is already a chain with that title!'})
            else:
                return jsonify({ 'error': 'Some characters in chain title not allowed! Allowed(a-z;A-Z;0-9; _)'})
            #flash('<span style="color:#2E7D32;">Saved!</span>')
    else:
        return redirect(url_for('signin'))
