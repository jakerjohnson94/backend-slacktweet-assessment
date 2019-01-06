import tweepy


class TweepyStreamListener(tweepy.StreamListener):
    """
    overwrite tweepystreamlistener to monitor our bot's twitter stream
    """

    def on_status(self, status):
        print(status.text)
