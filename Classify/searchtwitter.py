import tweepy, csv, time
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

def checkKeywords(keywords, text, exact=False):
    if exact:
        if keywords in text:
            return True
        else:
            return False
    else:
        for i in keywords.split(' '):
            if i not in text:
                return False
        return True


def searchtwitter(keywords, savename, key, include_rt=False):
    with app.app_context():

        try:
            fileq = FileQueue.query.filter_by(key=key).filter(FileQueue.status=='processing').first()
            print(fileq.status)
        except AttributeError:
            time.sleep(3)
            fileq = FileQueue.query.filter_by(key=key).filter(FileQueue.status=='processing').first()


        try:
            api = tweepy.API(get_authorization(), wait_on_rate_limit=True)

            tweet_batch = tweepy.Cursor(api.search,
                               q=keywords,
                               count=100,
                               result_type="recent",
                               include_entities=False,
                               lang="en").items(5000)
            tweets = tweet_batch

            with open('Classify/temp/'+key+'/'+savename, 'w', newline="", encoding='utf-8') as destfile:
                headers = ['Id', 'Handle', 'Followers', 'Text', 'Retweets', 'Favorites', 'Created At']

                if include_rt:
                    headers.append('RT')
                    headers.append('Original Id')

                f = csv.DictWriter(destfile, fieldnames=headers)
                f.writeheader()
                totalcount = 0

                if keywords.startswith('"') and keywords.endswith('"'):
                    exact = True
                    keywords = keywords.replace('"', '')
                else:
                    exact = False

                for tweet in tweets:
                    try:
                        rt_status = tweet.retweeted_status
                    except AttributeError:
                        rt_status = None
                    if (((include_rt == False) and (not rt_status)) or (include_rt)) and checkKeywords(keywords, tweet.text.lower(), exact):
                        totalcount += 1
                        writedata = {}
                        writedata['Id'] = tweet.id_str
                        writedata['Handle'] = tweet.author.screen_name
                        writedata['Followers'] = tweet.author.followers_count
                        writedata['Text'] = tweet.text
                        writedata['Retweets'] = tweet.retweet_count
                        writedata['Created At'] = tweet.created_at

                        if include_rt:
                            if (rt_status):
                                writedata['RT'] = 1
                                writedata['Original Id'] = tweet.retweeted_status.id_str
                                writedata['Favorites'] = tweet.retweeted_status.favorite_count
                            else:
                                writedata['RT'] = 0
                                writedata['Original Id'] = tweet.id_str
                                writedata['Favorites'] = tweet.favorite_count
                        else:
                            writedata['Favorites'] = tweet.favorite_count

                        f.writerow(writedata)

                    print(totalcount)


            print('almost done')
            fileq.status = 'complete'
            fileq.complete = totalcount
            fileq.total = totalcount
            db.session.commit()
            print('finished')

        except Exception as e:
            print(e)
            fileq.status = 'error'
            db.session.commit()
