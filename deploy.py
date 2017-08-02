import subprocess
import json
import yaml
import boto3
import traceback

regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ca-central-1',
           'eu-west-1', 'eu-central-1', 'eu-west-2', 'ap-northeast-1',
           'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2',
           'ap-south-1', 'sa-east-1']


def validate_slack_teams():
    try:
        teams = get_config()['slack_teams']
        if teams == None:
            print 'slack_teams Configuration Error!!'
            print "Please spesify at least 1 Slack Teams Configuration!"
            return False
        else:
            for key in teams:
                if teams[key]['slash_command_token'] == None or \
                        teams[key]['team_name'] == None\
                        or teams[key]['incoming_webhook_url'] == None:
                    print 'slack_teams Configuration Error!!'
                    print 'slash_command_token, team_name, incoming_webhook_url can not be empty!'
                    return False
            print 'Slack Teams Configuration Validated!!'
            return True
    except Exception as e:
        print "There was error in your slack_teams configurations, please make sure you've follow the right format!!"
        print e
        return False


def validate_instances():
    try:
        instances = get_config()['instances']
        teams = get_config()['slack_teams']
        if instances == None:
            print 'instances Configuration Error!!'
            print "Please spesify at least 1 EC2 instances configuration!"
            return False
        else:
            for key in instances:
                if instances[key]['id'] == None or instances[key]['region'] == None\
                        or instances[key]['slack_team_id'] == None:
                    print 'instances Configuration Error!!'
                    print 'id, region, slack_team_id can not be empty!'
                    return False
                elif instances[key]['region'] not in regions:
                    print 'instances Configuration Error!!'
                    print 'Please specify correct region for instace ' + key + '!'
                    print "Available region is : "
                    print regions
                    return False
                elif teams.has_key(instances[key]['slack_team_id']) == False:
                    print 'instances Configuration Error!!'
                    print 'Please specify correct slack_team_id for instace ' + key + '!'
                    print 'Available slack_team_id is :'
                    print teams.keys()
                    return False
            print 'Instance List Configuration Validated!!'
            return True
    except Exception as e:
        print "There was error in your instances configurations, please make sure you've follow the right format!!"
        print e
        return False


def validate_scheduled_events():
    try:
        events = get_config()['scheduled_events']
        if events == None:
            return
        instances = get_config()['instances']
        for key in events:
            if events[key]['command'] == None or events[key]['scheduled_expression'] == None:
                print 'scheduled_events Configuration Error!!'
                print 'command and scheduled_expression can not be empty!'
                return False
            elif len(events[key]['instances']) == 0:
                print 'scheduled_events Configuration Error!!'
                print "Please specify atleast 1 instances!"
                return False
            else:
                temp = events[key]['instances']
                for i in range(len(temp)):
                    if instances.has_key(temp[i]) == False:
                        print 'scheduled_events Configuration Error!!'
                        print "Instance " + temp[i] + "is not valid!"
                        print "The valid instance is:"
                        print instances.keys()
                        return False
        print 'Schedules events List Configuration Validated!!'
        return True
    except Exception as e:
        print "There was error in your scheduled_events configurations, please make sure you've follow the right format!!"
        print e
        return False


def get_config():
    file_path = 'configs.yaml'
    with open(file_path, "r") as file_descriptor:
        config = yaml.load(file_descriptor)
    return config


def create_or_update_events():
    events = get_config()['scheduled_events']
    client = boto3.client('events')
    lambda_client = boto3.client('lambda')
    lambda_arn = lambda_client.get_function(FunctionName='lambda_start_stop')[
        'Configuration']['FunctionArn']
    for key in events:
        try:
            if events[key].has_key('state'):
                state = events[key]['state']
            arn = client.put_rule(
                Name=key,
                ScheduleExpression=events[key]['scheduled_expression'],
                State=state
            )
            inputs = {
                "command": events[key]['command'],
                "instances": events[key]['instances']
            }
            target = client.put_targets(
                Rule=key,
                Targets=[
                    {
                        'Id': 'target' + key,
                        'Arn': lambda_arn,
                        'Input': json.dumps(inputs)
                    }]
            )
            lambda_client.add_permission(
                FunctionName=lambda_arn,
                StatementId=key,
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=arn['RuleArn'],
            )
        except Exception as e:
            print e
            continue


boolTeams = validate_slack_teams()
boolInstances = validate_instances()
boolEvents = validate_scheduled_events()
if boolTeams == True and boolInstances == True and boolEvents == True:
    try:
        client = boto3.client('lambda')
        client.delete_function(FunctionName='lambda_receiver')
        client.delete_function(FunctionName='lambda_worker')
        client.delete_function(FunctionName='lambda_start_stop')
    except Exception as e:
        print e
    subprocess.call(['./terraform.sh'], shell=True)
    create_or_update_events()
