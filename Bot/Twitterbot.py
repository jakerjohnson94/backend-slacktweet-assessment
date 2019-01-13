#! ./py3env/bin/python3.7
import time
import logging
import os
from dotenv import load_dotenv
import tweepy
import sys
import signal
import json
from datetime import datetime as dt
from threading import Thread
from library.create_logger import create_logger
# get enviornment variables
load_dotenv()
# twitter keys and variables
CONSUMER_API_KEY = os.getenv('TWITTER_CONSUMER_API_KEY')
CONSUMER_SECRET_API_KEY = os.getenv('TWITTER_CONSUMER_SECRET_API_KEY')
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
ACCESS_SECRET_TOKEN = os.getenv('TWITTER_ACCESS_SECRET_TOKEN')
BOT_TWITTER_HANDLE = 'BobBot2018'
# Monkey patch for the tweepy.Stream class!


def _start(self, is_async):
    self.running = True
    if is_async:
        # In this patch we set 'daemon=True' during async thread creation
        self._thread = Thread(
            target=self._run, name='tweepy.Stream', daemon=True)
        self._thread.start()
    else:
        self._run()


class Twitterbot(tweepy.StreamListener):
    """
    this class creates a twitterbot objeect capable of logging into Twitter,
    monitoring/sending messages and subscribing to feeds
    """

    def __init__(self, username, subscriptions):
        self.logger = create_logger(__name__)
        self.username = username

        self.api = self.create_api()

        self.subscriptions = subscriptions

        self.logger.info('Connecting to Twitter stream...')
        # Patch the tweepy.Stream._start() method
        self.logger.warn('Applying monkeypatch to tweepy.Stream class ...')
        tweepy.Stream._start = _start
        self.stream = tweepy.Stream(auth=self.api.auth,
                                    listener=self)

    def on_status(self, status):
        self.logger.info(f'Twitter event: {status.text}')

    def on_disconnect(self, status):
        self.logger.error(f'Disconnected from Twitter Stream. {status}')

    def add_subscription(self, slug):
        self.subscriptions.append(slug)
        self.logger.info('added {slug} to current Twitter subscriptions')
        self.start_stream()

    def create_api(self):
        """
        Logs in to twitter api using bot authorization tokens
        """
        self.logger.info(f'Connecting to Twitter API as {self.username}...')
        try:
            auth = tweepy.OAuthHandler(
                CONSUMER_API_KEY, CONSUMER_SECRET_API_KEY)
            auth.set_access_token(ACCESS_TOKEN,
                                  ACCESS_SECRET_TOKEN)
            return tweepy.API(auth)

        except Exception as e:
            self.logger.error(f'Failed to login to Twitter: {e}')

    def start_stream(self):
        try:
            self.logger.info(f'Monitoring Twitter for {self.subscriptions}...')
            self.stream.filter(track=self.subscriptions, is_async=True)
        except Exception as e:
            self.logger.error(f"Error: {e}")


# log thread ID
# loggin.basic_config
