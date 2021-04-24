from leia import SentimentIntensityAnalyzer
import tweepy
import configparser
import os
import sys
import sqlite3
import traceback
import time
from urllib3.exceptions import ProtocolError

config = configparser.ConfigParser()
dir_path = os.path.abspath(os.getcwd())
config_file = os.path.join(dir_path, "config.cfg")
config.read_file(open(config_file))

# TWITTER API
API_KEY = config.get("TWITTER", "API_KEY")
API_KEY_SECRET = config.get("TWITTER", "API_KEY_SECRET")
ACCESS_TOKEN = config.get("TWITTER", "ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = config.get("TWITTER", "ACCESS_TOKEN_SECRET")

auth = tweepy.OAuthHandler(API_KEY, API_KEY_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth, wait_on_rate_limit=True)

# DATABASE
DB_NAME = config.get("DATABASE", "DB_NAME")
TABLE_NAME = config.get("DATABASE", "TABLE_NAME")
TABLE_ATTRIBUTES = config.get("DATABASE", "TABLE_ATTRIBUTES")
con = sqlite3.connect(DB_NAME)

def create_table():
    try:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS {} ({})".format(
            TABLE_NAME, TABLE_ATTRIBUTES))
        cur.execute("CREATE INDEX IF NOT EXISTS pk_index ON tweets(id_str)")
        cur.execute("CREATE INDEX IF NOT EXISTS created_at_index ON tweets(created_at)")
        con.commit()
        cur.close()
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))

class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        if status.retweeted or status.text.startswith('RT @'):
            return True

        #print(status.text)
        # Extract attributes from each tweet
        id_str = status.id_str
        created_at = status.created_at
        user_name = status.user.screen_name
        text = str(status.text)
        entities = str(status.entities)
        user_created_at = status.user.created_at
        user_location = status.user.location
        user_description = status.user.description
        user_followers_count = status.user.followers_count
        longitude = None
        latitude = None
        if status.coordinates:
            longitude = status.coordinates['coordinates'][0]
            latitude = status.coordinates['coordinates'][1]

        retweet_count = status.retweet_count
        favorite_count = status.favorite_count

        # Compute sentiment polarities
        s = SentimentIntensityAnalyzer()
        polarity_scores = s.polarity_scores(status.text)
        neg_score = polarity_scores['neg']
        neu_score = polarity_scores['neu']
        pos_score = polarity_scores['pos']
        compound_score = polarity_scores['compound']
        sentiment = classify_sentiment(compound_score)

        # Save data
        try:
            with con:
                cur = con.cursor()
                sql = """INSERT INTO {} (id_str, created_at, text, entities,
                        user_created_at, user_location, user_description,
                        user_followers_count, longitude, latitude, retweet_count, 
                        favorite_count, neg_score, neu_score, pos_score, compound_score, sentiment)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""".format(TABLE_NAME)

                val = (id_str, created_at, text, entities, user_created_at, user_location,
                       user_description, user_followers_count, longitude, latitude,
                       retweet_count, favorite_count, neg_score, neu_score, pos_score, compound_score, sentiment)
                cur.execute(sql, val)
                con.commit()
                cur.close()
                time.sleep(1)

        except sqlite3.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def on_error(self, status_code):
        if status_code == 420:
            # return False to disconnect the stream
            return False


def classify_sentiment(score):
    if score >= 0.05:
        return 'positive'
    elif score <= -0.05:
        return 'negative'
    else:
        return 'neutral'


def streamtweets():
    streamlistener = MyStreamListener()
    myStream = tweepy.Stream(auth=api.auth, listener=streamlistener)
    while True:
        try:
            myStream.filter(track=["flamengo"])
        except (ProtocolError, AttributeError):
            continue

if __name__ == '__main__':
    create_table()
    streamtweets()
