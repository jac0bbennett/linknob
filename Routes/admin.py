#!/usr/bin/env python

# Copyright Jacob Bennett 10/20/16

from flask import render_template, request, session, abort, jsonify
from config import app, db
from Models.models import User, Link, Point, Page
from utils import Pagination, colorgen, escapeit
from Links.trending import trend
from datetime import datetime
from Routes import maintenance
import importlib, re

# Admin Dashboard
@app.route('/i/dashboard')
def dashboard():
    if 'user' in session and session['rank'] == 3:
        title = 'Dashboard'
        # Query site stats
        users = User.query.filter(User.joindate != None).order_by(User.joindate.desc()).limit(20)
        links = Link.query.order_by(Link.time.desc()).limit(20)
        points = Point.query.order_by(Point.time.desc()).limit(20)
        totalusers = User.query.count() - 3
        totallinks = Link.query.count()
        totalpoints = Point.query.count()
        trendingurls = trend.urls()
        activepage = Page.query.filter_by(active=1).first()
        pages = Page.query.filter_by(active=0).order_by(Page.time.desc()).limit(10)
        return render_template('dashboard.html', title=title, users=users, links=links, points=points, totalusers=totalusers, totallinks=totallinks, totalpoints=totalpoints, trendingurls=trendingurls, activepage=activepage, pages=pages)
    else:
        abort(403)

@app.route('/i/maintenance/<status>')
def triggermaintenance(status):
    importlib.reload(maintenance)
    if 'user' in session and session['rank'] == 3:
        with open('Routes/maintenance.py', 'w') as maint:
            if status == 'off':
                maint.write('status = False')
                return 'Maintenance Mode Off'
            elif status == 'on':
                maint.write('status = True')
                return 'Maintenance Mode On'
            else:
                abort(404)
    else:
        abort(404)

@app.route('/i/newdoc', methods=['GET','POST'])
def createnewdoc():
    title = 'New Page'
    if 'user' in session and session['rank'] == 3:
        if request.method == 'POST':
            title = request.json['title']
            url = request.json['url'].strip()
            header = request.json['header']
            content = request.json['content']
            active = request.json['active']
            if active == 'page':
                active = 0
            else:
                active = 1
                activecheck = Page.query.filter_by(active=1).first()
                if activecheck:
                    return jsonify({'error': 'The page ' + activecheck.url + ' is already set to active!'})
            if title == '' or url == '' or header == '' or content == '':
                return jsonify({'error': 'All fields are required!'})
            else:
                check = Page.query.filter_by(url=url).first()
                if not check:
                    if re.match('^[a-z0-9_-]+$', url):
                        title = escapeit(title)
                        header = escapeit(header)
                        content = content

                        newdoc = Page(url, title, header, content, datetime.now(), active)

                        db.session.add(newdoc)
                        db.session.commit()

                        return jsonify()
                    else:
                        return jsonify({'error': 'Some characters unallowed in Url!'})
                else:
                    return jsonify({'error': 'A page already exists with that url!'})
        else:
            return render_template('editdoc.html', title=title, page=None)
    else:
        abort(404)

@app.route('/i/editdoc/<docurl>', methods=['GET','POST'])
def editdoc(docurl):
    title = 'Edit Page | ' + docurl
    if 'user' in session and session['rank'] == 3:
        page = Page.query.filter_by(url=docurl).first()
        if page:
            if request.method == 'POST':
                delete = request.json['deletedoc']
                if delete:
                    db.session.delete(page)
                    db.session.commit()
                    return jsonify()
                title = request.json['title']
                url = request.json['url'].strip()
                header = request.json['header']
                content = request.json['content']
                active = request.json['active']
                if active == 'page':
                    active = 0
                else:
                    active = 1
                    activecheck = Page.query.filter_by(active=1).first()
                    if activecheck and activecheck.id != page.id:
                        return jsonify({'error': 'The page ' + activecheck.url + ' is already set to active!'})
                if title == '' or url == '' or header == '' or content == '':
                    return jsonify({'error': 'All fields are required!'})
                else:
                    check = Page.query.filter_by(url=url).first()
                    if not check or check.id == page.id:
                        if re.match('^[a-z0-9_-]+$', url):
                            title = escapeit(title)
                            header = escapeit(header)
                            content = content

                            page.url = url
                            page.title = title
                            page.header = header
                            page.content = content
                            page.active = active
                            page.time = datetime.now()

                            db.session.commit()

                            return jsonify()
                        else:
                            return jsonify({'error': 'Some characters unallowed in Url!'})
                    else:
                        return jsonify({'error': 'A page already exists with that url!'})
            else:
                return render_template('editdoc.html', title=title, page=page)
        else:
            abort(404)
    else:
        abort(404)

@app.route('/loaderio-6c4b182450998bf144d03acda53ce019')
def loaderverify():
    return 'loaderio-6c4b182450998bf144d03acda53ce019'
