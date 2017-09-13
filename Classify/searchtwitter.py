import tweepy, csv
from Models.models import FileQueue, db
from config import app

def get_authorization():

    info = {
        'consumer_key': 'kJX1DdEVJgPQ4JXqQhoU8dw4d',
        'consumer_secret': 'VcaXF2aKc9emMR4FTUlmFS8bmOnX9Qk4uEKmocnoQHlG92P1fY',
        'access_token': '427711118-xxUVzdF3mBEYCFEt7J4r65rjknuvJVA1Xqyr6IZS',
        'access_token_secret': 'RuUBhzXFQbZKgimYcy1Oc3IkaeYR5JBeOt7MpmVKXJufY'
        }

    auth = tweepy.OAuthHandler(info['consumer_key'], info['consumer_secret'])
    auth.set_access_token(info['access_token'], info['access_token_secret'])
    return auth


def searchtwitter(keywords, savename, key):
    with app.app_context():
        try:
            api = tweepy.API(get_authorization(), wait_on_rate_limit=True)


            tweet_batch = tweepy.Cursor(api.search,
                               q=keywords,
                               count=100,
                               result_type="recent",
                               include_entities=False,
                               lang="en").items(3000)
            tweets = tweet_batch

            with open('Classify/temp/'+key+'/'+savename, 'w', newline="", encoding='utf-8') as destfile:
                headers = ['Handle', 'Text', 'Created At']
                f = csv.DictWriter(destfile, fieldnames=headers)
                f.writeheader()
                totalcount = 0
                for tweet in tweets:
                    if (not tweet.retweeted) and ('RT @' not in tweet.text) and (keywords.lower() in tweet.text.lower()):
                        totalcount += 1
                        writedata = {}
                        writedata['Handle'] = tweet.author.screen_name
                        writedata['Text'] = tweet.text
                        writedata['Created At'] = tweet.created_at
                        f.writerow(writedata)

            fileq = FileQueue.query.filter_by(key=key).filter(FileQueue.status=='processing').first()

            fileq.status = 'complete'
            fileq.complete = totalcount
            fileq.total = totalcount

            db.session.commit()

        except Exception as e:
            print(e)
            fileq.status = 'error'
            db.session.commit()
