# Slacktweet

Slacktweet is a slack and twitter bot integration. This application is written in **Python**. The goal is to create a controllable, long-running Slackbot that subscribes to various Twitter streams, and republishes those tweets into a channel (or channels) on Slack.  You don't need to send messages from Slack to Twitter - just a Twitter listener.  The Bot ,@bobbot2018 on twitter, will be deployed on Heroku cloud-hosting platform.

## Getting Started

Python 3.7.1 is need for this instance of the application to work. For the slackbot install [slackclient](https://python-slackclient.readthedocs.io/en/latest/). One will also need to create a slack workspace to test. For twitter install [tweepy](http://www.tweepy.org/). Make sure that you are looking for the latest version of tweepy. [tweepy stream](https://tweepy.readthedocs.io/en/v3.7.0/streaming_how_to.html#streaming-with-tweepy). The tweepy stream will allow the monitoring of twitter. The last step to getting started is to register with [twitter dev](https://developer.twitter.com/en.html).

## Features

This project makes a:
*Slack and twitter bot
*The Slackbot will become a simple command line tool
*Slackbot commands first mention the bot @bobbot2018 then type UPDADE, ADD, REMOVE, OR EXIT.
*The Twitterbot will monitor streams that will be updated through the slackbot

## Deployment

This section assumes that you have already created a Heroku account from previous assignments, and you have the Heroku CLI toolsLinks to an external site. installed on your local development machine. Most of the python Heroku deployment examples on the internet assume that you are developing a web app, but in this case you are deploying a simple standalone python script without a framework or WSGI gateway.  In order to deploy your bot to Heroku, your github repo must contain some special files named `Procfile` and `runtime.txt`.  Procfile tells Heroku which program to run when you activate your free dyno instance.  Procfile contents should look like this