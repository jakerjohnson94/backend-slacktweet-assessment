#! ./py3env/bin/python3.7
import time
import logging
import os
from dotenv import load_dotenv
import tweepy
import sys
import signal
import json
from pprint import pprint
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


def async_stream_start(self, is_async):
    """
    Monkey patch for the tweepy.Stream class!
    to allow immediate termination of the async stream listener thread
    """
    self.running = True
    if is_async:
        # In this patch we set 'daemon=True' during async thread creation
        # this allows us to kill the entire thread immediately when we exit
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
        self.subscriptions = subscriptions
        self.data_dict = dict()
        self.api = self.create_api()

        self.logger.info('Connecting to Twitter stream...')
        # Patch the tweepy.Stream._start() method
        self.logger.debug('Applying monkeypatch to tweepy.Stream class ...')
        tweepy.Stream._start = async_stream_start

        # start stream
        self.stream = tweepy.Stream(auth=self.api.auth,
                                    listener=self)

    def __enter__(self):
        """Implements TwitterClient as a context manager"""
        self.logger.debug('Enter TwitterClient')
        return self

    def __exit__(self, type, value, traceback):
        """Implements TwitterClient context manager"""
        if self.stream is not None:
            self.stream.disconnect()
        self.logger.debug('Exit TwitterClient')

    def register_slack_function(self, func):
        if func is not None:
            self.slack_func = func

    def on_status(self, status):
        data = status._json
        username = data['user']['screen_name']
        timestamp = data['timestamp_ms']
        text = data['text']
        if data['user']['name'] not in self.data_dict.keys():
            self.data_dict[username] = {"messages": [
                {"time": timestamp, "text": text}]}
        else:
            self.data_dict[username]["messages"].append(
                {"time": timestamp, "text": text})
        self.logger.info(f'Twitter event: {status.text}')

    def on_disconnect(self, status):
        self.logger.error(f'Disconnected from Twitter Stream. {status}')

    def add_subscription(self, slug):
        if slug in self.subscriptions:
            self.subscriptions.append(slug)
            self.logger.info(f'added {slug} to current Twitter subscriptions.')
            self.start_stream()
        else:
            self.logger.error(f'{slug} is already subscribed to')

    def delete_subscription(self, slug):
        if slug in self.subscriptions:
            self.subscriptions.pop(slug)
            self.logger.info(f'Removed {slug} from current Twitter'
                             'subscriptions.')
            self.start_stream()
        else:
            self.logger.error(f'Failed to delete Twitter Subscription: {slug}'
                              'was not found in the current stream'
                              'subscriptions.')

    def update_subscriptions(self, subscriptions):
        self.logger.info(f'Updating Twitter Subscriptions...')
        self.subscriptions = subscriptions
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
