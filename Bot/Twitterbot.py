#! ./py3env/bin/python3.7
import time
import logging
import os
from dotenv import load_dotenv
import tweepy
import sys
import signal
from tweepy.api import API
import json
from datetime import datetime as dt
from library.create_logger import create_logger
# get enviornment variables


class Twitterbot(tweepy.StreamListener):
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
        self.subscriptions = []
        self.stream = None

    def on_status(self, status):
        self.logger.info(f'Twitter event: {status.text}')
        return self.stream.running

    def on_disconnect(self, status):
        self.logger.error(f'Disconnected from Twitter Stream. {status}')

    def add_subscription(self, slug):
        self.subscriptions.append(slug)
        self.logger.info('added {slug} to current Twitter subscriptions')
        self.monitor_stream()

    def login(self):
        """
        Logs in to twitter api using bot authorization tokens
        """
        self.logger.info(f'Logging in to Twitter as {self.username}...')
        try:
            auth = tweepy.OAuthHandler(
                self.api_key, self.secret_api_key)
            auth.set_access_token(self.access_token,
                                  self.secret_access_token)
            self.api = API(auth)
            self.logger.info('Twitter Login Success')

        except Exception as e:
            self.logger.error(f'Failed to login to Twitter: {e}')

    def start_stream(self, **kwargs):
        self.logger.info('Monitoring Twitter Stream...')
        try:
            self.stream.filter(**kwargs)
        except Exception as e:
            self.logger.error(f"Error: {e}")

    def monitor_stream(self):
        """
        listen to twitter stream for messages containing the bot's twitter handle
        """

        self.logger.info('Connecting to Twitter stream...')
        self.stream = tweepy.Stream(auth=self.api.auth,
                                    listener=self)
        self.logger.info('Successfully Connected to Twitter Stream')
        self.start_stream(track=self.subscriptions, is_async=True)
