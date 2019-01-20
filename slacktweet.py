#! /usr/local/bin/python3

import logging
import signal
import argparse
from library.create_logger import create_logger
from Bot.Slackbot import Slackbot
from Bot.Twitterbot import Twitterbot


"""
Slacktweet Project
"""
__author__ = "Slackbot Team: Jake Johnson and Kyle Meiklejohn"

# setup logger
logger = create_logger(__name__)


def signal_handler(sig_num, frame):
    global slackbot
    global twitterbot
    """
    This is a handler for SIGTERM and SIGINT. Other signals can be mapped
    here as well
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used (needed for signal call)
    :return None
    """
    signames = dict(
        (k, v)
        for v, k in reversed(sorted(signal.__dict__.items()))
        if v.startswith("SIG") and not v.startswith("SIG_")
    )

    logger.warning(f"Received {signames[sig_num]}")
    exit_bots(twitterbot, slackbot)


def create_args_parser():
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument(
        "subscriptions",
        nargs="+",
        help=(
            "list of strings to subscribe to on"
            "Twitter. These include usernames,"
            "hashtags, and any other text"
        ),
    )
    parser.add_argument("--channel", help=("Name of slack channel to post in"))
    args = parser.parse_args()
    return (parser, args)


def exit_bots(twitterbot, slackbot):
    if twitterbot.stream.running:
        twitterbot.close_stream()
    slackbot.close_stream()


def main(args):
    global slackbot
    global twitterbot
    """
    This connects to twitter and slack clients and monitors
    both streams for messages mentioning our bot.
    """
    channel = args.channel if args.channel else "#bobbot-twitter-stream"
    logger.info(
        "\n----------------------------\n"
        "Starting Bobbot\n"
        "----------------------------\n"
    )

    # async twitter stream monitor\
    with Twitterbot(
        username="Bobbot2018", subscriptions=args.subscriptions
    ) as twitterbot:
        with Slackbot("Bobbot", channel) as slackbot:

            twitterbot.register_slack_function(slackbot.on_twitter_data)
            slackbot.register_twitter_func(twitterbot.on_slack_command)
            twitterbot.start_stream()
            slackbot.connect_to_stream()
            slackbot.monitor_stream()

    # exit gracefully
    logger.warning("Shutting Down...")

    logger.info(
        "\n----------------------------\n"
        "Bobbot Closed\n"
        f"Gathered {twitterbot.total_events} Event(s) in"
        f" {twitterbot.total_run_time} minutes\n"
        f"An average of {twitterbot.events_per_min}"
        f" Tweets per minute\n"
        f"{twitterbot.create_top_user_str()}\n"
        "----------------------------\n"
    )
    logging.shutdown()
    raise SystemExit


if __name__ == "__main__":
    """ This is executed when run from the command line """
    # setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    parser, args = create_args_parser()

    args.subscriptions = [str(sub) for sub in args.subscriptions]
    main(args)
