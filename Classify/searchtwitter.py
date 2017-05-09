import csv
from TwitterSearch import *
from Models.models import FileQueue, db
from config import app
import time

time.sleep(1)

def searchtwitter(keywords, savename, key):
    with app.app_context():
        fileq = FileQueue.query.filter_by(key=key).filter(FileQueue.status=='processing').first()

        try:
            tso = TwitterSearchOrder()
            tso.set_keywords(keywords)
            tso.set_language('en')
            tso.set_include_entities(False)


            ts = TwitterSearch(
                consumer_key = 'kJX1DdEVJgPQ4JXqQhoU8dw4d',
                consumer_secret = 'VcaXF2aKc9emMR4FTUlmFS8bmOnX9Qk4uEKmocnoQHlG92P1fY',
                access_token = '427711118-xxUVzdF3mBEYCFEt7J4r65rjknuvJVA1Xqyr6IZS',
                access_token_secret = 'RuUBhzXFQbZKgimYcy1Oc3IkaeYR5JBeOt7MpmVKXJufY'
            )

            with open('Classify/temp/'+key+'/'+savename, 'w', newline="", encoding='Utf-8') as destfile:
                headers = ['Handle', 'Text', 'Created At']
                f = csv.DictWriter(destfile, fieldnames=headers)
                f.writeheader()
                totalcount = 0
                for tweet in ts.search_tweets_iterable(tso):
                    totalcount += 1
                    writedata = {}
                    writedata['Handle'] = tweet['user']['screen_name']
                    writedata['Text'] = tweet['text']
                    writedata['Created At'] = tweet['created_at']
                    f.writerow(writedata)

            fileq.status = 'complete'
            fileq.complete = totalcount
            fileq.total = totalcount

            db.session.commit()

        except:
            fileq.status = 'error'
            db.session.commit()
