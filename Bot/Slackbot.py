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
    Creates a slackbot object capable of logging into slack
    and monitoring messages
    """

    def __init__(self, name, channel):
        """
        This function sets variables,
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
        self.slack_methods = {
            "exit": self.handle_exit_command,
            "help": self.handle_help_command,
        }
        self.twitter_commands = ["update", "add", "delete"]

        self.twitterbot = None
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

    def register_twitterbot(self, twitterbot):
        """register method to allow us access
        to our twitterbot from within the slackbot"""
        if twitterbot is not None:
            self.twitterbot = twitterbot
            logger.info(
                f"Registered twitterbot {self.twitterbot.username} to the slackbot"
            )

    def publish_tweet_to_slack(self, data):
        """
        Publish tweets to the output channel
        """
        self.lock.acquire()
        try:
            self.send_message(
                "🐦🐦 Incoming Tweet 🐦🐦\n"
                f"@{data['username']}:"
                f"\n{data['text']}\n\n"
            )
        except Exception as e:
            logger.error(f"Failed to post Twitter event to Slack:\n{e}")
        finally:
            self.lock.release()

    def monitor_stream(self):
        """
        Monitor slack rtm feed for messages mentioning the bot
        if the message is an exit message,
        """
        logger.info("Monitoring Slack messages...")
        while self.client.server.connected:
            # turn on thread lock
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
                    "websocket. Restarting ..."
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
        Monitor slack stream for messages that mention out bots name
        and respond to them accordingly
        """
        for event in events:
            # only look for messages that mention the bot
            if (
                "message" in event.values()
                and "text" in event.keys()
                and self.mentioned_string in event["text"]
            ):
                text = event["text"].strip()
                text_list = text.split(" ")
                command = text_list[1].lower()
                if len(text_list) == 1:
                    self.send_message("`Yes? Please enter a valid command.`")
                if len(text_list) == 2:
                    if command in self.slack_methods.keys():
                        # call appropriate command method
                        self.slack_methods[command]()

                elif len(text_list) > 2:
                    # CRUD commands for twitterbot subs
                    if (
                        command in self.twitter_commands
                        and self.twitterbot is not None
                    ):
                        sub_str = " ".join(text_list[2:])
                        subs = self.parse_subs(sub_str)
                        self.twitterbot.on_slack_command(command, subs, self)

                # else:
                #     # Normal message, respond
                #     self.respond_to_mention(event)

    def parse_subs(self, subs):
        if subs.startswith("["):
            return subs[1:-1].split(",")
        else:
            return subs.split(",")

    def respond_to_mention(self, event):
        """
        Send a response message when bot is mentioned
        in a normal message
        """
        # replace mention tag with bot name and log
        msg = event["text"].replace(self.mentioned_string, f"@{self.name}")

        logger.info(f"Bot was mentioned: {msg}")
        # send response message in chat
        self.send_message("Who wants Ramen or Ramlets?")

    def handle_exit_command(self, *args):
        """Send an exit message upon exiting and close the stream"""
        logger.warning("Received Exit Message...")
        self.send_message("`Shutting Down...`")
        self.close_stream()

    def handle_help_command(self, *args):
        self.send_message(
            "```"
            "Bobbot is an integrated Slack and Twitter Bot capable of"
            "'Subscribing' To keywords on Twitter and publishing them to slack\n"
            "To Interact with the bot, mention @BobBot on Slack followed by a valid command\n"
            "*Basic Commands:*\n"
            "*exit:* close the bot"
            "*help:* bring up this dialogue\n\n"
            "*Subscription Commands:*\n"
            "_(Separate separate subscriptions by commas)_\n"
            "*add <subscriptions>:* add new subscription(s) to the current list\n"
            "*update <subscriptions>:* replace the current subscriptions list\n"
            "*remove <subscriptions>:* remove subscriptions(s) from current"
            " list```"
        )

    def send_message(self, message):
        """
        Send an rtm message on slack
        """
        try:
            self.client.rtm_send_message(self.output_channel, message)
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
        """Disconnect the client server"""
        if self.client and self.client.server and self.client.server.connected:
            try:
                self.client.server.connected = False
            except Exception as e:
                logger.error(f"Tried to close stream, but it failed. {e}")
