#! ./py3env/bin/python3.7
import time
import logging
import signal
import os
import argparse
import sys
from pprint import pprint
from slackclient import SlackClient
from dotenv import load_dotenv
import tweepy
from library.create_logger import create_logger
from Bots.Slack import Slackbot
from Bots.Twitter import Twitterbot

"""
Slacktweet Project
"""
__author__ = "Slackbot Team: Jake Johnson and Kyle Meiklejohn"
# get enviornment variables
load_dotenv()

# twitter keys and variables
TWITTER_CONSUMER_API_KEY = os.getenv('TWITTER_CONSUMER_API_KEY')
TWITTER_CONSUMER_SECRET_API_KEY = os.getenv('TWITTER_CONSUMER_SECRET_API_KEY')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET_TOKEN = os.getenv('TWITTER_ACCESS_SECRET_TOKEN')
BOT_TWITTER_HANDLE = 'BobBot2018'

# slack keys and variables
SLACK_VERIFICATION_KEY = os.getenv("SLACK_VERIFICATION_KEY")
SLACK_OAUTH_ACCESS_KEY = os.getenv("SLACK_OAUTH_ACCESS_KEY")
SLACK_BOT_ACCESS_KEY = os.getenv("SLACK_BOT_ACCESS_KEY")
SLACKBOT_ID = 'UF5QHDYCU'
BOT_MENTIONED_STRING = f'<@{SLACKBOT_ID}>'

# setup logger
logger = create_logger('main')

# set exit flag to start
exit_flag = False


def signal_handler(sig_num, frame):
    global exit_flag
    global logger
    global slackbot
    global twitterbot
    """
    This is a handler for SIGTERM and SIGINT. Other signals can be mapped
    here as well
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used (needed for signal call)
    :return None
    """
    signames = dict((k, v) for v, k in reversed(sorted(
        signal.__dict__.items()))
        if v.startswith('SIG') and not v.startswith('SIG_'))

    logger.warning(
        f'Received {signames[sig_num]}')
    set_exit_flag(slackbot, twitterbot)


def set_exit_flag(slackbot, tweetbot):
    global exit_flag
    slackbot.client.server.connected = False
    tweetbot.logged_in = False
    exit_flag = True


def main(slackbot, twitterbot):
    # global twitter_stream
    # global exit_flag
    # global twitter_api
    """
    This connects to twitter and slack clients and monitors
    both streams for messages mentioning our bot.
    """
    logger.info('\n----------------------------\n'
                'Starting Bobbot\n'
                '----------------------------\n')

    slackbot.connect_to_stream()
    twitterbot.login()

    # async twitter stream monitor

    twitterbot.monitor_stream()
    time.sleep(60)

    slackbot.monitor_stream()

    # exit gracefully
    logger.info('Shutting Down...')

    logging.shutdown()

    raise SystemExit


if __name__ == "__main__":
    """ This is executed when run from the command line """
    # setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # setup cients
    slackbot = Slackbot('Bobbot', SLACKBOT_ID, SLACK_VERIFICATION_KEY,
                        SLACK_OAUTH_ACCESS_KEY, SLACK_BOT_ACCESS_KEY)
    twitterbot = Twitterbot(BOT_TWITTER_HANDLE, TWITTER_CONSUMER_API_KEY,
                            TWITTER_CONSUMER_SECRET_API_KEY, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET_TOKEN)
    main(slackbot, twitterbot)

# Questions for Piero:
# Firehose vs stream
# duplicate logger entries when name provided
# exit flag vs rtm.server.connected / how to handle exit?
# how to structure files
