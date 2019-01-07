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


class Slackbot(object):
    """
    creats a slackbot object capable of logging into slack
    and monitoring messages
    """

    def __init__(self, name, slack_id, verification_key,
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
        self.verification_key = verification_key
        self.oauth_key = oauth_key
        self.access_key = access_key
        self.mentioned_string = f'<@{self.id}>'
        self.exit_command = f'{self.mentioned_string} exit'
        self.client = SlackClient(self.access_key)
        self.logger = create_logger(__name__)
        assert self.logger is not None

    def info(self, msg):
        """
        convenience method for logging a message
        with level 'INFO'
        """
        self.logger.info(msg)

    def warning(self, msg):
        """
        convenience method for logging a message
        with level 'WARNING'
        """
        self.logger.warning(msg)

    def error(self, msg):
        """
        convenience method for logging a message
        with level 'ERROR'
        """
        self.logger.error(msg)

    # TODO: cCONVERT old methods to class

    def monitor_stream(self):
        """
        monitor slack rtm feed for messages mentioning the bot
        if the message is an exit message,
        """

        self.info('Monitoring Slack messages...')
        while self.client.server.connected:
            try:
                events = self.client.rtm_read()
                self.parse_events(list(events))
            except Exception as e:
                self.error(f'Failed to Read Slack Events\n{e}')
            time.sleep(2)
        self.info('Exiting Slack Stream...')

    def parse_events(self, events):
        general_channel = '#general'
        for event in events:
            # only look for messages that mention the bot
            if 'message' in event.values() and self.id in event['text']:
                # disconnect if we get an exit message
                if event['text'].strip() == self.exit_command:
                    self.warning('Received Exit Message...')
                    self.client.server.connected = False
                else:
                    # replace mention tag with bot name and log
                    msg = event['text'].replace(
                        self.mentioned_string, self.name)

                    self.info(f'Bot was mentioned:\n{msg}')
                    # send response message in chat
                    try:
                        self.client.rtm_send_message(
                            general_channel, "Who wants Ramen or Ramlets?")
                    except Exception as e:
                        self.error(
                            f'Failed to send response message: {e}')

    def connect_to_stream(self):
        """
        continuously monitor slack events for mentions of this bot
        if exit message is received then exit gracefully
        """
        self.info('Connecting to Slack Stream...')
        # command to listen to on slack to indicate bot is exiting
        try:
            res = self.client.rtm_connect()
            self.info(
                'Successfully Connected to Slack Stream!')
        except:
            self.error("Connection Failed")
