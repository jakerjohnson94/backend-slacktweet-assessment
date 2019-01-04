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
load_dotenv()
"""
Slackbot Project
"""

__author__ = "Slackbot Team: Jake Johnson and Kyle Meiklejohn"

SLACK_VERIFICATION_KEY = os.getenv("SLACK_VERIFICATION_KEY")
SLACK_OAUTH_ACCESS_KEY = os.getenv("SLACK_OAUTH_ACCESS_KEY")
SLACK_BOT_ACCESS_KEY = os.getenv("SLACK_BOT_ACCESS_KEY")
BOT_ID = 'UF5QHDYCU'
BOT_MENTIONED_STRING = f'<@{BOT_ID}>'
sc = SlackClient(SLACK_BOT_ACCESS_KEY)
exit_flag = False


def post_message(channel, text):
    try:
        c = sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=text
        )
    except Exception as e:
        logger.error('FAILED TO POST MESSAGE')
    if 'error' in c.keys():
        logger.error(c['error'])


def create_logger():
    """
    Settup logger level and format
    """
    # create logger
    logger = logging.getLogger('BobBot')
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    # # create formatter
    # formatter = logging.Formatter(
    #     '%(asctime)s  %(levelname)s:  %(message)s',
    #     datefmt='%Y-%m-%d  %H:%M:%S')
    # # add formatter to ch
    # ch.setFormatter(formatter)
    # # add ch to logger
    # logger.addHandler(ch)

    return logger


def signal_handler(sig_num, frame):
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
    logger.warning(
        '\nReceived {}\n\n'.format(signames[sig_num]))

    sc.server.connected = False


def main():
    global exit_flag

    # command to listen to on slack to indicate bot is exiting
    exit_command = f'{BOT_MENTIONED_STRING} exit'

    # slack channel IDs
    general_channel = 'CCD7MHJD8'

    if sc.rtm_connect():
        while sc.server.connected is True:
            # continuously monitor slack events for mentions of this bot
            # if exit message is received then exit gracefully
            events = sc.rtm_read()
            for event in events:
                if 'message' in event.values() and BOT_ID in event['text']:
                    if event['text'].strip() == exit_command:
                        print('Exit message received...')
                        sc.server.connected = False
                    else:

                        # replace mention tag with bot name and log
                        msg = event['text'].replace(
                            BOT_MENTIONED_STRING, '@Bobbot')
                        logger.info(f'Bot was mentioned!\n{msg}')

                        # send response message in chat
                        post_message(general_channel,
                                     "Who wants Ramen or Ramlets?")
            time.sleep(1)
    else:
        logger.error("Connection Failed")


if __name__ == "__main__":
    """ This is executed when run from the command line """

    # setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # setup logger
    global logger
    logger = create_logger()

    # keep bot open until we close it

    main()

    # exit gracefully
    logger.info('Shutting Down...')
    exit(1)
