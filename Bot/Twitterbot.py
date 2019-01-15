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
from datetime import datetime
from collections import Counter
# get enviornment variables
load_dotenv()
# twitter keys and variables
CONSUMER_API_KEY = os.getenv('TWITTER_CONSUMER_API_KEY')
CONSUMER_SECRET_API_KEY = os.getenv('TWITTER_CONSUMER_SECRET_API_KEY')
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
ACCESS_SECRET_TOKEN = os.getenv('TWITTER_ACCESS_SECRET_TOKEN')
BOT_TWITTER_HANDLE = 'BobBot2018'

# create logger
logger = create_logger(__name__)


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
        self.username = username
        self.subscriptions = subscriptions
        self.event_list = []
        self.api = self.create_api()
        self.slack_func = None
        logger.info('Connecting to Twitter stream...')
        # Patch the tweepy.Stream._start() method
        logger.debug('Applying monkeypatch to tweepy.Stream class ...')
        tweepy.Stream._start = async_stream_start

        # start stream
        self.stream = tweepy.Stream(auth=self.api.auth,
                                    listener=self)
        self.start_time = time.time()

# context manager functions
    def __enter__(self):
        """Implements TwitterClient as a context manager"""
        logger.debug('Enter TwitterClient')
        return self

    def __exit__(self, type, value, traceback):
        """Implements TwitterClient context manager"""
        if self.stream is not None:
            self.stream.disconnect()
        self.get_stream_summary()
        logger.debug('Exit TwitterClient')

    def register_slack_function(self, func):
        if func is not None:
            self.slack_func = func

    def on_slack_command(self, command, subs):
        self.close_stream()
        self.stream = tweepy.Stream(auth=self.api.auth,
                                    listener=self)
        if command == 'update':
            self.update_subscriptions(subs)
        elif command == 'delete':
            self.delete_subscriptions(subs)
        elif command == 'add':
            self.add_subscriptions(subs)

    def on_status(self, status):
        username = status.user.screen_name
        text = status.text
        timestamp = str(datetime.fromtimestamp(
            float(status.timestamp_ms)/1000.0))
        # timestamp = datetime.datetime.fromtimestamp(data[ms_/1000.0)
        self.event_list.append(
            {'username': username, 'text': text, "timestamp": timestamp, })
        logger.info(f'Twitter event: {status.text}')
        if self.slack_func is not None:
            self.slack_func(self.event_list[-1])

    def on_disconnect(self, status):
        logger.error(f'Disconnected from Twitter Stream. {status}')

    def add_subscriptions(self, slugs):
        logger.info('Adding Subscription...')
        self.subscriptions += slugs
        self.start_stream()

    def delete_subscriptions(self, slugs):
        logger.info('Deleting Subscription...')
        for slug in slugs:
            self.subscriptions.pop(self.subscriptions.index(slug))
        self.start_stream()

    def update_subscriptions(self, subscriptions):
        logger.info(f'Updating Twitter Subscriptions...')
        self.subscriptions = subscriptions
        self.start_stream()

    def create_api(self):
        """
        Logs in to twitter api using bot authorization tokens
        """
        logger.info(f'Connecting to Twitter API as {self.username}...')
        try:
            auth = tweepy.OAuthHandler(
                CONSUMER_API_KEY, CONSUMER_SECRET_API_KEY)
            auth.set_access_token(ACCESS_TOKEN,
                                  ACCESS_SECRET_TOKEN)
            return tweepy.API(auth)

        except Exception as e:
            logger.error(f'Failed to login to Twitter: {e}')

    # event statistics
    def set_total_events(self):
        self.total_events = len(self.event_list)
        return self.total_events

    def set_total_run_time(self):
        self.total_run_time = round((time.time() - self.start_time) / 60, 2)
        return self.total_run_time

    def set_top_user(self):
        if self.event_list is not []:
            user_data = [x['username'] for x in self.event_list]
            user_counts = Counter(user_data)
            top_users = sorted(user_counts.most_common(),
                               key=lambda x: x[1], reverse=True)
            if ((len(top_users) > 1 and top_users[0][1] == top_users[1][1]) or
                    not top_users):
                self.top_user = None
            else:
                self.top_user = top_users[0]
            return self.top_user

    def set_events_per_min(self):
        if self.total_events and self.total_run_time:
            self.events_per_min = int(
                float(self.total_events) /
                float(self.total_run_time))
        else:
            logger.error('Attempted to calculate total events'
                         'per minute, but the stream has not ended')
            self.events_per_min = None

        return self.events_per_min

    def get_stream_summary(self):
        self.set_total_events()
        self.set_total_run_time()
        self.set_top_user()
        self.set_events_per_min()

    def create_top_user_str(self):
        if self.top_user:
            user, event_num = self.top_user
            top_user_str = (f'@{user} had the most activity'
                            f' with {event_num} events.')
        else:
            top_user_str = 'Multiple users had the most activity'
        return top_user_str

    def start_stream(self):
        self.subscriptions = list(set(self.subscriptions))
        try:
            logger.info(f'Monitoring Twitter for {self.subscriptions}...')
            self.stream.filter(track=self.subscriptions, is_async=True)
        except Exception as e:
            logger.error(f"Error tracking Twitter Stream: {e}")

    def close_stream(self):
        try:
            self.stream.running = False
        except Exception as e:
            logger.error('Tried to close stream, but it was already closed')
