#!/usr/bin/env python

# Copyright Jacob Bennett 6/24/17

from flask import render_template, request, session, jsonify, abort, flash, redirect, url_for, send_file
from sqlalchemy import or_, func
from config import app, db, pepper, bsalt
from hashlib import md5
from Models.models import User, Link, ReferenceLink, Point, Invite, Follow, Chain, Chainlink, Monthupdate, Comment, Page, FreePoint, UserApiKey
from Links.score import score
from Links.scrape import scrape_link, check_link
from utils import Pagination, codegen, escapeit, loadmsgs, genuuid, randLowNum
from datetime import datetime, timedelta
from filters import safeurl, datetimeformat, getuserid
import lxml.html, requests, re, random, bcrypt, json

headers = {'user-agent': 'Linknob server'}

# Post a link without Extension API
@app.route('/i/addlnc', methods=['POST'])
def sendpost():
    comment = request.json['comment']
    link = request.json['link'].strip()
    ptname = request.json['ptname'].strip()

    # Validate URL
    if check_link(link):
        pass
    else:
        return jsonify({ 'error': ' Please enter a valid link' })

    # Check for custom point name
    if comment and len(comment) > 300:
        return jsonify({ 'error': ' Comment cannot be more than 300 chars' })

    # Check for custom point name
    if ptname and len(ptname) > 20:
        return jsonify({ 'error': ' Point name cannot be more than 20 chars' })
    if ptname == '':
        ptname = 'Cool' # Default to "Cool"

    # Request and Parse HTML of link
    try:
        t = requests.get(link, headers=headers)
        t = lxml.html.fromstring(t.text)
    except Exception:
        t = ''

    # Scrape the link using /links/scrape.py
    scrapedata = scrape_link(link, t)
    title = scrapedata.title
    image = scrapedata.image
    description = scrapedata.description
    favicon = scrapedata.favicon

    # Post it
    if link == None:
        flash('Please enter a link!')
    else:
        time = datetime.now().strftime('%m-%d-%y %I:%M:%S %p')
        if comment == None:
            newlnc = Link(genuuid(), session['userid'], link, None, time, 0, None, escapeit(title), escapeit(ptname), favicon, image, escapeit(description), 1)
        else:
            newlnc = Link(genuuid(), session['userid'], link, escapeit(comment), time, 0, None, escapeit(title), escapeit(ptname), favicon, image, escapeit(description), 1)
        db.session.add(newlnc)
        db.session.commit()
    return jsonify()

# Post link using the json api
@app.route('/api/addlnc', methods=['POST'])
def apipost():
    comment = request.json['comment']
    link = request.json['link'].strip()
    ptname = request.json['ptname']
    userid = int(request.json['userid'])
    formkey = request.json['apikey']
    if 'vis' in request.json:
        vis = request.json['vis']
    else:
        vis = 1

    user = User.query.filter_by(id=userid).first()

    # Check for user's key saved in extension
    if user is not None:
        apicheck = UserApiKey.query.filter_by(key=formkey).first()
        if apicheck != None and apicheck.userid == userid:
            key = apicheck.key
        else:
            return jsonify({'errors': ' Session expired! Please signout and sign back in.'})
    if key == formkey:
        if ptname == '':
            ptname = 'Cool'
        try:
            t = requests.get(link, headers=headers)
            t = lxml.html.fromstring(t.text)
        except Exception:
            t = ''

        # Validate URL
        if check_link(link):
            pass
        else:
            return jsonify({ 'errors': ' Please enter a valid link' })

        # Check for custom point name
        if ptname and len(ptname) > 20:
            return jsonify({ 'errors': ' Point name cannot be more than 20 chars' })

        # Scrape the link using /links/scrape.py
        scrapedata = scrape_link(link, t)
        title = scrapedata.title
        image = scrapedata.image
        description = scrapedata.description
        favicon = scrapedata.favicon
        if link == None:
            flash('Please enter a link!')
        else:
            time = datetime.now().strftime('%m-%d-%y %I:%M:%S %p')
            uuid = genuuid()
            if comment == None:
                newlnc = Link(uuid, userid, link, None, time, 0, None, escapeit(title), escapeit(ptname), favicon, image, escapeit(description), vis)
            else:
                newlnc = Link(uuid, userid, link, escapeit(comment), time, 0, None, escapeit(title), escapeit(ptname), favicon, image, escapeit(description), vis)
            db.session.add(newlnc)
            db.session.commit()

            postedlnc = Link.query.filter_by(uuid=uuid).first()
            error = None
            if request.json['chain'] and request.json['chain'] != '':
                chaintitles = request.json['chain'].strip().lower().replace(', ', ',').split(',')
                for chaintitle in chaintitles:
                    if not chaintitle.isspace() and chaintitle != '':
                        chain = Chain.query.filter((or_(Chain.visibility == 1, Chain.userid == userid)) & (func.lower(Chain.title)==chaintitle)).first()
                        if chain:
                            if link != None:
                                addlink = Chainlink(userid, postedlnc.id, chain.id, datetime.now())
                                db.session.add(addlink)
                                db.session.commit()
                            else:
                                error = 'That link does not exist!'
                        else:
                            error = 'The chain "'+chaintitle+'" is not real!'
            if not error:
                return jsonify({'status': 'success'})
            else:
                db.session.delete(postedlnc)
                db.session.commit()
                return jsonify({'errors': error})
    else:
        return jsonify({ 'errors': 'Invalid Key'})

# Sign in with api
@app.route('/api/signin', methods=['POST'])
def apisignin():
    pseudo = request.json['pseudo']
    formkey = request.json['key']
    user = User.query.filter_by(pseudo=pseudo).first()
    if user is not None:
        formkey = formkey.encode('utf-8')
        theemail = user.email.encode('utf-8')
        pepperkey = pepper.encode('utf-8')
        formkey = md5(theemail + formkey + pepperkey).hexdigest() # Encrypt the key in form for checking
        formkey = bcrypt.hashpw(formkey.encode('utf-8'), bsalt).decode('utf-8')
        if user.key == formkey:
            pseudo = user.pseudo
            userid = user.id
            apikey = codegen(12)
            newapi = UserApiKey(userid, apikey, datetime.now())
            db.session.add(newapi)
            db.session.commit()
            return jsonify({'apikey': apikey,
                            'pseudonym': pseudo,
                            'userid': userid,
                            'avatar': user.avatar(),
                            'points': int(user.points),
                            })
    return jsonify({'errors': 'Incorrect credentials!'})

@app.route('/api/signout', methods=['POST'])
def apisignout():
    userid = request.json['userid']
    try:
        formkey = request.json['apikey']
    except Exception:
        return jsonify()
    user = User.query.filter_by(id=userid).first()
    apicheck = UserApiKey.query.filter_by(key=formkey).first()
    if user is not None:
        db.session.delete(apicheck)
        db.session.commit()
        return jsonify()
    return jsonify({'errors': 'Unable to logout!'})

@app.route('/api/global/<catg>')
def getglobalpostsapi(catg):
    apikey = request.args.get('apikey')
    apicheck = UserApiKey.query.filter_by(key=apikey).first()

    if apicheck:
        user = User.query.filter_by(id=apicheck.userid).first()
    else:
        return jsonify({'errors': 'Invalid User Api key!'})

    PER_PAGE = 20
    try:
        page = int(request.args.get('page'))
    except TypeError:
        page = 1

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
            after = None
            PER_PAGE = 50
            linkcount = Link.query.filter(Link.visibility == 1).limit(50).count()
            links = Link.query.join(Point, (Point.link == Link.id)).group_by(Link.id).filter((Link.visibility == 1) & (Link.points > 0) & (Link.age >= 60)).order_by((score(Link.points, Link.age, func.count(Point.id))).desc()).limit(50)
    pagination = Pagination(page, PER_PAGE, linkcount)
    jsonposts = {}
    count = 0
    for link in links:
        if link.favicon == 'None':
            favicon = 'https://www.linknob.com/static/images/defaultglobe.ico'
        else:
            favicon = link.favicon

        linkdata = {
            'id': link.id,
            'uuid': link.uuid,
            'userid': link.userid,
            'pseudo': getuserid(link.userid),
            'url': link.link,
            'comment': link.comment,
            'time': link.time,
            'timeAgo': datetimeformat(link.time),
            'points': link.points,
            'title': link.title,
            'favicon': 'https://www.linknob.com/api/getexternalimage?url='+safeurl(favicon),
            'image': link.image,
            'description': link.description,
            'ptname': link.ptname,
            'pointed': link.pointedapi(user.id)
            }
        jsonposts[str(count)] = linkdata
        count += 1
    jsonposts['has_next'] = pagination.has_next
    jsonposts['user'] = {'points': int(user.points)}
    return jsonify(jsonposts)

@app.route('/api/path/<catg>')
def getpathpostsapi(catg):
    apikey = request.args.get('apikey')
    apicheck = UserApiKey.query.filter_by(key=apikey).first()

    if apicheck:
        user = User.query.filter_by(id=apicheck.userid).first()
    else:
        return jsonify({'errors': 'Invalid User Api key!'})

    PER_PAGE = 20
    try:
        page = int(request.args.get('page'))
    except TypeError:
        page = 1

    linkcount = User.followed_posts(user.id).limit(200).count()

    if request.args.get('after'):
        after = request.args.get('after')
        if catg == 'new':
            links = User.followed_posts(user.id).filter((Link.id <= after)).paginate(page, PER_PAGE, linkcount).items
        elif catg == 'top':
            links = User.followed_posts_top(user.id).filter((Link.points <= after)).paginate(page, PER_PAGE, linkcount).items
    else:
        if catg == 'new':
            after = User.followed_posts(user.id).first()
            if after:
                after = after.id
            links = User.followed_posts(user.id).paginate(page, PER_PAGE, linkcount).items
        elif catg == 'top':
            after = User.followed_posts_top(user.id).first()
            if after:
                after = after.points
            links = User.followed_posts_top(user.id).paginate(page, PER_PAGE, linkcount).items
    pagination = Pagination(page, PER_PAGE, linkcount)
    jsonposts = {}
    count = 0
    for link in links:
        if link.favicon == 'None':
            favicon = 'https://www.linknob.com/static/images/defaultglobe.ico'
        else:
            favicon = link.favicon

        linkdata = {
            'id': link.id,
            'uuid': link.uuid,
            'userid': link.userid,
            'pseudo': getuserid(link.userid),
            'url': link.link,
            'comment': link.comment,
            'time': link.time,
            'timeAgo': datetimeformat(link.time),
            'points': link.points,
            'title': link.title,
            'favicon': 'https://www.linknob.com/api/getexternalimage?url='+safeurl(favicon),
            'image': link.image,
            'description': link.description,
            'ptname': link.ptname,
            'pointed': link.pointedapi(user.id)
            }
        jsonposts[str(count)] = linkdata
        count += 1
    jsonposts['has_next'] = pagination.has_next
    jsonposts['user'] = {'points': int(user.points)}
    return jsonify(jsonposts)

@app.route('/api/user/<user>/<catg>')
def getusersposts(user, catg):
    apikey = request.args.get('apikey')
    apikey = UserApiKey.query.filter_by(key=apikey).first()
    apiuser = User.query.filter_by(id=apikey.userid).first()
    user = User.query.filter_by(pseudo=user).first()
    if user:
        try:
            page = int(request.args.get('page'))
        except TypeError:
            page = 1

        PER_PAGE = 20
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
        jsonposts = {}
        count = 0
        for link in links:
            if link.favicon == 'None':
                favicon = 'https://www.linknob.com/static/images/defaultglobe.ico'
            else:
                favicon = link.favicon

            linkdata = {
                'id': link.id,
                'uuid': link.uuid,
                'userid': link.userid,
                'pseudo': getuserid(link.userid),
                'url': link.link,
                'comment': link.comment,
                'time': link.time,
                'timeAgo': datetimeformat(link.time),
                'points': link.points,
                'title': link.title,
                'favicon': 'https://www.linknob.com/api/getexternalimage?url='+safeurl(favicon),
                'image': link.image,
                'description': link.description,
                'ptname': link.ptname,
                'pointed': link.pointedapi(apiuser.id)
                }
            jsonposts[str(count)] = linkdata
            count += 1
        jsonposts['sel_user'] = {
                'id': user.id,
                'pseudo': user.pseudo,
                'name': user.name,
                'bio': user.bio,
                'joindate': user.joindate,
                'verified': user.verified,
                'flair': user.flair,
                'avatar': user.avatar(),
                'postcount': user.postcount(),
                'trailscount': user.trailscount(),
                'trailingcount': user.trailingcount(),
                'istrailing': user.istrailing(apiuser.id)
                }
        jsonposts['has_next'] = pagination.has_next
        jsonposts['user'] = {'points': int(apiuser.points)}
        return jsonify(jsonposts)
    else:
        return jsonify({'errors': 'User not found!'})


@app.route('/api/getunlistedchains', methods=['POST'])
def getunlistedchains():
    formid = request.json['userid']
    formkey = request.json['apikey']
    user = User.query.filter_by(id=formid).first()
    apicheck = UserApiKey.query.filter_by(key=formkey).first()
    if user is not None and formkey == apicheck.key:
        unlchains = Chain.query.filter_by(userid=user.id).filter(Chain.visibility==2).all()
        chains = {}
        for chain in unlchains:
            chains[chain.id] = chain.title
        return jsonify(chains)

@app.route('/api/crawl', methods=['POST'])
def crawllink():
    if 'user' in session and session['rank'] >= 2:
        linkid = request.json['linkid']
        link = Link.query.filter_by(id=linkid).first()
        url = link.link

        # Request and Parse HTML of link
        try:
            t = requests.get(url, headers=headers)
            t = lxml.html.fromstring(t.text)
        except Exception:
            t = ''

        # Scrape the link using /links/scrape.py
        scrapedata = scrape_link(url, t)
        title = scrapedata.title
        image = scrapedata.image
        description = scrapedata.description
        favicon = scrapedata.favicon

        link.title = title
        link.image = image
        link.description = description
        link.favicon = favicon

        db.session.commit()

        return jsonify()

@app.route('/i/addcomment', methods=['POST'])
def sendcomment():
    comment = request.json['comment']
    link = request.json['linkid']
    chain = request.json['chainid']

    # Post it
    if 'user' in session:
        if comment == None or comment.isspace():
            return jsonify({'error': 'Comment cannot be blank!'})
        else:
            comment = escapeit(comment)
            time = datetime.now().strftime('%m-%d-%y %I:%M:%S %p')
            newcom = Comment(session['userid'], link, chain, comment, 0, time)
            db.session.add(newcom)
            db.session.commit()
        return jsonify({'user': session['user'], 'comment': comment})
    else:
        return jsonify({'error': 'Must be signed in!'})

@app.route('/i/delcomment', methods=['POST'])
def deletecomment():
    comid = request.json['comid']
    comment = Comment.query.filter_by(id=comid).first()
    if session['userid'] == comment.userid or session['rank'] >= 2:
        comment.userid = 0
        comment.text = '[Deleted]'
        db.session.commit()
        return jsonify()

# Post reference Link
@app.route('/i/addref', methods=['POST'])
def addref():
    link = request.json['link'].strip()
    linkid = request.json['linkid']

    # Validate URL
    if check_link(link):
        pass
    else:
        return jsonify({ 'error': 'Please enter a valid link' })

    # Request and Parse HTML of link
    try:
        t = requests.get(link, headers=headers)
        t = lxml.html.fromstring(t.text)
    except Exception:
        t = ''

    # Scrape the link using /links/scrape.py
    scrapedata = scrape_link(link, t)
    title = scrapedata.title
    image = scrapedata.image
    description = scrapedata.description
    favicon = scrapedata.favicon

    if ReferenceLink.query.filter_by(link=linkid).count() == 3:
        return jsonify({ 'error': 'Reference Link limit reached! (3)'})

    # Post it
    if link == None:
        flash('Please enter a link!')
    else:
        time = datetime.now().strftime('%m-%d-%y %I:%M:%S %p')
        newref = ReferenceLink(session['userid'], linkid, link, time, title, favicon, image, description)
        db.session.add(newref)
        db.session.commit()
    return jsonify()

# Create a new chain
@app.route('/i/newchain', methods=['POST'])
def newchain():
    if 'user' in session:
        chaintitle = request.json['chaintitle'].strip()
        chaindesc = request.json['chaindesc']
        chainvis = request.json['chainvis']
        if chaintitle.isspace():
            return jsonify({ 'error': 'Title cannot be blank!'})
        if re.match("^[a-zA-Z0-9 #_.'-]+$", chaintitle):
            check = Chain.query.filter(func.lower(Chain.title)==func.lower(chaintitle)).first()
            if check == None:
                if len(chaintitle) > 50:
                    return jsonify({ 'error': 'Chain title must be 50 characters or less!'})
                elif len(chaindesc) > 300:
                    return jsonify({ 'error': 'Chain description must be 300 characters or less!'})
                else:
                    newuuid = genuuid()
                    newchain = Chain(newuuid, session['userid'], chaintitle, escapeit(chaindesc), chainvis, 1, datetime.now())
                    db.session.add(newchain)
                    db.session.commit()
                    return jsonify({'uuid': newuuid})
            else:
                return jsonify({ 'error': 'There is already a chain with that title!'})
        else:
            return jsonify({ 'error': 'Some characters in chain title not allowed! Allowed(a-z;A-Z;0-9; _)'})

@app.route('/api/chainsuggest', methods=['GET'])
def suggestchain():
    chainlist = []
    term = request.args.get('term').lower()
    if request.args.get('userid'):
        userid = int(request.args.get('userid'))
    elif 'user' in session:
        userid = session['userid']
    else:
        return 'error'
    chains = Chain.query.filter((or_(Chain.visibility == 1, Chain.userid == userid)) & (func.lower(Chain.title).startswith(term))).limit(5)
    for chain in chains:
        chainlist.append(chain.title)
    return json.dumps(chainlist)


# Add a link to a chain
@app.route('/i/addchain', methods=['POST'])
def addlinktochain():
    if 'user' in session:
        error = None
        chaintitles = request.json['chaintitle'].strip().lower().replace(', ', ',').split(',')
        linkid = request.json['linkid']
        link = Link.query.filter_by(id=linkid).first()
        for chaintitle in chaintitles:
            if not chaintitle.isspace() and chaintitle != '':
                chain = Chain.query.filter((or_(Chain.visibility == 1, Chain.userid == session['userid'])) & (func.lower(Chain.title)==chaintitle)).first()
                if chain != None:
                    if link != None and link.visibility == 1:
                        check = Chainlink.query.filter((Chainlink.chain == chain.id) & (Chainlink.link == linkid)).first()
                        if check == None:
                            addlink = Chainlink(session['userid'], linkid, chain.id, datetime.now())
                            db.session.add(addlink)
                            db.session.commit()
                        else:
                            error = 'That link is already in chain '+ chain.title + '!'
                    else:
                        error = 'That link does not exist!'
                else:
                    error = 'The chain "'+chaintitle+'" is not real!'
        if error:
            return jsonify({'error': error})
        else:
            return jsonify()

# Add a new link directly to a chain
@app.route('/i/newaddchain', methods=['POST'])
def addnewlinktochain():
    if 'user' in session:
        chainid = request.json['chainid']
        comment = request.json['comment']
        link = request.json['link'].strip()
        ptname = request.json['ptname'].strip()
        linkvis = request.json['linkvis']

        chain = Chain.query.filter((or_(Chain.visibility == 1, Chain.userid == session['userid'])) & (Chain.id==chainid)).first()

        # Validate URL
        if check_link(link):
            pass
        else:
            return jsonify({ 'error': ' Please enter a valid link' })

        # Check for custom point name
        if ptname and len(ptname) > 20:
            return jsonify({ 'error': ' Point name cannot be more than 20 chars' })
        if ptname == '':
            ptname = 'Cool' # Default to "Cool"

        # Request and Parse HTML of link
        try:
            t = requests.get(link, headers=headers)
            t = lxml.html.fromstring(t.text)
        except Exception:
            t = ''

        # Scrape the link using /links/scrape.py
        scrapedata = scrape_link(link, t)
        title = scrapedata.title
        image = scrapedata.image
        description = scrapedata.description
        favicon = scrapedata.favicon

        # Post it
        if link == None:
            flash('Please enter a link!')
        else:
            uuid = genuuid()
            time = datetime.now().strftime('%m-%d-%y %I:%M:%S %p')
            if comment == None:
                newlnc = Link(uuid, session['userid'], link, None, time, 0, None, escapeit(title), escapeit(ptname), favicon, image, escapeit(description), linkvis)
            else:
                newlnc = Link(uuid, session['userid'], link, escapeit(comment), time, 0, None, escapeit(title), escapeit(ptname), favicon, image, escapeit(description), linkvis)
            db.session.add(newlnc)
            db.session.commit()

        link = Link.query.filter_by(uuid=uuid).first()
        if chain != None:
            if link != None:
                check = Chainlink.query.filter((Chainlink.chain == chain.id) & (Chainlink.link == link.id)).first()
                if check == None:
                    addlink = Chainlink(session['userid'], link.id, chain.id, datetime.now())
                    db.session.add(addlink)
                    db.session.commit()
                    return jsonify()
                else:
                    return jsonify({ 'error': 'That link is already in this chain!'})
            else:
                return jsonify({ 'error': 'That link does not exist!'})
        else:
            return jsonify({ 'error': 'This chain is not real!'})

# Remove from chain
@app.route('/i/removelfromc', methods=['POST'])
def removelfromc():
    chainid = request.json['chainid']
    linkid = request.json['linkid']
    chain = Chain.query.filter_by(id=chainid).first()
    link = Link.query.filter_by(id=linkid).first()
    linkchain = Chainlink.query.filter((Chainlink.chain==chain.id) & (Chainlink.link==link.id)).first()
    if 'user' in session and (session['userid'] == chain.userid or session['rank'] >= 2 or session['userid'] == linkchain.userid) and chain is not None:
        db.session.delete(linkchain)
        db.session.commit()
        return jsonify()
    else:
        return 'Access Denied'

# Delete a chain
@app.route('/i/deletechain', methods=['POST'])
def deletec():
    chainid = request.json['chainid']
    chain = Chain.query.filter_by(id=chainid).first()
    if 'user' in session and (session['userid'] == chain.userid or session['rank'] >= 2) and chain is not None:
        chainlinks = Chainlink.query.filter_by(chain=chain.id).all()
        links = Link.query.join(Chainlink, (Chainlink.link == Link.id)).filter(Chainlink.chain == chain.id).all()
        for link in links:
            reflinks = ReferenceLink.query.filter_by(linkid=link.id).all()
            comments = Comment.query.filter_by(link=link.id).all()
            for i in reflinks:
                db.session.delete(i)
            for i in comments:
                db.session.delete(i)
            db.session.delete(link)
        db.session.delete(chain)
        db.session.commit()
        return jsonify()
    else:
        return 'Access Denied'

# Add a point to a link
@app.route('/api/addpoint/<linkid>', methods=['POST'])
def addpoint(linkid):
    if 'user' in session:
        # Query the user signed in
        myself = User.query.filter_by(id=session['userid']).first()
        if myself.points > .5: # Make sure the user has a point
            linked = Link.query.filter_by(id=linkid).first()
            if linked.userid == session['userid']:
                return 'Denied'
            else:
                # Query the person who posted the link
                person = User.query.filter_by(id=linked.userid).first()
                points = Point(myself.id, linked.id, datetime.now(), 1)
                check = Point.query.filter((Point.link == linkid) & (Point.userid == session['userid'])).first()
                person.points += .5 # Give the person half a point (Gives a person a point for every other one donated)
                linked.points += 1
                myself.points -= 1
                if check:
                    check.amount += 1
                    check.time = datetime.now()
                else:
                    db.session.add(points)
                db.session.commit()
                session['points'] -= 1
        else:
            return '<h1>Oops</h1>Your all out of points'
    else:
        userid = request.json['userid']
        apikey = request.json['apikey']
        try:
            formkey = request.json['apikey']
        except Exception:
            return jsonify()
        linked = Link.query.filter_by(id=linkid).first()
        user = User.query.filter_by(id=userid).first()
        apicheck = UserApiKey.query.filter_by(key=formkey).first()
        if user.points > .5:
            if linked.userid == user.id:
                return jsonify({'errors': "Can't give points to your own link!"})
            if user.id == apicheck.userid:
                person = User.query.filter_by(id=linked.userid).first()
                points = Point(user.id, linked.id, datetime.now(), 1)
                check = Point.query.filter((Point.link == linkid) & (Point.userid == user.id)).first()
                person.points += .5 # Give the person half a point (Gives a person a point for every other one donated)
                linked.points += 1
                user.points -= 1
                if check:
                    check.amount += 1
                    check.time = datetime.now()
                else:
                    db.session.add(points)
                db.session.commit()
                return jsonify()
        else:
            return jsonify({'errors': 'Out of points!'})
        return jsonify({'errors': 'Unable to add point!'})
    return jsonify()

# Trail or untrail a user
@app.route('/api/trail/<userid>', methods=['POST'])
def trail(userid):
    if 'user' in session:
        istrail = Follow.query.filter((Follow.follower == session['userid']) & (Follow.followed == userid)).first()
        if istrail == None:
            trail = Follow(session['userid'], userid, datetime.now())
            db.session.add(trail)
        else:
            db.session.delete(istrail)
        db.session.commit()
        return jsonify()

# See how many points the user has donated to a link
@app.route('/api/pointcheck/<linkid>')
def pointcheck(linkid):
    if 'user' in session:
        howmany = Point.query.filter((Point.link == linkid) & (Point.userid == session['userid'])).first().amount
    else:
        return redirect(url_for('signin'))
    return jsonify({'check': howmany})

# See if you have already posted the link
# NOTE: Change to check if ANYONE has posted it
@app.route('/api/checklink', methods=['POST'])
def checklink():
    userid = request.json['userid']
    linkurl = request.json['linkurl']
    if linkurl.endswith('/'):
        linkurl = linkurl[:-1]
    link = Link.query.filter((Link.userid == userid) & (Link.link == linkurl)).first()
    # Check both http and https
    if link == None:
        linkurl = re.sub(r'https://', r'http://', linkurl)
        link = Link.query.filter((Link.userid == userid) & (Link.link == linkurl)).first()
        if link == None:
            return jsonify({'posted': 'no', 'points': '...'})
        else:
            return jsonify({'posted': 'yes', 'points': str(link.points)})
    else:
        return jsonify({'posted': 'yes', 'points': str(link.points)})

# Add to link click count
# NO TRACKING ALLOWED
@app.route('/api/addclick', methods=['POST'])
def addclick():
    linkid = request.json['linkid']
    linked = Link.query.filter_by(uuid=linkid).first()
    if linked.userid != session['userid']:
        linked.clicks += 1
        db.session.commit()
    return jsonify()

# Delete a post
@app.route('/api/delete', methods=['POST'])
def deletel():
    linkid = request.json['linkid']
    link = Link.query.filter_by(id=linkid).first()
    user = User.query.filter_by(id=link.userid).first()

    if ('user' in session and session['userid'] == link.userid) or session['rank'] >= 2:
        db.session.delete(link)
        reflinks = ReferenceLink.query.filter_by(linkid=link.id).all()
        comments = Comment.query.filter_by(link=link.id).all()
        for i in reflinks:
            db.session.delete(i)
        for i in comments:
            db.session.delete(i)
        if link.points > 0:
            pointsnow = link.points * .5
            user.points = user.points - pointsnow
        db.session.commit()
        return jsonify()
    else:
        return 'Access Denied'

@app.route('/api/deleteref', methods=['POST'])
def deletereflink():
    linkid = request.json['linkid']
    reflink = ReferenceLink.query.filter_by(id=linkid).first()
    user = User.query.filter_by(id=reflink.userid).first()
    # See if it's even their reflink to delete
    if 'user' in session and session['userid'] == reflink.userid:
        db.session.delete(reflink)
        db.session.commit()
        return jsonify()
    elif session['rank'] >= 2: # If the user is a moderator then they have the POWA
        db.session.delete(reflink)
        db.session.commit()
        return jsonify()
    else:
        return 'Access Denied'

@app.route('/api/closealert')
def closealert():
    alert = Page.query.filter_by(active=1).first()
    if alert:
        session['alertclosed'] = alert.header

    session.pop('alert')
    session.pop('alerturl')
    return jsonify({'status': 'success'})

# Generate an invite for user to give Out
# NOTE: Add functionality to send invite via email directly from invite page
@app.route('/api/geninvite')
def geninvite():
    if 'user' in session:
        user = User.query.filter_by(id=session['userid']).first()
        if user.rank >= 2 or user.verified == 1:
            invitecheck = Invite.query.filter_by(sender=session['userid']).count()
            if invitecheck < 5 or session['rank'] == 3: # Make sure user hasn't hit invite limit of 5
                code = codegen() # Generate the invite code
                # Add the invite to the database
                newinvite = Invite(session['userid'], code, datetime.now(), 0, None)
                db.session.add(newinvite)
                db.session.commit()
                return jsonify({'code': code})


# Confirm user's email
@app.route('/i/confirm/<user>/confirm/<code>')
def confirmaccount(user, code):
    user = User.query.filter_by(pseudo=user).first()
    if user and user.confirm == code: # Verify confirmation code
        user.confirm = 0 # DB confirmcode must be 0 to sign in
        db.session.commit()
        flash('You may now Sign in.')
        return redirect(url_for('signin'))
    else:
        abort(404)

# Get favicon or meta image using sick api to keep everthing HTTPS
# PS: It's basic, but I'm pretty proud of this
@app.route('/api/getexternalimage')
def externalimage():
    urlurl = request.args.get('url') # Insert special characters back into URL
    url = urlurl # I don't really know/remember what this is about; Maybe debugging? ¯\_(ツ)_/¯
    if urlurl == 'none' or urlurl == 'None':
        return send_file('static/images/defaultglobe.ico', mimetype='image/png')
    try:
        urlurl = requests.get(url)
    except requests.ConnectionError:
        print('Connection error!')
        return send_file('static/images/defaultglobe.ico', mimetype='image/png')
    if urlurl.status_code != 200:
        print('Not 200!')
        return send_file('static/images/defaultglobe.ico', mimetype='image/png')
    try:
        url = requests.get(url, headers=headers, timeout=5)
    except requests.ConnectionError:
        print('2nd Connection error!')
        return send_file('static/images/defaultglobe.ico', mimetype='image/png')
    except requests.exceptions.Timeout:
        print('Timeout!')
        return send_file('static/images/defaultglobe.ico', mimetype='image/png')
    else:
        image = app.make_response(url.content)
        contype = url.headers['Content-Type']
        contype = re.match('image/', contype) # Make sure it returns an image
        if contype: # If it is a valid image then return it
            image.headers['Content-Type'] = url.headers['Content-Type'] # Make response content type same as the requested image
            return image
        else:
            abort(404)

@app.route('/api/getloadmsg')
def getloadmsg():
    session['loadinglabel'] = loadmsgs[random.randint(0, (len(loadmsgs) - 1))]
    return(jsonify({'loadmsg': session['loadinglabel']}))

@app.route('/api/checkinteract')
def checknewint():
    if 'user' in session:
        user = User.query.filter_by(id=session['userid']).first()
        if user.checkint:
            checkinttime = user.checkint
        else:
            checkinttime = datetime.now()
        trailcount = Follow.query.filter_by(followed=session['userid']).filter(Follow.time > checkinttime).count()
        links = Link.query.filter_by(userid=session['userid']).all()
        pointcount = Point.query.join(Link, (Point.link == Link.id)).filter(Link.userid == session['userid']).filter(Point.time > checkinttime).order_by(Point.time.desc()).count()
        commentcount = Comment.query.join(Link, (Comment.link == Link.id)).filter((Link.userid == session['userid']) & (Comment.userid != session['userid'] or Comment.userid != 0) & (Comment.time > checkinttime)).order_by(Comment.time.desc()).count()
        lastfreept = FreePoint.query.filter_by(userid=session['userid']).order_by(FreePoint.time.desc()).first()
        if lastfreept:
            freeptcheck = (datetime.now() - lastfreept.time).total_seconds()
            if freeptcheck >= 72000:
                freeptcheck = 1
            else:
                freeptcheck = 0
        else:
            freeptcheck = 1
        count = trailcount + pointcount + commentcount + freeptcheck
        return jsonify({'intcount': count})
    else:
        return jsonify({'intcount': 0})

@app.route('/api/collectfreepts')
def collectfreepts():
    if 'user' in session:
        user = User.query.filter_by(id=session['userid']).first()
        lastfreept = FreePoint.query.filter_by(userid=session['userid']).order_by(FreePoint.time.desc()).first()
        if lastfreept:
            freeptcheck = (datetime.now() - lastfreept.time).total_seconds()
            if freeptcheck >= 72000:
                freeptcheck = 1
            else:
                freeptcheck = 0
        else:
            freeptcheck = 1

        if freeptcheck:
            points = randLowNum(1,10,8)
        else:
            points = 0

        user.points += points
        freepts = FreePoint(user.id, points, datetime.now())
        db.session.add(freepts)
        db.session.commit()

        session['points'] += points

        return jsonify({'points':points})

@app.route('/api/getsubposts/<sub>/<count>')
def getcustomdash(sub, count):
    posts = requests.get('https://www.reddit.com/r/'+sub+'.json', headers=headers).text
    data = json.loads(posts)['data']['children']
    ret = {sub: {}}
    i = 0
    while i < int(count):
        try:
            ret[sub][i] = data[i]['data']['title']
        except Exception:
            ret[sub][i] = 'Error!'
        i+=1
    return jsonify(ret)
