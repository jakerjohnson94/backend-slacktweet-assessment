#! ./py3env/bin/python3.7
import time
import logging
import os
from dotenv import load_dotenv
import tweepy
import sys

from library.create_logger import create_logger
# get enviornment variables


logger = create_logger('Twitterbot')


class TwitterStreamListener(tweepy.StreamListener):
    """
    overwrite tweepystreamlistener to monitor our bot's twitter stream
    """

    def on_status(self, status):
        logger.info(status.text)


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
        self.logger = logger
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

        tweepyStreamListener = TwitterStreamListener()
        self.logger.info('Connecting to Twitter stream...')

        if self.logged_in == True:
            try:
                self.stream = tweepy.Stream(auth=self.api.auth,
                                            listener=tweepyStreamListener)
                self.logger.info('Connected to Twitter Stream.')
            except Exception as e:
                self.logger.error(f'Error Connecting to Twitter Stream.{e}')
                time.sleep(10)
            try:
                self.stream.filter(track=[self.username], is_async=True)
            except Exception as e:
                self.logger.error(f'An error occured while monitoring the Twitter stream: {e}')
                time.sleep(10)
        else:
            raise SystemExit
