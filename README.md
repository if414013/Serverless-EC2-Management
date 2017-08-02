# EC2 Instances Management using AWS Lambda
This project is used to manage EC2 instances like start instance, stop instance, get the status of an instance and schedule which and when instances being started/stopped.
The start, stop, and status action will be done using SLACK Slash command and scheduled
action will be automatically follow the configuration file specified.
The system architecture can be found in */diagram* folder.
### Prerequisites
This guide are created and tested using Ubuntu 16.04 LTS
Before using this project, make sure that your local machine already meet all the
 prerequisites listed below :
- **Python 2.7 and PIP**
- **Terraform**

   You can follow instruction [Here!!](https://www.terraform.io/intro/getting-started/install.html) to install Terraform
- **ZIP**

   Use command below to install ZIP:

    ```apt-get update```

    ```apt-get install zip```
- Python Package

    Use command below to install all python package which needed to run this project :

    ```pip install -r requirements.txt```


- **AWS CLI** with **shared credential** setting up

    First install the AWS CLI using command:

    ```pip install --upgrade --user awscli```

    then setup your AWS CREDENTIALS :

    ```
    $ aws configure
    AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
    AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    Default region name [None]: us-west-2
    Default output format [None]: json
    ```
- Setup ***Slack Slash Command** and **Slack Incoming Webhook**

    Go to url below to setup your Slash Command :

    ```https://YOUR_SLACK_TEAM.slack.com/apps/A0F82E8CA-slash-commands```

    and save your **TEAM NAME**, **TOKEN**, and, **TEAM ID**, tobe used later.
    Then setup your **Slack Incoming Webhook** go to url below :

    ```https://YOUR_SLACK_TEAM.slack.com/apps/manage/custom-integrations```
    then save **incoming webhooks url** to be used later too.

### Configuration
- Setup **region**, **lambda arn**, and **accound_id** in **main.tf** file :

    ```
    variable "region" {
        default = "YOUR_REGION"
    }
    variable "account_id" {
        default = "YOUR_ACCOUNT_ID"
    }
    variable "lambda_role" {
        default = "Arn Role for lambda fit SNS and EC2 Full Acces"
    }
    ```

    make sure you entry a valid region listed below :

    | Region Code   | Region Name       |
    |:-------------:|:-------------:|
    | us-east-2     | US East (Ohio) |
    | us-east-1     |US East (N. Virginia)     |  
    | us-west-1     | US West (N. California)      |
    | us-west-2     | US West (Oregon)      |
    | ap-south-1    | Asia Pacific (Mumbai)      |
    |ap-northeast-2 | Asia Pacific (Seoul)      |
    |ap-southeast-1 | Asia Pacific (Singapore)      |
    |ap-southeast-2 | Asia Pacific (Sydney)      |
    |ap-northeast-1 | Asia Pacific (Tokyo)      |
    |ca-central-1   | Canada (Central)     |
    |eu-central-1   | EU (Frankfurt)     |
    |eu-west-1      | EU (Ireland)      |
    |eu-west-2      | EU (London)      |
    |sa-east-1      | South America (São Paulo)      |

    and **don't forget to set your AWS Account ID**, you can get it from AWS Console, click **Setting** then **Support Center** in the upper left side of your AWS Console,and you will get the id in the upper left side too

- Setup **Terraform Remote Config BackEnd**
    ```
    terraform {
        backend "s3" {
            bucket = "YOUR_S3_BUCKET_NAME"
            key    = "terraform.tfstate"
            region = "us-west-2"
        }
    }

    data "terraform_remote_state" "network" {
        backend = "s3"
        config {
            bucket = "YOUR_S3_BUCKET_NAME"
            key    = "terraform.tfstate"
            region = "us-west-2"
       }
    }
    ```
    Specify your S3 bucket name to configure **terraform remote state backend**.

- Setup **slack_teams**, **instances**, and **scheduled_events**

    **slack_teams** is a configuration where you define your slack team (one or more) that will be connected to system and can manage ec2 instances.Here is some example of configuration :
    ```
    EXAMPLE_TEAM_A_ID :
        team_name:             EXAMPLE TEAM NAME A
        slash_command_token:   SLASH_COMMAND_TOKEN
        incoming_webhook_url:  |
        https://hooks.example-slack.com/services/FZVVpScFjkhjhdsjdhsjhdjsh
    ```

    Note that a slack team id from previous step used here as an index then we define its atributes such as team_name, slash_command_token, incoming_webhook_url. Please beware of indentation and multiline input when you edit or add a config.

    **instances** is section where you can define instance whitelist that can be started/stopped either by using slack or scheduled events, here is the example of configuration :
    ```
    instancename-01:
        id :                   i-EXAMPLE
        region :               us-west-2
        slack_team_id:         EXAMPLE
    ```
    instancename-01 is an instance name that you define associated with an ec2 instance so we can start by its name.Please make sure that instancesname is unique, region valid, and slack_team_id already registered before in previous configuration.
    **scheduled_events** is section where you define scheduled events to start/stop
    instance, here is the sample configuration :
    ```
    start-instances-group-a:
        scheduled_expression:  rate(10 minutes) (rate or cron expression)
        command:               start | stop
        state :                ENABLED | DISABLED
        instances:
            - a-01
            - a-02
            - a-03

    ```
    in scheduled_expression you can use ```rate()``` or valid ```CRON``` expression
## Deployment
To deploy the project, just run command below :

``` python deploy.py```

Then you will get URL ENDPOINT, then use it to finish your slash command setup

## Common Errors

## Built With

* [AWS LAMBDA](https://aws.amazon.com/documentation/lambda/) - ServerLess Function
* [AWS API GATEWAY](https://aws.amazon.com/documentation/apigateway/) - Webhook for slash command
* [AWS Simple Notification Service](https://aws.amazon.com/documentation/sns/) - Push Notification to Lambda Worker from Lambda Receiver
* [AWS Cloudwatch Scheduled Events](http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html) - Scheduling
* [Terraform](https://www.terraform.io/docs/index.html) - Deployment and Infrastructure Management
* [Python 2.7](https://www.python.org/download/releases/2.7/) - Programming Language
