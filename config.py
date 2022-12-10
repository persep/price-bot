from configparser import ConfigParser

CONFIG = {}


def read_config():

    global CONFIG

    config = ConfigParser(interpolation=None)
    config.read('config.ini')

    CONFIG['api_key'] = config['credentials']['api_key']
    CONFIG['api_key_secret'] = config['credentials']['api_key_secret']
    CONFIG['access_token'] = config['credentials']['access_token']
    CONFIG['access_token_secret'] = config['credentials']['access_token_secret']
    CONFIG['bearer_token'] = config['credentials']['bearer_token']

    CONFIG['tb_by_url'] = config['credentials']['tb_by_url']
    CONFIG['tb_by_basename'] = config['credentials']['tb_by_basename']
    