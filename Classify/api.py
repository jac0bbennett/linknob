#!/usr/bin/env python
from flask import render_template, request, session, jsonify, abort, flash, redirect, url_for, send_file
from werkzeug import secure_filename
from datetime import datetime
from config import app, db
from utils import codegen
from Models.models import ClassifyKey, FileQueue
import requests, json, os, string, threading, time
import urllib.parse as urlparse

def genkey(email, limit):
    checkemail = ClassifyKey.query.filter_by(email=email).first()
    if checkemail:
        return 'Email already in use'

    newkey = ClassifyKey(codegen(size=11, chars=string.ascii_letters), email, 0, datetime.now(), 1, limit, datetime.now())
    db.session.add(newkey)
    db.session.commit()

def processfile(uploadname, savename, key):
    keycheck = ClassifyKey.query.filter_by(key=key).first()
    fileq = FileQueue.query.filter_by(save=savename).first()
    with open('Classify/temp/'+key+'/'+savename, 'w') as f, open('Classify/temp/uploads/'+uploadname, 'r') as r:
        f.write('Url,Arts,Business,Computers,Games,Health,Home,Recreation,Science,Society,Sports\n')
        for url in r.read().split('\n'):
            if fileq.status == 'cancelled':
                break
            elif keycheck.queries < keycheck.querylimit:
                if not url.startswith('http'):
                    url = 'http://' + url
                #url = urlparse.quote_plus(url)
                #req = requests.get(url)
                req = requests.get('http://uclassify.com/browse/uclassify/topics/ClassifyUrl/?readkey=yWyLHltfbdYQ&output=json&url='+url)
                data = req.json()
                #data = {}
                try:
                    data = data['cls1']
                except KeyError:
                    data = None
                if data:
                    f.write(urlparse.unquote(url)+','+str(data['Arts'])+','+str(data['Business'])+','+str(data['Computers'])+','
                    +str(data['Games'])+','+str(data['Health'])+','+str(data['Home'])+','+str(data['Recreation'])+','
                        +str(data['Science'])+','+str(data['Society'])+','+str(data['Sports'])+'\n')
                else:
                    f.write(urlparse.unquote(url)+'\n')
                keycheck.queries += 1
                keycheck.lastquery = datetime.now()
                fileq.complete += 1
                db.session.commit()
    if fileq.status != 'cancelled':
        fileq.status = 'complete'
        db.session.commit()
    os.remove(os.path.join('Classify/temp/uploads', uploadname))


def queuefile(uploadname, savename, keycheck):
    checkqueue = FileQueue.query.filter_by(status='processing').count()
    checkkeyqueue = FileQueue.query.filter_by(key=keycheck.key).filter(FileQueue.status=='processing').first()
    with open('Classify/temp/uploads/'+uploadname, 'r') as r:
        rowcount = len(r.read().split('\n'))
    if checkkeyqueue:
        newqueue = None
        filestatus = 'running'
    elif checkqueue < 2:
        newqueue = FileQueue(keycheck.key, uploadname, savename, 'processing', 0, rowcount, datetime.now())
        process = threading.Thread(target=processfile, kwargs={'uploadname': uploadname, 'savename': savename, 'key': keycheck.key})
        process.daemon = True
        process.start()
        filestatus = 'processing'
    else:
        newqueue = None
        filestatus = 'unavailable'
        '''
        #Queue files for later
        newqueue = FileQueue(keycheck.key, uploadname, savename, 'queued', 0, rowcount, datetime.now())
        filestatus = 'queued'
        '''
    if newqueue:
        db.session.add(newqueue)
    db.session.commit()
    return filestatus

@app.route('/api/classify/check/<key>')
def checkqueueid(key):
    check = FileQueue.query.filter_by(key=key).order_by(FileQueue.added.desc()).first()
    apikey = ClassifyKey.query.filter_by(key=key).first()
    if datetime.date(apikey.lastquery) != datetime.date(datetime.now()):
        apikey.queries = 0
        db.session.commit()
    if check:
        return jsonify({
        'id': check.id,
        'result': check.save,
        'status': check.status,
        'complete': check.complete,
        'total': check.total,
        'added': check.added,
        'apiused': apikey.queries,
        'apilimit': apikey.querylimit,
        'url': '/api/classify/temp/'+check.save+'?key='+check.key
        })
    else:
        return jsonify({'status': 'none'})

@app.route('/api/classify/cancel/<key>')
def cancelqueue(key):
    check = FileQueue.query.filter_by(key=key).filter(FileQueue.status=='processing').order_by(FileQueue.added.desc()).first()
    if check:
        check.status = 'cancelled'
        db.session.commit()
        return jsonify()
    else:
        abort(404)

@app.route('/api/classify/topics', methods=['GET', 'POST'])
def classifytopics():
    if request.method == 'GET':
        title = 'Upload'
        if 'classifykey' in session:
            queuedfile = FileQueue.query.filter_by(key=session['classifykey']).filter(FileQueue.status=='processing').order_by(FileQueue.added.asc()).first()
        else:
            queuedfile = None

        if 'classifykey' in session:
            apikey = ClassifyKey.query.filter_by(key=session['classifykey']).first()
        else:
            apikey = None
        return render_template('classify/upload.html', title=title, queuedfile=queuedfile, apikey=apikey)
    elif request.method == 'POST':
        key = request.form['apikey']
        keycheck = ClassifyKey.query.filter_by(key=key).first()
        if not keycheck:
            return jsonify({'error': 'Invalid API key'})
        session['classifykey'] = key
        if datetime.date(keycheck.lastquery) != datetime.date(datetime.now()):
            keycheck.queries = 0
        if keycheck.queries >= keycheck.querylimit:
            return jsonify({'error': 'Exceeded daily limit. ('+str(keycheck.querylimit)+')'})
        if 'file' not in request.files:
            return jsonify({'error': 'Missing file'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Missing file'})
        fileext = file.filename.split('.')[1]
        if fileext != 'csv' and fileext != 'txt':
            return jsonify({'error': 'File extension not supported'})
        uploadname = secure_filename(file.filename.split('.')[0]+'---'+codegen(5)+'.'+file.filename.split('.')[1])
        file.save(os.path.join('Classify/temp/uploads', uploadname))
        savename = uploadname.split('.')[0].split('---')[0]+'-topics-'+str(datetime.now()).split('.')[0].replace(':', '-')+'.csv'
        if not os.path.exists(os.path.join('Classify/temp/'+key)):
            os.makedirs(os.path.join('Classify/temp/'+key))
        queue = queuefile(uploadname, savename, keycheck)
        return jsonify({'status': queue, 'savename': savename})

@app.route('/api/classify/temp/list/<classifier>')
def listclassifyfiles(classifier):
    key = request.args.get('key')
    if key and ClassifyKey.query.filter_by(key=key).first():
        session['classifykey'] = key
        files = FileQueue.query.filter_by(key=key).order_by(FileQueue.added.desc()).all()
        '''
        #View files in file system
        files = [f for f in os.listdir(os.path.join('Classify/temp/'+key)) if '-'+classifier+'-' in f]
        files.sort(key=lambda x: os.stat(os.path.join('Classify/temp/'+key, x)).st_mtime)
        files = files[::-1]
        '''
        return render_template('classify/listfiles.html', files=files, classifier=classifier, key=key)
    else:
        abort(404)

@app.route('/api/classify/temp/<csvname>')
def downloadcsv(csvname):
    key = request.args.get('key')
    if key:
        try:
            file = send_file('Classify/temp/'+key+'/'+csvname, mimetype='text/csv')
        except Exception:
            return abort(404)
        return file
    else:
        abort(404)
