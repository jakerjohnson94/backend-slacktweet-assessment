#! ./py3env/bin/python3.7
import os
import argparse
import requests
from pprint import pprint
from slackclient import SlackClient
import signal
import logging
import time
"""
Slackbot Project
"""

__author__ = "Slackbot Team: Jake Johnson and Kyle Meiklejohn"

SLACK_VERIFICATION_KEY = os.getenv("SLACK_VERIFICATION_KEY")
SLACK_OAUTH_ACCESS_KEY = os.getenv("SLACK_OAUTH_ACCESS_KEY")
SLACK_BOT_ACCESS_KEY = os.getenv("SLACK_BOT_ACCESS_KEY")
BOT_ID = 'UF5QHDYCU'
bot_mentioned_string = f'<@{BOT_ID}>'
sc = SlackClient(SLACK_BOT_ACCESS_KEY)


def post_message(general_channel, text):
    sc.api_call(
        "chat.postMessage",
        general_channel=general_channel,
        text=text
    )


def create_logger():
    """
    Settup logger level and format
    """
    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter(
        '%(asctime)s  %(levelname)s:  %(message)s',
        datefmt='%Y-%m-%d  %H:%M:%S')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

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
        '\nReceived {}\n\nShutting Down...'.format(signames[sig_num]))
    sc.server.connected = False


def main():

    # command to listen to on slack to indicate bot is exiting
    exit_command = f'{bot_mentioned_string} exit'

    # slack channel IDs
    general_channel = 'CCD7MHJD8'

    if sc.rtm_connect():
        while sc.server.connected is True:
            # continuously monitor slack events for mentions of this bot
            # if exit message is received then exit gracefully
            event = sc.rtm_read()
            if type(event) is list and event != [] and 'message' in event[0].values() and BOT_ID in event[0]['text']:
                if event[0]['text'].strip() == exit_command:
                    print('Exit message received...')
                    exit_flag = True
                else:
                    # replace mention tag with bot name and log
                    msg = event[0]['text'].replace(
                        '<@UF5QHDYCU>', '@Bobbot')
                    logger.info('Bot was mentioned!')
                    logger.info(msg)

                    # send response message in chat
                    post_message(general_channel, "Who wants Ramen?")
            time.sleep(1)
    else:
        print ("Connection Failed")


if __name__ == "__main__":
    """ This is executed when run from the command line """
    global exit_flag
    exit_flag = False
    # setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # setup logger
    global logger
    logger = create_logger()

    # keep bot open until we close it
    while not exit_flag:
        main()

    # exit gracefully
    logger.info('Shutting Down...')
    exit()
