#! ./py3env/bin/python3.7
import logging
import os
from pprint import pprint
from slackclient import SlackClient
import time
from library.create_logger import create_logger

"""
bobbot_slack.py
"""

# slack keys and variables
SLACK_VERIFICATION_KEY = os.getenv("SLACK_VERIFICATION_KEY")
SLACK_OAUTH_ACCESS_KEY = os.getenv("SLACK_OAUTH_ACCESS_KEY")
SLACK_BOT_ACCESS_KEY = os.getenv("SLACK_BOT_ACCESS_KEY")
SLACKBOT_ID = 'UF5QHDYCU'
BOT_MENTIONED_STRING = f'<@{SLACKBOT_ID}>'


class Slackbot(object):
    """
    creats a slackbot object capable of logging into slack
    and monitoring messages
    """

    def __init__(self, name, slack_id, channel, verification_key,
                 oauth_key, access_key):
        """
        this function sets variables,
        sets up a slack client, and sets up a logger
        params:
        name: the name of this bot used on Slack
        id: the slack ID of this bot
        verification_key, oath_key, access_key:
            the given secret keys of this bot
            for use with slack api
        """

        self.name = name
        self.id = slack_id
        self.channel = channel
        self.verification_key = verification_key
        self.oauth_key = oauth_key
        self.access_key = access_key
        self.mentioned_string = f'<@{self.id}>'
        self.exit_command = f'{self.mentioned_string} exit'
        self.client = SlackClient(self.access_key)
        self.logger = create_logger(__name__)

    def __enter__(self):
        """Implements SlackClient as a context manager"""
        self.logger.debug('Enter SlackClient')
        return self

    def __exit__(self, type, value, traceback):
        """Implements TwitterClient context manager"""
        if self.client is not None and self.client.server is not None:
            self.client.server.connected = False
        self.logger.debug('Exit Slack Client')

    def on_twitter_data(self, data):
        self.client.rtm_send_message(
            self.channel, "Who wants Ramen or Ramlets?")

    def monitor_stream(self):
        """ Monitor slack rtm feed for messages mentioning the bot
        if the message is an exit message,
        """

        self.logger.info('Monitoring Slack messages...')
        while self.client.server.connected:
            try:
                events = self.client.rtm_read()
                self.monitor_events(list(events))
            except Exception as e:
                self.logger.error(f'Failed to Read Slack Events\n{e}')
            time.sleep(2)
        self.logger.info('Exiting Slack Stream...')

    def monitor_events(self, events):
        for event in events:
            # only look for messages that mention the bot
            if 'message' in event.values() and self.id in event['text']:
                # disconnect if we get an exit message
                if event['text'].strip() == self.exit_command:
                    self.logger.warning('Received Exit Message...')
                    self.client.server.connected = False
                else:
                    # replace mention tag with bot name and log
                    msg = event['text'].replace(
                        self.mentioned_string, f'@{self.name}')

                    self.logger.info(f'Bot was mentioned: {msg}')
                    # send response message in chat
                    try:
                        self.client.rtm_send_message(
                            self.channel, "Who wants Ramen or Ramlets?")
                    except Exception as e:
                        self.logger.error(
                            f'Failed to send response message: {e}')

    def connect_to_stream(self):
        """Continuously monitor slack events for mentions of this bot
        if exit message is received then exit gracefully
        """
        self.logger.info(f'Connecting to Slack Stream as {self.name}...')
        # command to listen to on slack to indicate bot is exiting
        try:
            res = self.client.rtm_connect()
            self.logger.info(
                'Successfully Connected to Slack Stream!')
        except:
            self.logger.error("Connection Failed")
