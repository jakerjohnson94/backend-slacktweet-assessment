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
from Bot.Slackbot import Slackbot
from Bot.Twitterbot import Twitterbot
from datetime import datetime as dt
from collections import Counter
"""
Slacktweet Project
"""
__author__ = "Slackbot Team: Jake Johnson and Kyle Meiklejohn"
# get enviornment variables
load_dotenv()
#comment for github
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
logger = create_logger(__file__)


def signal_handler(sig_num, frame):
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
    exit_bots(twitterbot, slackbot)


def create_args_parser():
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument("subscriptions",
                        nargs='+',
                        help=("list of strings to subscribe to on"
                              "Twitter. These include usernames,"
                              "hashtags, and any other text"))

    # Specify output of "--version"
    return parser


def exit_bots(twitterbot, slackbot):
    if twitterbot.stream.running:
        twitterbot.close_stream()
    if slackbot.client.server.connected:
        slackbot.client.server.connected = False


def main(subscriptions):
    global twitterbot
    global slackbot
    """
    This connects to twitter and slack clients and monitors
    both streams for messages mentioning our bot.
    """
    logger.info('\n----------------------------\n'
                'Starting Bobbot\n'
                '----------------------------\n')

    # async twitter stream monitor\
    with Twitterbot(username='Bobbot2018',
                    subscriptions=subscriptions) as twitterbot:
        with Slackbot('Bobbot', SLACKBOT_ID, '#bobbot-twitter-stream',
                      SLACK_VERIFICATION_KEY, SLACK_OAUTH_ACCESS_KEY,
                      SLACK_BOT_ACCESS_KEY) as slackbot:
            # setup cients
            twitterbot.register_slack_function(slackbot.on_twitter_data)
            slackbot.register_twitter_func(
                twitterbot.on_slack_command)
            twitterbot.start_stream()
            slackbot.connect_to_stream()
            slackbot.monitor_stream()

    # exit gracefully
    logger.warning('Shutting Down...')

    logger.info('\n----------------------------\n'
                'Bobbot Closed\n'
                f'Gathered {twitterbot.total_events} Event(s) in'
                f' {twitterbot.total_run_time} minutes\n'
                f'An average of {twitterbot.events_per_min}'
                f' Tweets per minute\n'
                f'{twitterbot.create_top_user_str()}\n'
                '----------------------------\n')
    logging.shutdown()
    raise SystemExit


if __name__ == "__main__":
    """ This is executed when run from the command line """
    # setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    parser = create_args_parser()
    args = parser.parse_args()
    logger.debug(args)
    subs = [str(sub) for sub in args.subscriptions]
    logger.debug(subs)
    main(subs)
