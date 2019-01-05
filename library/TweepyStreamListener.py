import tweepy


class TweepyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        print(status.text)
