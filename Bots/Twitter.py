#! ./py3env/bin/python3.7
import time
import logging
import signal
import os
import argparse
import requests
from pprint import pprint
from slackclient import SlackClient
from dotenv import load_dotenv
import tweepy

from library.TweepyStreamListener import TweepyStreamListener
from library.create_logger import create_logger
# get enviornment variables
load_dotenv()
# twitter keys and variables
TWITTER_CONSUMER_API_KEY = os.getenv('TWITTER_CONSUMER_API_KEY')
TWITTER_CONSUMER_SECRET_API_KEY = os.getenv('TWITTER_CONSUMER_SECRET_API_KEY')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET_TOKEN = os.getenv('TWITTER_ACCESS_SECRET_TOKEN')
BOT_TWITTER_HANDLE = 'BobBot2018'


class Twitterbot(object):
    """
    this class creates a twitterbot objeect capable of logging into Twitter,
    monitoring/sending messages and subscribing to feeds
    """

    def __init__(self, username, api_key, secret_api_key, access_token,
                 secret_access_token):
        self.username = username
        self.api_key = api_key
        self.secret_api_key = secret_api_key
        self.access_token = access_token
        self.secret_access_token = secret_access_token
        self.logger = create_logger(__name__)
        self.logged_in = False

    def login(self):
        """
        Logs in to twitter api using bot authorization tokens
        """
        self.logger.info(f'Loggin in to Twitter as {self.username}...')
        try:
            auth = tweepy.OAuthHandler(
                self.api_key, self.secret_api_key)
            auth.set_access_token(self.access_token,
                                  self.secret_access_token)
            self.api = tweepy.API(auth)
            self.logged_in = True
            self.logger.info('Twitter Login Success!')
        except Exception as e:
            self.logger.error(f'Failed to log into Twitter: {e}')

    def monitor_stream(self):
        """
        listen to twitter stream for messages containing the bot's twitter handle
        """
        tweepyStreamListener = TweepyStreamListener()
        self.logger.info('Monitoring Twitter Stream...')
        try:
            self.stream = tweepy.Stream(auth=self.api.auth,
                                        listener=tweepyStreamListener)
            # twitter_stream.filter(is_async=True)
        except Exception as e:
            self.logger.error(f'An error occured while monitoring the Twitter stream: {e}')
