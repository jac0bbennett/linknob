#!/usr/bin/env python
from flask import render_template, request, session, jsonify, abort, flash, redirect, url_for, send_file
from werkzeug import secure_filename
from datetime import datetime
from config import app, db
from utils import codegen
from Models.models import ClassifyKey, FileQueue
from Classify import mbasket
import requests, json, os, string, threading, time, csv
import urllib.parse as urlparse

def genkey(email, limit):
    checkemail = ClassifyKey.query.filter_by(email=email).first()
    if checkemail:
        return 'Email already in use'

    newkey = ClassifyKey(codegen(size=11, chars=string.ascii_letters), email, 0, datetime.now(), 1, limit, datetime.now())
    db.session.add(newkey)
    db.session.commit()

def processfile(uploadname, savename, key, topictypes):
    keycheck = ClassifyKey.query.filter_by(key=key).first()
    fileq = FileQueue.query.filter_by(save=savename).first()
    gentopics = ['Arts', 'Business', 'Computers', 'Games', 'Health', 'Home',
        'Recreation', 'Science', 'Society', 'Sports']
    comptopics = ['News_and_Media', 'Internet', 'Virtual_Reality', 'Systems', 'Education',
        'Data_Communications', 'Hardware', 'Security', 'E-Books', 'Human-Computer_Interaction',
        'CAD_and_CAM', 'Robotics', 'History', 'Organizations', 'Software',
        'Open_Source', 'FAQs,_Help,_and_Tutorials', 'Mobile_Computing', 'Desktop_Publishing', 'Performance_and_Capacity',
        'Data_Formats', 'Multimedia', 'Speech_Technology', 'Programming', 'Consultants',
        'Home_Automation', 'Graphics', 'Usenet', 'Ethics', 'Parallel_Computing', 'Hacking',
        'Algorithms', 'Artificial_Life', 'Artificial_Intelligence', 'Bulletin_Board_Systems', 'Computer_Science',
        'Supercomputing', 'Emulators']
    alltopics = [] #Append all selected categories to this list
    alltopics.append('Url')
    if 'general' in topictypes:
        for topic in gentopics:
            alltopics.append(topic)
    if 'computer' in topictypes:
        for topic in comptopics:
            alltopics.append(topic)
    fullsize = 0
    for i in topictypes:
        fullsize += 1
    fileq.total = fileq.total * fullsize
    db.session.commit()
    with open('Classify/temp/'+key+'/'+savename, 'w', newline="") as destfile, open('Classify/temp/uploads/'+uploadname, 'r') as r:
        f = csv.DictWriter(destfile, fieldnames=alltopics)
        f.writeheader()
        for url in r.read().split('\n'):
            if fileq.status == 'cancelled':
                break
            elif keycheck.queries < keycheck.querylimit:
                if not url.startswith('http'):
                    url = 'http://' + url
                writedata = {}
                writedata['Url'] = url
                if 'general' in topictypes:
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
                        for i in data:
                            writedata[i] = data[i]
                    keycheck.queries += 1
                    keycheck.lastquery = datetime.now()
                    fileq.complete += 1
                    db.session.commit()
                if 'computer' in topictypes:
                    req = requests.get('http://uclassify.com/browse/uclassify/computer-topics/ClassifyUrl/?readkey=yWyLHltfbdYQ&output=json&url='+url)
                    data = req.json()
                    try:
                        data = data['cls1']
                    except KeyError:
                        data = None
                    if data:
                        for i in data:
                            writedata[i] = data[i]
                    keycheck.lastquery = datetime.now()
                    fileq.complete += 1
                    db.session.commit()
                f.writerow(writedata)
    if fileq.status != 'cancelled':
        fileq.status = 'complete'
        db.session.commit()
    os.remove(os.path.join('Classify/temp/uploads', uploadname))


def queuefile(uploadname, savename, keycheck, type='topics', support=0, confidence=0, antqnt='one', upformat=2, topictypes='general'):
    checkqueue = FileQueue.query.filter_by(status='processing').count()
    checkkeyqueue = FileQueue.query.filter_by(key=keycheck.key).filter(FileQueue.status=='processing').first()
    with open('Classify/temp/uploads/'+uploadname, 'r') as r:
        rowcount = len(r.read().split('\n'))
    if checkkeyqueue:
        newqueue = None
        filestatus = 'running'
    elif checkqueue < 2:
        newqueue = FileQueue(keycheck.key, uploadname, savename, 'processing', 0, rowcount, datetime.now(), type)
        if type == 'topics':
            process = threading.Thread(target=processfile, kwargs={'uploadname': uploadname, 'savename': savename, 'key': keycheck.key, 'topictypes': topictypes})
        elif type == 'assoc':
            process = threading.Thread(target=mbasket.calc, kwargs={'support_threshold': support, 'confidence_threshold': confidence, 'uploadname': uploadname, 'savename': savename, 'key': keycheck.key, 'antqnt': antqnt, 'upformat': upformat})
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
        'catg': check.category,
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
    if check and ('-assoc-' not in check.save):
        check.status = 'cancelled'
        db.session.commit()
        return jsonify()
    elif check and ('-assoc-' in check.save):
        return jsonify({'error': 'Cancellation unavailable!'})
    else:
        abort(404)

@app.route('/api/classify', methods=['GET', 'POST'])
def classifytopics():
    catg = request.args.get('catg')
    if not catg:
        catg = 'topics'
    elif catg != 'topics':
        abort(404)
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
        return render_template('classify/upload.html', title=title, queuedfile=queuedfile, apikey=apikey, catg=catg)
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
        if 'topictypes' not in request.form or request.form['topictypes'] == '':
            return jsonify({'error': 'Topic category must be selected!'})
        else:
            topictypes = request.form.getlist('topictypes')
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
        savename = uploadname.split('.')[0].split('---')[0]+'-'+catg+'-'+str(datetime.now()).split('.')[0].replace(':', '-')+'.csv'
        if not os.path.exists(os.path.join('Classify/temp/'+key)):
            os.makedirs(os.path.join('Classify/temp/'+key))
        queue = queuefile(uploadname, savename, keycheck, topictypes=topictypes)
        return jsonify({'status': queue, 'savename': savename})

@app.route('/api/classify/assoc', methods=['GET', 'POST'])
def classifyassoc():
    if request.method == 'GET':
        title = 'Upload Association'
        if 'classifykey' in session:
            queuedfile = FileQueue.query.filter_by(key=session['classifykey']).filter(FileQueue.status=='processing').order_by(FileQueue.added.asc()).first()
        else:
            queuedfile = None

        if 'classifykey' in session:
            apikey = ClassifyKey.query.filter_by(key=session['classifykey']).first()
        else:
            apikey = None
        return render_template('classify/uploadassoc.html', title=title, queuedfile=queuedfile, apikey=apikey, catg='assoc')
    elif request.method == 'POST':
        key = request.form['apikey']
        keycheck = ClassifyKey.query.filter_by(key=key).first()
        if not keycheck:
            return jsonify({'error': 'Invalid API key'})
        session['classifykey'] = key
        support = request.form['support']
        confidence = request.form['confidence']
        if not support or not confidence:
            return jsonify({'error': 'Support and Confidence required'})
        if 'file' not in request.files:
            return jsonify({'error': 'Missing file'})
        antqnt = request.form['antqnt']
        if antqnt != 'one' and antqnt != 'many':
            return jsonify({'error': 'Invalid Antecedent Quantity'})
        if 'upformat' in request.form and int(request.form['upformat']) == 1:
            upformat = 1
        else:
            upformat = 2
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Missing file'})
        fileext = file.filename.split('.')[1]
        if fileext != 'csv' and fileext != 'txt':
            return jsonify({'error': 'File extension not supported'})
        uploadname = secure_filename(file.filename.split('.')[0]+'---'+codegen(5)+'.'+file.filename.split('.')[1])
        file.save(os.path.join('Classify/temp/uploads', uploadname))
        savename = uploadname.split('.')[0].split('---')[0]+'-assoc-'+str(datetime.now()).split('.')[0].replace(':', '-')+'.csv'
        if not os.path.exists(os.path.join('Classify/temp/'+key)):
            os.makedirs(os.path.join('Classify/temp/'+key))
        queue = queuefile(uploadname, savename, keycheck, type='assoc', support=float(support), confidence=float(confidence), antqnt=antqnt, upformat=upformat)
        return jsonify({'status': queue, 'savename': savename})

#TODO Display files based on DB catg
@app.route('/api/classify/temp/list/<classifier>')
def listclassifyfiles(classifier):
    key = request.args.get('key')
    if key and ClassifyKey.query.filter_by(key=key).first():
        session['classifykey'] = key
        files = FileQueue.query.filter_by(key=key).filter(FileQueue.save.contains(classifier)).order_by(FileQueue.added.desc()).all()
        '''
        #View files in file system
        files = [f for f in os.listdir(os.path.join('Classify/temp/'+key)) if '-'+classifier+'-' in f]
        files.sort(key=lambda x: os.stat(os.path.join('Classify/temp/'+key, x)).st_mtime)
        files = files[::-1]
        '''
        if classifier != 'assoc':
            return render_template('classify/listfiles.html', files=files, classifier=classifier, key=key)
        else:
            return render_template('classify/listassoc.html', files=files, classifier=classifier, key=key)
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
