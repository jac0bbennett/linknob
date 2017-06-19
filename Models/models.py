#!/usr/bin/env python

# Copyright Jacob Bennett 2/4/17

from config import db
from flask import session
from sqlalchemy import Date, cast, func, or_
from Links.score import score
from datetime import date
from hashlib import md5

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    pseudo = db.Column(db.String(20), nullable=False, unique=True)
    key = db.Column(db.String, nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    rank = db.Column(db.Integer, default=1)
    name = db.Column(db.String)
    bio = db.Column(db.String, default='')
    points = db.Column(db.Float, default=10)
    joindate = db.Column(db.DateTime)
    verified = db.Column(db.Integer, default=0)
    confirm = db.Column(db.String)
    checkint = db.Column(db.DateTime)
    flair = db.Column(db.String)

    pathid = 0

    def __init__(self, pseudo, key, email, rank, name, bio, points, joindate, verified, confirm, checkint, flair, pathid=0):
        self.pseudo = pseudo
        self.key = key
        self.email = email
        self.rank = rank
        self.name = name
        self.bio = bio
        self.points = points
        self.joindate = joindate
        self.verified = verified
        self.confirm = confirm
        self.checkint = checkint
        self.flair = flair

        self.pathid = pathid

    def __repr__(self):
        return '<User %r>' % self.pseudo

    def avatar(self):
        email = str(self.email).encode('utf-8')
        md5hash = md5(email).hexdigest()
        avatar = 'https://secure.gravatar.com/avatar/' + md5hash + '?d=identicon'
        return avatar

    def postcount(self):
        count = Link.query.filter_by(userid=self.id).filter(Link.visibility==1).count()
        return count

    def trailscount(self):
        count = Follow.query.filter_by(followed=self.id).count()
        return count

    def trailingcount(self):
        count = Follow.query.filter_by(follower=self.id).count()
        return count

    def istrailing(self):
        if 'user' in session:
            # Check if user is trailing this user
            istrail = Follow.query.filter((Follow.follower == session['userid']) & (Follow.followed == self.id)).first()
        else:
            istrail = None
        if istrail:
            istrail = True
        else:
            istrail = False

        return istrail

    # Get posts from only who you trail
    def followed_posts(pathid):
        q1 = Link.query.filter_by(userid=pathid).filter(Link.visibility == 1)
        return q1.union(Link.query.join(Follow, (Follow.followed == Link.userid)).filter(Follow.follower == pathid)).filter_by(visibility=1).order_by(Link.time.desc())

    # Get top posts from trailing
    def followed_posts_top(pathid):
        q1 = Link.query.filter_by(userid=pathid).filter(Link.visibility == 1)
        return q1.union(Link.query.join(Follow, (Follow.followed == Link.userid)).filter(Follow.follower == pathid)).filter_by(visibility=1).order_by(Link.points.desc())

    # Get scored from trailing
    def followed_posts_scored(pathid):
        q1 = Link.query.filter(Link.visibility == 1).join(Follow, (Follow.followed == Link.userid)).filter(or_(Link.userid == pathid, Follow.follower == pathid)).join(Point, (Point.link == Link.id)).group_by(Link.id).filter((Link.points > 0) & (Link.age >= 60)).order_by((score(Link.points, Link.time, func.count(Point.id))).desc())
        return q1


class Link(db.Model):
    __tablename__ = 'links'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True)
    userid = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String, nullable=False)
    comment = db.Column(db.String(300))
    time = db.Column(db.DateTime)
    points = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    title = db.Column(db.String, default='None')
    ptname = db.Column(db.String(12), default="Cool")
    favicon = db.Column(db.String, default='None')
    image = db.Column(db.String, default='None')
    description = db.Column(db.String, default='None')
    visibility = db.Column(db.Integer, default=1) #1=Public, 2=Chain specific

    age = func.extract('epoch', func.current_timestamp() - time)

    def __init__(self, uuid, userid, link, comment, time, points, clicks, title, ptname, favicon, image, description, visibility):
        self.uuid = uuid
        self.userid = userid
        self.link = link
        self.comment = comment
        self.time = time
        self.points = points
        self.clicks = clicks
        self.title = title
        self.ptname = ptname
        self.favicon = favicon
        self.image = image
        self.description = description
        self.visibility = visibility

    def __repr__(self):
        return '<Link %r>' % self.link

    def pseudo(self):
        user = User.query.filter_by(id=self.userid).first()
        if user:
            return user.pseudo
        else:
            return '[Deleted]'

    def pointcount(self):
        count = Point.query.with_entities(func.sum(Point.amount)).filter_by(link=self.id).scalar()
        if not count:
            count = 0
        return count

    def pointed(self):
        if 'user' in session:
            point = Point.query.filter_by(link=self.id).filter(Point.userid == session['userid']).first()
            if point:
                return 'style=color:#fff;background:#C44437;'

    def pointedapi(self, userid):
        point = Point.query.filter_by(link=self.id).filter(Point.userid == userid).first()
        if point:
            return True
        else:
            return False

    def comcount(self):
        count = Comment.query.filter_by(link=self.id).count()
        return count

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    link = db.Column(db.Integer, nullable=False)
    chain = db.Column(db.Integer, default=0)
    text = db.Column(db.String(300))
    depth = db.Column(db.Integer, default=0)
    time = db.Column(db.DateTime)

    def __init__(self, userid, link, chain, text, depth, time):
        self.userid = userid
        self.link = link
        self.chain = chain
        self.text = text
        self.depth = depth
        self.time = time

    def __repr__(self):
        return '<Comment %r>' % self.text

    def pseudo(self):
        user = User.query.filter_by(id=self.userid).first()
        if user:
            return user.pseudo
        else:
            return '[Deleted]'

class ReferenceLink(db.Model):
    __tablename__ = 'referencelinks'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    linkid = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String, nullable=False)
    time = db.Column(db.DateTime)
    title = db.Column(db.String, default='None')
    favicon = db.Column(db.String, default='None')
    image = db.Column(db.String, default='None')
    description = db.Column(db.String, default='None')

    def __init__(self, userid, linkid, link, time, title, favicon, image, description):
        self.userid = userid
        self.linkid = linkid
        self.link = link
        self.time = time
        self.title = title
        self.favicon = favicon
        self.image = image
        self.description = description

    def __repr__(self):
        return '<Ref Link %r>' % self.link

    def pseudo(self):
        user = User.query.filter_by(id=self.userid).first()
        if user:
            return user.pseudo
        else:
            return '[Deleted]'


class Point(db.Model):
    __tablename__ = 'points'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    link = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Integer, nullable=False)

    def __init__(self, userid, link, time, amount):
        self.userid = userid
        self.link = link
        self.time = time
        self.amount = amount

    def __repr__(self):
        return '<Link %r>' % self.link

    def pseudo(self):
        user = User.query.filter_by(id=self.userid).first()
        if user:
            return user.pseudo
        else:
            return '[Deleted]'

    # Get link point updates
    def new_points(userid):
        links = Link.query.filter_by(id=userid).all()
        q2 = Point.query.join(Link, (Link.id == Point.link)).filter(Link.userid == userid).order_by(Point.time.desc())
        return q2


# DB model for general, static pages/announcements
class Page(db.Model):
    __tablename__ = 'pages'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    header = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Integer, default=0)

    def __init__(self, url, title, header, content, time, active):
        self.url = url
        self.title = title
        self.header = header
        self.content = content
        self.time = time
        self.active = active

    def __repr__(self):
        return '<Page %r>' % self.title

# DB model for Monthly point bump
class Monthupdate(db.Model):
    __tablename__ = 'monthupdates'

    id = db.Column(db.Integer, primary_key=True)
    users = db.Column(db.Integer, nullable=False)
    links = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, nullable=False)

    def __init__(self, users, links, time):
        self.users = users
        self.links = links
        self.time = time

    def __repr__(self):
        return '<Update %r>' % self.time

class FreePoint(db.Model):
    __tablename__ = 'freepoints'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, nullable=False)

    def __init__(self, userid, points, time):
        self.userid = userid
        self.points = points
        self.time = time

    def __repr__(self):
        return '<FP %r>' % self.points

# DB model for trails
class Follow(db.Model):
    __tablename__ = 'follows'

    id = db.Column(db.Integer, primary_key=True)
    follower = db.Column(db.Integer, nullable=False)
    followed = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, nullable=False)

    def __init__(self, follower, followed, time):
        self.follower = follower
        self.followed = followed
        self.time = time

    def __repr__(self):
        return '<Trail %r>' % self.followed

class Invite(db.Model):
    __tablename__ = 'invites'

    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String, nullable=False)
    timegen = db.Column(db.DateTime)
    activated = db.Column(db.Integer, default=0)
    userid = db.Column(db.Integer)

    def __init__(self, sender, code, timegen, activated, userid):
        self.sender = sender
        self.code = code
        self.timegen = timegen
        self.activated = activated
        self.userid = userid

    def __repr__(self):
        return '<Invite %r>' % self.code

# DB model for Invite Requests
class Request(db.Model):
    __tablename__ = 'requests'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False)
    time = db.Column(db.DateTime)
    invited = db.Column(db.Integer, default=0)

    def __init__(self, email, time, invited):
        self.email = email
        self.time = time
        self.invited = invited

    def __repr__(self):
        return '<Request %r>' % self.email


class Resetkey(db.Model):
    __tablename__ = 'resetkeys'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, nullable=False)
    userid = db.Column(db.Integer)

    def __init__(self, code, userid):
        self.code = code
        self.userid = userid

    def __repr__(self):
        return '<Code %r>' % self.code

class Chain(db.Model):
    __tablename__ = 'chains'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True)
    userid = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    visibility = db.Column(db.Integer, default=1) # 1=Public, 2=Unlisted
    permission = db.Column(db.Integer, default=1)
    created = db.Column(db.DateTime)

    def __init__(self, uuid, userid, title, description, visibility, permission, created):
        self.uuid = uuid
        self.userid = userid
        self.title = title
        self.description = description
        self.visibility = visibility
        self.permission = permission
        self.created = created

    def __repr__(self):
        return '<Chain %r>' % self.title

    def pseudo(self):
        user = User.query.filter_by(id=self.userid).first()
        if user:
            return user.pseudo
        else:
            return '[Deleted]'

class Chainlink(db.Model):
    __tablename__ = 'chainlinks'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    link = db.Column(db.Integer, nullable=False)
    chain = db.Column(db.Integer, nullable=False)
    added = db.Column(db.DateTime)

    def __init__(self, userid, link, chain, added):
        self.userid = userid
        self.link = link
        self.chain = chain
        self.added = added

    def __repr__(self):
        return '<Chainlink %r>' % self.link

    def pseudo(self):
        user = User.query.filter_by(id=self.userid).first()
        if user:
            return user.pseudo
        else:
            return '[Deleted]'

class UserApiKey(db.Model):
    __tablename__ = 'userapikeys'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    key = db.Column(db.String, nullable=False)
    added = db.Column(db.DateTime)

    def __init__(self, userid, key, added):
        self.userid = userid
        self.key = key
        self.added = added

    def __repr__(self):
        return '<User Api Key %r>' % self.key

    def pseudo(self):
        user = User.query.filter_by(id=self.userid).first()
        if user:
            return user.pseudo
        else:
            return '[Deleted]'

'''
Classifier Api
'''
class ClassifyKey(db.Model):
    __bind_key__ = 'classify'
    __tablename__ = 'keys'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, nullable=False)
    email = db.Column(db.String)
    queries = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime)
    active = db.Column(db.Integer, default=1)
    querylimit = db.Column(db.Integer, default=100)
    lastquery = db.Column(db.DateTime)

    def __init__(self, key, email, queries, created, active, querylimit, lastquery):
        self.key = key
        self.email = email
        self.queries = queries
        self.created = created
        self.active = active
        self.querylimit = querylimit
        self.lastquery = lastquery

    def __repr__(self):
        return '<Email %r>' % self.email

class FileQueue(db.Model):
    __bind_key__ = 'classify'
    __tablename__ = 'filequeue'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String)
    upload = db.Column(db.String)
    save = db.Column(db.String)
    status = db.Column(db.String)
    complete = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer)
    added = db.Column(db.DateTime)
    category = db.Column(db.String, default='topics')

    def __init__(self, key, upload, save, status, complete, total, added, category):
        self.key = key
        self.upload = upload
        self.save = save
        self.status = status
        self.complete = complete
        self.total = total
        self.added = added
        self.category = category

    def __repr__(self):
        return '<Save Filename %r>' % self.save
