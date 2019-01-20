#! ./py3env/bin/python3.7
import os
from slackclient import SlackClient
from library.create_logger import create_logger
import threading
import time
from websocket import WebSocketConnectionClosedException

"""
Slackbot.py
"""
# get enviornment variables
ACCESS_KEY = os.getenv("SLACK_BOT_ACCESS_KEY")
SLACKBOT_ID = "UF5QHDYCU"
BOT_MENTIONED_STRING = f"<@{SLACKBOT_ID}>"
logger = create_logger(__name__)


class Slackbot(object):
    """
    creats a slackbot object capable of logging into slack
    and monitoring messages
    """

    def __init__(self, name, channel):
        """
        this function sets variables,
        sets up a slack client, and sets logger
        params:
        name: the name of this bot used on Slack
        id: the slack ID of this bot
        verification_key, oath_key, access_key:
            the given secret keys of this bot
            for use with slack api
        """
        self.name = name
        self.id = SLACKBOT_ID
        self.output_channel = channel
        self.mentioned_string = f"<@{self.id}>"
        self.exit_command = f"{self.mentioned_string} exit"
        self.twitter_func = None
        self.lock = threading.Lock()
        try:
            self.client = SlackClient(ACCESS_KEY)
        except Exception as e:
            logger.error(f"failed to connect to Slack Client:\n{e}")

    def __enter__(self):
        """Implements SlackClient as a context manager"""
        logger.debug("Enter SlackClient")
        return self

    def __exit__(self, type, value, traceback):
        """Implements TwitterClient context manager"""
        self.close_stream()
        logger.debug("Exit Slack Client")

    def register_twitter_func(self, func):
        """
        function to register a twitter func
        once set, we can pass data to a twitterbot
        """
        if func is not None:
            self.twitter_func = func

    def on_twitter_data(self, data):
        """
        publish tweets to the output channel
        """
        self.lock.acquire()
        try:
            self.send_message(
                self.output_channel,
                (
                    f"🐦🐦 Incoming Tweet 🐦🐦\n"
                    f"{data['timestamp']} - "
                    f"@{data['username']}:"
                    f"\n{data['text']}\n\n"
                ),
            )
        except Exception as e:
            logger.error(f"Failed to post Twitter event to Slack:\n{e}")
        finally:
            self.lock.release()

    def monitor_stream(self):
        """ Monitor slack rtm feed for messages mentioning the bot
        if the message is an exit message,
        """
        logger.info("Monitoring Slack messages...")
        while self.client.server.connected:
            self.lock.acquire()
            try:
                events = self.client.rtm_read()
            except WebSocketConnectionClosedException:
                # If remote host closed the connection or some network error
                # happened, this exception will be raised.
                # This sometimes happens in the rtm_read() function.
                # See https://github.com/slackapi/python-slackclient/issues/36
                error_str = (
                    "The Slack RTM host unexpectedly closed its"
                    "websocket.\nRestarting ..."
                )
                logger.error(error_str, exc_info=True)
                time.sleep(2)
                continue
            except Exception as e:
                logger.error(f"{e}")
            finally:
                self.lock.release()
                if events:
                    self.monitor_events(list(events))
        logger.info("Exiting Slack Stream...")

    def monitor_events(self, events):
        """
        monitor slack stream for messages that mention out bots name
        and respond to them accordingly
        """
        for event in events:
            # only look for messages that mention the bot
            if (
                "message" in event.values()
                and "text" in event.keys()
                and self.id in event["text"]
            ):
                text = event["text"].strip()
                text_list = text.split(" ")

                if text == self.exit_command:
                    # disconnect if we get an exit message
                    self.handle_exit_command(self.output_channel)

                elif self.twitter_func is not None and len(text_list) > 2:
                    # CRUD commands for twitterbot subs
                    command = text_list[1]
                    subs = text_list[2:]
                    self.twitter_func(command, subs, self)

                else:
                    # Normal message, respond
                    self.respond_to_mention(event)

    def respond_to_mention(self, event):
        """
        Send a response message when bot is mentioned
        in a normal message
        """
        # replace mention tag with bot name and log
        msg = event["text"].replace(self.mentioned_string, f"@{self.name}")

        logger.info(f"Bot was mentioned: {msg}")
        # send response message in chat
        self.send_message(self.output_channel, "Who wants Ramen or Ramlets?")

    def handle_exit_command(self, channel):
        """send an exit message upon exiting and close the stream"""
        logger.warning("Received Exit Message...")
        self.send_message(channel, "Okay. Bye.")
        self.close_stream()

    def send_message(self, channel, message):
        """
        send an rtm message on slack
        """
        try:
            self.client.rtm_send_message(channel, message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def connect_to_stream(self):
        """Continuously monitor slack events for mentions of this bot
        if exit message is received then exit gracefully
        """
        logger.info(f"Connecting to Slack Stream as {self.name}...")
        # command to listen to on slack to indicate bot is exiting
        try:
            self.client.rtm_connect()
            logger.info("Successfully Connected to Slack Stream!")
        except Exception as e:
            logger.error(f"Connection to Slack Stream Failed. {e}")

    def close_stream(self):
        """
        disconnect the client server
        """
        if self.client and self.client.server and self.client.server.connected:
            try:
                self.client.server.connected = False
            except Exception as e:
                logger.error(f"Tried to close stream, but it failed. {e}")
