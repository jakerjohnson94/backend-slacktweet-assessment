#! /usr/local/bin/python3
import time
import os
import tweepy
from threading import Thread
from library.create_logger import create_logger
from datetime import datetime
from collections import Counter

# twitter keys and variables
CONSUMER_API_KEY = os.getenv("TWITTER_CONSUMER_API_KEY")
CONSUMER_SECRET_API_KEY = os.getenv("TWITTER_CONSUMER_SECRET_API_KEY")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET_TOKEN = os.getenv("TWITTER_ACCESS_SECRET_TOKEN")
BOT_TWITTER_HANDLE = "BobBot2018"

# create logger
logger = create_logger(__name__)


def async_stream_start(self, is_async):
    """
    Monkey patch for the tweepy.Stream
    to allow immediate termination of the async stream listener thread
    """
    self.running = True

    if is_async:
        # In this patch we set 'daemon=True' during async thread creation
        # this allows us to kill the entire thread immediately when we exit
        self._thread = Thread(target=self._run, name="tweepy.Stream", daemon=True)
        self._thread.start()
    else:
        self._run()


class Twitterbot(tweepy.StreamListener):
    """
    Creates a twitterbot objeect capable of logging into Twitter,
    monitoring/sending messages and subscribing to feeds
    """

    def __init__(self, username, subscriptions):
        """
        Initializes bot and connects to twitter api, then
        starts a twitter stream and run timer
        """
        self.username = username
        self.subscriptions = subscriptions
        self.event_list = []
        self.api = self.create_api()
        self.slack_func = None
        logger.info("Connecting to Twitter stream...")
        # Patch the tweepy.Stream._start() method
        logger.debug("Applying monkeypatch to tweepy.Stream class ...")
        tweepy.Stream._start = async_stream_start

        # start stream
        self.stream = tweepy.Stream(auth=self.api.auth, listener=self)
        self.start_time = time.time()

    # context manager functions
    def __enter__(self):
        """Implements TwitterClient as a context manager"""
        logger.debug("Enter TwitterClient")
        return self

    def __exit__(self, type, value, traceback):
        """Exits Twitterclient context manager """
        logger.debug("Context Manager Exiting TwitterClient")
        self.close_stream()

    def register_slack_function(self, func):
        """
        Communicates data to our slackbot
        this method is called at the end of on_status()
        overriding this method allows us to send self.events
        data to other classes
        """
        if func is not None:
            self.slack_func = func

    def on_slack_command(self, command, subs, slackbot):
        """
        Handles a CRUD command on slack
        and runs the appropriate subscription function
        then restarts the stream
        """
        self.close_stream()
        self.stream = tweepy.Stream(auth=self.api.auth, listener=self)
        if command == "update":
            self.update_subscriptions(subs)
        elif command == "delete":
            self.delete_subscriptions(subs)
        elif command == "add":
            self.add_subscriptions(subs)
        slackbot.send_message(
            channel=slackbot.output_channel,
            message=(f"Subscription list changed. Monitoring {self.subscriptions}"),
        )
        self.start_stream()

    def on_status(self, status):
        """
        Takes data from a twitter event
        and adds it to our list of events, then calls our slack func
        """
        username = status.user.screen_name
        text = status.text
        timestamp = str(datetime.fromtimestamp(float(status.timestamp_ms) / 1000.0))
        # timestamp = datetime.datetime.fromtimestamp(data[ms_/1000.0)
        self.event_list.append(
            {"username": username, "text": text, "timestamp": timestamp}
        )
        logger.info(f"Twitter event: {status.text}")
        if self.slack_func is not None:
            self.slack_func(self.event_list[-1])

    def on_disconnect(self, status):
        """Overwrites tweepy disconnect class"""
        logger.error(f"Disconnected from Twitter Stream. {status}")

    def add_subscriptions(self, slugs):
        """Adds a twitter subscription to our subscriptions"""
        logger.info("Adding Subscription...")
        self.subscriptions += slugs

    def delete_subscriptions(self, slugs):
        """Removes a subscription from our sub list"""
        logger.info("Deleting Subscription...")
        for slug in slugs:
            if slug in self.subscriptions:
                self.subscriptions.pop(self.subscriptions.index(slug))

    def update_subscriptions(self, subscriptions):
        """Sets a new list of subscriptions"""
        logger.info(f"Updating Twitter Subscriptions...")
        self.subscriptions = subscriptions

    def create_api(self):
        """Logs in to twitter api using bot authorization tokens"""
        logger.info(f"Connecting to Twitter API as {self.username}...")
        try:
            auth = tweepy.OAuthHandler(CONSUMER_API_KEY, CONSUMER_SECRET_API_KEY)
            auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET_TOKEN)
            return tweepy.API(auth)

        except Exception as e:
            logger.error(f"Failed to login to Twitter: {e}")

    # event statistics
    def set_total_events(self):
        """Counts total number of events that were monitored"""
        self.total_events = len(self.event_list)
        return self.total_events

    def set_total_run_time(self):
        """Calculates and rounds the total runtime of this bot"""
        self.total_run_time = round((time.time() - self.start_time) / 60, 2)
        return self.total_run_time

    def set_top_user(self):
        """
        Searches through monitored twitter data to find
        user with the most activity. If multiple users
        have the most activity, return None
        """
        if self.event_list is not []:
            user_data = [x["username"] for x in self.event_list]
            user_counts = Counter(user_data)
            top_users = sorted(
                user_counts.most_common(), key=lambda x: x[1], reverse=True
            )
            if (
                len(top_users) > 1 and top_users[0][1] == top_users[1][1]
            ) or not top_users:
                self.top_user = None
            else:
                self.top_user = top_users[0]
            return self.top_user

    def set_events_per_min(self):
        """
        Calculates the average number of Twitter events
        per minute based on the bot's runtime
        """
        if self.total_events and self.total_run_time:
            self.events_per_min = int(
                float(self.total_events) / float(self.total_run_time)
            )
        else:
            logger.error(
                "Attempted to calculate total events"
                "per minute, but the stream has not ended"
            )
            self.events_per_min = None

        return self.events_per_min

    def get_stream_summary(self):
        """
        Finds total events, run time, top user, and events per min
        to be displayed once the program exits
        """
        self.set_total_events()
        self.set_total_run_time()
        self.set_top_user()
        self.set_events_per_min()

    def create_top_user_str(self):
        """Formats the top user to be logged to output"""
        if self.top_user:
            username, event_count = self.top_user
            top_user_str = f"@{username} had the most activity"
            f" with {event_count} events."
        else:
            top_user_str = "Multiple users had the most activity"
        return top_user_str

    def start_stream(self):
        """
        Sets subscriptions and begin async thread
        to monitor twitter events
        """
        # remove duplicate subscriptions before we start monitoring the stream
        self.subscriptions = list(set(self.subscriptions))
        try:
            logger.info(f"Monitoring Twitter for {self.subscriptions}...")
            self.stream.filter(track=self.subscriptions, is_async=True)
        except Exception as e:
            logger.error(f"Error tracking Twitter Stream: {e}")

    def close_stream(self):
        """Disconnects the stream to exit thread"""
        if self.stream and self.stream.running:
            try:
                self.stream.running = False
                logger.info("Exiting TwitterClient")
                self.get_stream_summary()
            except Exception as e:
                logger.error(f"Tried to close stream, but it failed. {e}")
