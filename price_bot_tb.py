# Importing Modules/Libraries
import tweepy
import config
import time
import pandas
from matplotlib import ticker
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
import io

def start_client():
    config.read_config()
    
    api_key = config.CONFIG['api_key']
    api_key_secret = config.CONFIG['api_key_secret']
    access_token = config.CONFIG['access_token']
    access_token_secret = config.CONFIG['access_token_secret']
    bearer_token = config.CONFIG['bearer_token']

    tb_by_basename = config.CONFIG['tb_by_basename']
    
    auth = tweepy.OAuth1UserHandler(
        api_key, api_key_secret, access_token, access_token_secret)

    api = tweepy.API(auth, wait_on_rate_limit=True)

    client = tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=api_key,
        consumer_secret=api_key_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

    return client, api

def plotting(data):
    data['date'] = pandas.to_datetime(data['date'])
    
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


def generate_chart_url(url):
    tb_by_url = config.CONFIG['tb_by_url']

    params = {
        'token': tb_by_url,
        'param': url
    }

    # print("In generate_chart_url")

    url = f'https://api.tinybird.co/v0/pipes/products_by_url.csv'
    response = requests.get(url, params=params)
    data = pandas.read_csv(io.StringIO(response.text))
    if data.empty:
        # print('DataFrame is empty!')
        return False
    else:
        plotting(data)
        return True

def generate_chart_basename(basename):
    tb_by_basename = config.CONFIG['tb_by_basename']

    params = {
        'token': tb_by_basename,
        'param': basename
    }

    # print("In generate_chart_basename")
    url = f'https://api.tinybird.co/v0/pipes/products_by_basename.csv'
    response = requests.get(url, params=params)

    data = pandas.read_csv(io.StringIO(response.text))
    if data.empty:
        # print('DataFrame is empty!')
        return False
    else:
        plotting(data)
        return True

def proc_mention(client, api, tweet):
    if 'urls' in tweet['entities']:
        url = tweet.entities["urls"][0]['expanded_url']
        if "https://tienda.mercadona.es/product/" in url:
            if 'aceite-girasol-refinado-02o-hacendado' in url or not generate_chart_url(url):
                basename = url.split('/')[-1]
                if not generate_chart_basename(basename):
                    # print("Not in DB")
                    message = 'No he encontrado ese producto'
                    client.create_tweet(in_reply_to_tweet_id=tweet.id, text=message)
                    return

            # print(f"sending tweet")
            media = api.media_upload(filename="chart.png")
            message = "Aquí tienes el gráfico"
            client.create_tweet(in_reply_to_tweet_id=tweet.id, text=message, media_ids=[media.media_id])
        else:
            # print("not a mercadona url")
            message = 'No es una url válida'
            client.create_tweet(in_reply_to_tweet_id=tweet.id, text=message)
    else:
        # print("no urls")
        message = 'No has mandado una url'
        client.create_tweet(in_reply_to_tweet_id=tweet.id, text=message)

def proc_mentions(client, api):
    credentials = api.verify_credentials()
    print(f"Connected API 1 as: {credentials.id} {credentials.screen_name}")

    me = client.get_me()
    client_id = me.data.id
    username = me.data.username
    print(f"Connected API 2 as: {client_id} {username}")
    
    initialisation_resp = client.get_users_mentions(client_id)
    
    if initialisation_resp.data:
        start_id = initialisation_resp.meta["newest_id"]
    else:
        start_id = client_id
    
    while True:
        response = client.get_users_mentions(client_id, 
                                            since_id=start_id,
                                            tweet_fields=['entities']
                                            )
        if response.data:
            for tweet in response.data:
                # print(f"tweet: {tweet}")
                proc_mention(client, api, tweet)
                start_id = tweet.id
    
        time.sleep(5)

if __name__ == '__main__':
    client, api = start_client()
    proc_mentions(client, api)
