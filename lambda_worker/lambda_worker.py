# worker
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

# mapping instance status
instanceStatus = {0: "pending", 16: "running", 32: "Shutting Down", 48: "Terminated",
                  64: "stopping", 80: "stopped"}


def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    command = message['text'].split(' ')
    if command[0] == 'help':
        help(message['response_url'])
    elif command[0] == 'list-instances':
        list_instances(message['response_url'], message['available_instances'])
    elif command[0] == 'start':
        start_instance(message["instance"], message)
    elif command[0] == 'stop':
        stop_instance(message["instance"], message)
    elif command[0] == 'status':
        status_instance(message["instance"], message['response_url'])


def start_instance(instance, info):
    name = instance.keys()[0]
    instance = instance[instance.keys()[0]]
    ec2 = boto3.resource('ec2', region_name=instance['region'])
    instance = ec2.Instance(instance['id'])
    try:
        instance.start()
        post_to_slack_channel(info['user_name'] + " start instance *" + name + "*", info['channel_name'],
                              info['incoming_webhook_url'])
        post_to_slack_user("instance *" + name +
                           "* is `started`!", info['response_url'])
    except Exception as e:
        post_to_slack_user("*EC2 Permission Error!!*", info['response_url'])


def stop_instance(instance, info):
    name = instance.keys()[0]
    instance = instance[instance.keys()[0]]
    ec2 = boto3.resource('ec2', region_name=instance['region'])
    instance = ec2.Instance(instance['id'])
    try:
        instance.stop()
        post_to_slack_channel(info['user_name'] + " stop instance *" + name + "*", info['channel_name'],
                              info['incoming_webhook_url'])
        post_to_slack_user("instance *" + name +
                           "* is `stopped`!", info['response_url'])
    except Exception as e:
        post_to_slack_user("*EC2 Permission Error!!*", info['response_url'])


def status_instance(instance, response_url):
    name = instance.keys()[0]
    instance = instance[instance.keys()[0]]
    try:
        client = boto3.client('ec2', region_name=instance['region'])
        status = 'stopped'
        if len(client.describe_instance_status(
                InstanceIds=[instance['id']])['InstanceStatuses']) == 1:
            status = client.describe_instance_status(
                InstanceIds=[instance['id']])['InstanceStatuses'][0]['InstanceState']['Name']
        post_to_slack_user("instance *" + name +
                           "* is currently `" + status + "`!", response_url)
    except Exception as e:
        post_to_slack_user("*EC2 Permission Error!!*", info['response_url'])


def list_instances(response_url, instances):
    print instances
    message = '*INSTANCE LIST*\n'
    for key in instances:
        try:
            client = boto3.client('ec2', region_name=instances[key]['region'])
            status = 'stopped'
            if len(client.describe_instance_status(
                    InstanceIds=[instances[key]['id']])['InstanceStatuses']) == 1:
                status = client.describe_instance_status(
                    InstanceIds=[instances[key]['id']])['InstanceStatuses'][0]['InstanceState']['Name']
            name = '*' + key + '*'
            status = '`' + status + '`'
            for j in range(len(name), 25):
                name = name + ' '
            message = message + name + status + "\n"
        except Exception as e:
            print e
            continue
    post_to_slack_user(message, response_url)


def help(response_url):
    message = """:one: `help`:arrow_right: get information about all valid commands\n
    *FORMAT: *`/ec2 help`\n"""
    message = message + """:two: `start`:arrow_right: start EC2 instance\n \
    *FORMAT: *`/ec2 start [INSTANCE_NAME]`\n \
    *EXAMPLE: *`/ec2 start a-01`\n"""
    message = message + """:three: `stop`: arrow_right: stop EC2 instance\n \
    *FORMAT: *`/ec2 stop [INSTANCE_NAME]`\n \
    *EXAMPLE: *`/ec2 stop a-01`\n"""
    message = message + """:four: `status`:arrow_right: check EC2 instance status\n \
    *FORMAT: *`/ec2 status [INSTANCE_NAME]`\n \
    *EXAMPLE: *`/ ec2 status a-01`\n"""
    message = message + """:five: `list-instances`: arrow_right: list available instances
    *FORMAT: *`/ec2 list-instances`"""
    post_to_slack_user(message, response_url)


def post_to_slack_channel(message, channel_name, incoming_webhook_url):
    channel_name = '#' + channel_name
    try:
        req = urllib2.Request(incoming_webhook_url)
        req.add_header("Content-Type", "application/json")
        urllib2.urlopen(req, data=json.dumps(
            {'channel': channel_name, 'text': message}))
    except urllib2.HTTPError as e:
        pass


def post_to_slack_user(message, response_url):
    try:
        req = urllib2.Request(response_url)
        req.add_header("Content-Type", "application/json")
        urllib2.urlopen(req, data=json.dumps({'text': message}))
    except urllib2.HTTPError as e:
        pass
