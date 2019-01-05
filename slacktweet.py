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
from library.BobBotLogger import create_logger
"""
Slackbot Project
"""
__author__ = "Slackbot Team: Jake Johnson and Kyle Meiklejohn"
# get enviornment variables
load_dotenv()
# slack keys
SLACK_VERIFICATION_KEY = os.getenv("SLACK_VERIFICATION_KEY")
SLACK_OAUTH_ACCESS_KEY = os.getenv("SLACK_OAUTH_ACCESS_KEY")
SLACK_BOT_ACCESS_KEY = os.getenv("SLACK_BOT_ACCESS_KEY")
SLACK_BOT_ID = 'UF5QHDYCU'
BOT_MENTIONED_STRING = f'<@{SLACK_BOT_ID}>'
exit_command = f'{BOT_MENTIONED_STRING} exit'

# twitter keys
TWITTER_CONSUMER_API_KEY = os.getenv('TWITTER_CONSUMER_API_KEY')
TWITTER_CONSUMER_SECRET_API_KEY = os.getenv('TWITTER_CONSUMER_SECRET_API_KEY')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET_TOKEN = os.getenv('TWITTER_ACCESS_SECRET_TOKEN')
BOT_TWITTER_HANDLE = 'BobBot2018'

sc = SlackClient(SLACK_BOT_ACCESS_KEY)
bobbot_logger = create_logger()


def raise_exit_flag():
    global exit_flag
    exit_flag = True
    sc.server.connected = False


def signal_handler(sig_num, frame):
    global exit_flag
    global bobbot_logger
    """
    This is a handler for SIGTERM and SIGINT. Other signals can be mapped
    here as well (SIGHUP?)Basically it just sets a global flag, and main()
     will exit it's loop if the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """
    signames = dict((k, v) for v, k in reversed(sorted(
        signal.__dict__.items()))
        if v.startswith('SIG') and not v.startswith('SIG_'))

    raise_exit_flag()
    bobbot_logger.warning(
        f'Received {signames[sig_num]}')


def twitter_login():
    global twitter_stream
    global twitter_api
    bobbot_logger.info(f'Loggin in to Twitter as {BOT_TWITTER_HANDLE}...')
    try:
        auth = tweepy.OAuthHandler(
            TWITTER_CONSUMER_API_KEY, TWITTER_CONSUMER_SECRET_API_KEY)
        auth.set_access_token(TWITTER_ACCESS_TOKEN,
                              TWITTER_ACCESS_SECRET_TOKEN)
        twitter_api = tweepy.API(auth)
        bobbot_logger.info('Twitter Login Success!')
    except:
        bobbot_logger.error('Failed to log into Twitter.')


def monitor_twitter_stream():
    global exit_flag
    global twitter_stream
    tweepyStreamListener = TweepyStreamListener()
    twitter_stream = tweepy.Stream(auth=twitter_api.auth,
                                   listener=tweepyStreamListener)

    twitter_stream.filter(track=[BOT_TWITTER_HANDLE])


def monitor_slack_stream():
    global exit_flag
    events = sc.rtm_read()
    for event in events:
        # only look for messages that mention the bot
        if 'message' in event.values() and SLACK_BOT_ID in event['text']:
            if event['text'].strip() == exit_command:
                raise_exit_flag()

            else:
                # replace mention tag with bot name and log
                msg = event['text'].replace(
                    BOT_MENTIONED_STRING, '@Bobbot')
                bobbot_logger.info(f'Bot was mentioned!\n{msg}')

                # send response message in chat
                post_slack_message(general_channel,
                                   "Who wants Ramen or Ramlets?")


def connect_to_slack_stream():
    """
    continuously monitor slack events for mentions of this bot
    if exit message is received then exit gracefully
    """
    bobbot_logger.info('Connecting to Slack Stream...')
    # command to listen to on slack to indicate bot is exiting
    try:
        sc.rtm_connect()
        bobbot_logger.info('Connected to Slack Stream!')
    except:
        bobbot_logger.error("Connection Failed")


def post_slack_message(channel, text):
    try:
        c = sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=text
        )
    except Exception as error:
        # catch python error
        bobbot_logger.error(f'FAILED TO POST MESSAGE\n{error}')
    if 'error' in c.keys():
        # catch bad server response
        bobbot_logger.error(c['error'])


def main():
    global twitter_stream
    global exit_flag
    """ This is executed when run from the command line """

    bobbot_logger.info('----------------------------\n'
                       'Starting Bobbot\n'
                       '----------------------------')
    # login to twitter
    twitter_login()
    # keep bot open until we close it
    connect_to_slack_stream()
    while not exit_flag:
        monitor_twitter_stream()
        while sc.server.connected:
            monitor_slack_stream()
        time.sleep(1)
    # exit gracefully
    bobbot_logger.info('Shutting Down...')
    logging.shutdown()
    if twitter_stream:
        twitter_stream.disconnect()
    exit(0)


if __name__ == "__main__":
    exit_flag = False
    # setup bobbot_logger

    # slack channel IDs
    global general_channel
    general_channel = 'CCD7MHJD8'

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # setup signal handlers

    main()

# Questions for Piero:
# Firehose vs stream
# duplicate bobbot_logger entries when name provided
# exit flag vs rtm.server.connected / how to handle exit?
# how to structure files
