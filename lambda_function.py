#!/usr/bin/env python
# encoding: utf-8

import json
import datetime
import requests
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Slack の設定
SLACK_POST_URL = os.environ['slackPostURL']
SLACK_CHANNEL = os.environ['slackChannel']

# HipChat の設定
#HIPCHAT_ROOM_ID = os.environ['hipchatRoomId']
#HIPCHAT_API_TOKEN = os.environ['hipchatApiToken']
#HIPCHAT_POST_URL = "https://api.hipchat.com/v2/room/" + HIPCHAT_ROOM_ID + "/notification?auth_token=" + HIPCHAT_API_TOKEN

def build_message(cost, date):
    if float(cost) >= 10.0:
        color = "#ff0000" #red
    elif float(cost) > 0.0:
        color = "warning" #yellow
    else:
        color = "good"    #green

    message = "@channel %sまでのAWSの料金は、$%sです。" % (date, cost)

    attachements = {
        "color":color,
        "text":message
    }

    return attachements

def lambda_handler(event, context):
    response = boto3.client('cloudwatch', region_name='us-east-1')

    get_metric_statistics = response.get_metric_statistics(
        Namespace='AWS/Billing',
        MetricName='EstimatedCharges',
        Dimensions=[
            {
                'Name': 'Currency',
                'Value': 'USD'
            }
        ],
        StartTime=datetime.datetime.today() - datetime.timedelta(days=1),
        EndTime=datetime.datetime.today(),
        Period=86400,
        Statistics=['Maximum'])

    logger.info("%s", str(get_metric_statistics))

    cost = get_metric_statistics['Datapoints'][0]['Maximum']
    date = get_metric_statistics['Datapoints'][0]['Timestamp'].strftime('%Y年%m月%d日')

    json_body = build_message(cost, date)

    slack_message = {
        'channel': SLACK_CHANNEL,
        "attachments": [json_body]
    }

    # HipChatにPOST
    try:
    #    req = requests.post(HIPCHAT_POST_URL, data=json.dumps(json_body), headers={'Content-Type': 'application/json'})
    #    logger.info("Message posted to %s", HIPCHAT_POST_URL)
        req = requests.post(SLACK_POST_URL, data=json.dumps(slack_message), headers={'Content-Type': 'application/json'})
        logger.info("Message posted to %s", SLACK_POST_URL)
        logger.info("%s", json.dumps(slack_message))
    except requests.exceptions.RequestException as e:
        logger.error("Request failed: %s", e)
