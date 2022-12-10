#Twitter sample code
#https://github.com/twitterdev/Twitter-API-v2-sample-code/blob/main/Bookmarks-lookup/bookmarks_lookup.py

#user's lookup
#https://developer.twitter.com/en/docs/twitter-api/users/lookup/migrate/standard-to-twitter-api-v2

#Migrating from Native Enriched data format to v2
#https://developer.twitter.com/en/docs/twitter-api/migrate/data-formats/native-enriched-to-v2

#Get a video URL from Twitter API v2
#https://dev.to/twitterdev/get-a-video-url-from-twitter-api-v2-1713

# Tweets information about flights based on their numbers.
# https://github.com/chilipolygon/FlightTrackBot-Twitter/blob/4e7943485c2c4279f804b3d65f32687eacf7efe6/main.py#L111

# A Twitter bot that tells you information about a flight by it's number or callsign.
# https://github.com/plcnk/TwitterFlightBot

# Bot de procesado de imagenes
# https://github.com/martxelo/yolo-twitterbot/blob/main/main.py

# Original reply bot code
# https://github.com/CreepyD246/twitter-reply-bot-with-tweepy

# Importing Modules/Libraries
import tweepy
import time
import config
import sqlite3
import pandas
import os.path
from matplotlib import ticker
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def start_client():
    # Credentials (Insert your keys and tokens below)
    config.read_config()
    
    api_key = config.CONFIG['api_key']
    api_key_secret = config.CONFIG['api_key_secret']
    access_token = config.CONFIG['access_token']
    access_token_secret = config.CONFIG['access_token_secret']
    bearer_token = config.CONFIG['bearer_token']
    
    auth = tweepy.OAuth1UserHandler(
        api_key, api_key_secret, access_token, access_token_secret)

    api = tweepy.API(auth, wait_on_rate_limit=True)

    print(f"v1: {api.verify_credentials().screen_name}")

    # Connecting to Twitter API
    client = tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=api_key,
        consumer_secret=api_key_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

    return client, api

def generate_chart(basename):
    sql = f"""
        SELECT date,price,name, description
        FROM products
        WHERE 
        url like "%{basename}"
        AND
        date >= "2021-08-01"
        """

    conn = sqlite3.connect(os.path.expanduser("~/scrape-super/db/products.db"))
    data = pandas.read_sql(sql, conn)

    data['date'] = pandas.to_datetime(data['date'])
    data['price'] = pandas.to_numeric(data['price'])
    
    date = data["date"]
    price = data["price"]

    fig, ax = plt.subplots(figsize=(12, 6), layout='constrained')
    ax.plot(date, price, linewidth=2.5, alpha=0.75)
    plt.grid(True)
    title_text = f"{data['name'][0]} {data['description'][0]}"
    ax.set_title(title_text, fontsize=16)
    ax.set_ylabel('Precio (€)')
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %y"))
    
    ax.xaxis.set_minor_locator(mdates.DayLocator(15))
    #ax.xaxis.set_minor_formatter(mdates.DateFormatter("%d"))
    
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.margins(x=0)

    plt.savefig("chart.png")


def proc_mention(client, api, tweet):
    if 'urls' in tweet['entities']:
        url = tweet.entities["urls"][0]['expanded_url']
        if "https://tienda.mercadona.es/product/" in url:
            basename = url.split('/')[-1]
            print(f"generating chart {basename}")
            generate_chart(basename)
            print(f"sending tweet")
            media = api.media_upload(filename="chart.png")
            message = "Aquí tienes el gráfico"
            client.create_tweet(in_reply_to_tweet_id=tweet.id, text=message, media_ids=[media.media_id])
        else:
            print("not a mercadona url")
    else:
        print("no urls")

def proc_mentions(client, api):
    # Bot's unique ID
    me = client.get_me()
    client_id = me.data.id
    username = me.data.username
    print(f"Connected as: {client_id} {username}")
    # This is so the bot only looks for the most recent tweets.
    initialisation_resp = client.get_users_mentions(client_id)
    #print(initialisation_resp)
    #print(f"\n{initialisation_resp.data[0].id} {initialisation_resp.data[0].text}")
    
    if initialisation_resp.data:
        start_id = initialisation_resp.meta["newest_id"]
    else:
        start_id = client_id
    
    # Looking for mentions tweets in an endless loop
    while True:
        response = client.get_users_mentions(client_id, 
                                            since_id=start_id,
                                            tweet_fields=['entities']
                                            )
        #print(f"response.data: {response.data}")
        # Reply Code
        if response.data:
            for tweet in response.data:
                print(f"tweet: {tweet}")
                proc_mention(client, api, tweet)
                start_id = tweet.id
    
        # Delay (so the bot doesn't search for new tweets a bucn of time each second)
        time.sleep(5)

if __name__ == '__main__':
    client, api = start_client()
    proc_mentions(client, api)
