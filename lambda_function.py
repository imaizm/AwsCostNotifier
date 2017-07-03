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

# HipChat の設定
HIPCHAT_ROOM_ID = os.environ['hipchatRoomId']
HIPCHAT_API_TOKEN = os.environ['hipchatApiToken']
HIPCHAT_POST_URL = "https://api.hipchat.com/v2/room/" + HIPCHAT_ROOM_ID + "/notification?auth_token=" + HIPCHAT_API_TOKEN

response = boto3.client('cloudwatch', region_name='us-west-2')

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

cost = get_metric_statistics['Datapoints'][0]['Maximum']
date = get_metric_statistics['Datapoints'][0]['Timestamp'].strftime('%Y年%m月%d日')

def build_message(cost):
#    if float(cost) >= 10.0:
#        color = "#ff0000" #red
#    elif float(cost) > 0.0:
#        color = "warning" #yellow
#    else:
#        color = "good"    #green

    message = "@all %sまでのAWSの料金は、$%sです。" % (date, cost)

    atachements = {
        "from":"AwsCostNotifier",
        "notify":"true",
        "message_format":"text",
        "message":message
    }
    return atachements

def lambda_handler(event, context):
    json_body = build_message(cost)

    # HipChatにPOST
    try:
        req = requests.post(HIPCHAT_POST_URL, data=json.dumps(json_body))
        logger.info("Message posted to %s", HIPCHAT_ROOM_ID)
    except requests.exceptions.RequestException as e:
        logger.error("Request failed: %s", e)
