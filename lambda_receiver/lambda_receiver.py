# receiver
import boto3
import yaml
import json
import logging
import os
import time
import re

from base64 import b64decode
from urlparse import parse_qs

# set logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    params = parse_qs(event['body'])
    slash_command_token = params['token'][0]
    team_id = params['team_id'][0]

    # validate request
    if validate_request(team_id, slash_command_token) == False:
        return ('Invalid request!!')

    # validate if command exist
    if params.has_key("text"):
        command = params['text'][0].split(" ")
    else:
        return "Your command isn't valid, type  /ec2 help for all ec2 valid slash command"

    # validate /ec2 command
    if len(command) == 0:
        return "Your command isn't valid, type  /ec2 help for all ec2 valid slash command"
    else:
        if (command[0] == 'help') or (command[0] == 'list-instances'):
            triggerWorker(build_message(params, ""))
            return "Your request is being processed!"
        elif ((command[0] == 'start') or (command[0] == 'stop')
                or (command[0] == 'status')) and (len(command) == 2):
            if validate_instance_name(command[1], team_id):
                triggerWorker(build_message(params, command[1]))
                return "Your request is being processed!"
            else:
                return 'Please specify correct instance-name!'
        else:
            return "Your command isn't valid, type  /ec2 help for all ec2 valid slash command"


def build_message(params, instance_name):
    incoming_webhook_url = get_slack_team_incoming_webhook(
        params['team_id'][0])
    if instance_name == "":
        instance = ""
    else:
        instance = get_instance(instance_name)
    available_instances = get_instance_list(params['team_id'][0])
    return json.dumps({"channel_name": params['channel_name'][0],
                       "text": params['text'][0],
                       "response_url": params['response_url'][0],
                       "incoming_webhook_url": incoming_webhook_url,
                       "user_name": params['user_name'][0],
                       "instance": {instance_name: instance},
                       "available_instances": available_instances})


def triggerWorker(message):
    sns_client = boto3.client('sns')
    sns_client.publish(
        TopicArn=os.environ.get("sns_arn"),
        Message=message,
        MessageStructure='string'
    )


def validate_request(team_id, slash_command_token):
    config = get_config()
    return config['slack_teams'][team_id]['slash_command_token'] == \
        slash_command_token


def validate_instance_name(instance_name, team_id):
    instances = get_config()['instances']
    for key in instances:
        if key == instance_name and instances[key]['slack_team_id'] ==\
                team_id:
            return True
    return False


def get_config():
    file_path = 'configs.yaml'
    with open(file_path, "r") as file_descriptor:
        config = yaml.load(file_descriptor)
    return config


def get_slack_team_incoming_webhook(team_id):
    config = get_config()
    incoming_webhook_url = config['slack_teams'][team_id]['incoming_webhook_url']
    return re.sub('[\s+]', '', incoming_webhook_url)


def get_instance(instance_name):
    instances = get_config()['instances']
    return instances[instance_name]


def get_instance_list(team_id):
    instances = get_config()['instances']
    temp = {}
    for key in instances:
        if instances[key]["slack_team_id"] == team_id:
            temp[key] = instances[key]
    return temp
