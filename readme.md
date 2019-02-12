# Slacktweet

Slacktweet is a slack and twitter bot integration. This application is written in **Python**. The goal is to create a controllable, long-running Slackbot that subscribes to various Twitter streams, and republishes those tweets into a channel (or channels) on Slack.  You don't need to send messages from Slack to Twitter - just a Twitter listener.  The Bot ,@bobbot2018 on twitter, will be deployed on Heroku cloud-hosting platform.

## Getting Started

Python 3.7.1 is need for this instance of the application to work. For the slackbot install [slackclient](https://python-slackclient.readthedocs.io/en/latest/). One will also need to create a slack workspace to test. For twitter install [tweepy](http://www.tweepy.org/). Make sure that you are looking for the latest version of tweepy. [tweepy stream](https://tweepy.readthedocs.io/en/v3.7.0/streaming_how_to.html#streaming-with-tweepy). The tweepy stream will allow the monitoring of twitter.

## Features

This project makes a:
*Slack and twitter bot
*The Slackbot will become a simple command line tool
*Slackbot commands first mention the bot @bobbot2018 then type UPDATE, ADD, REMOVE, OR EXIT.
*The Twitterbot will monitor streams that will be updated through the slackbot

