# start and stop
import boto3
import json
import urllib2
import os
import logging

from base64 import b64decode
from urlparse import parse_qs

# set logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    print event
    if event['command'] == 'start':
        start_instances(event['instances'])
    elif event['command'] == 'stop':
        stop_instances(event['instances'])


def start_instances(instances):
    for key in instances:
        try:
            ec2 = boto3.client('ec2', region_name=instances[key])
            ec2.start_instances(InstanceIds=[key])
        except Exception as e:
            continue


def stop_instances(instances):
    for key in instances:
        try:
            ec2 = boto3.client('ec2', region_name=instances[key])
            ec2.stop_instances(InstanceIds=[key])
        except Exception as e:
            continue
