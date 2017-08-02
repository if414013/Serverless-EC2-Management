###############################################################################
#                                  Variables                                  #
###############################################################################
variable "region" {
  default = "ca-central-1"
}
variable "account_id" {
  default = "059793240584"
}
variable "lambda_role" {
  default = "arn:aws:iam::059793240584:role/ec2_start_stop_role"
}
###############################################################################
#                       Backend and Remote State Setup                        #
###############################################################################

terraform {
  backend "s3" {
    bucket = "gl-intern-terraform"
    key    = "terraform.tfstate"
    region = "us-west-2"
  }
}

data "terraform_remote_state" "network" {
  backend = "s3"
  config {
    bucket = "gl-intern-terraform"
    key    = "terraform.tfstate"
    region = "us-west-2"
  }
}

###############################################################################
#                             Cloud Provider Setup                            #
###############################################################################
provider "aws" {
  region     = "${var.region}"
  shared_credentials_file  = "${pathexpand("~/.aws/credentials")}"
}


###############################################################################
#            AWS Lambda Function (lambda_start_stop) Setup                 #
###############################################################################
resource "aws_lambda_function" "lambda_start_stop" {
    filename = "lambda_start_stop.zip"
    role = "${var.lambda_role}"
    function_name = "lambda_start_stop"
    handler = "lambda_start_stop.lambda_handler"
    runtime = "python2.7"
    timeout = 300
    memory_size = 128
    publish = "true"
}

###############################################################################
#                 AWS Lambda Function (lambda_worker) Setup                   #
###############################################################################
resource "aws_lambda_function" "lambda_worker" {
    filename = "lambda_worker.zip"
    function_name = "lambda_worker"
    handler = "lambda_worker.lambda_handler"
    role = "${var.lambda_role}"
    runtime = "python2.7"
    timeout = 60
    memory_size = 128
    publish = "true"
}

###############################################################################
#               AWS Lambda Function (lambda_receiver) Setup                   #
###############################################################################
resource "aws_lambda_function" "lambda_receiver" {
    filename = "lambda_receiver.zip"
    function_name = "lambda_receiver"
    handler = "lambda_receiver.lambda_handler"
    role = "${var.lambda_role}"
    runtime = "python2.7"
    timeout = 60
    publish = "true"
    memory_size = 128
    environment {
      variables = {
        sns_arn = "${aws_sns_topic.internserverless-sns.arn}"
      }
    }
}

resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.lambda_receiver.arn}"
  principal     = "apigateway.amazonaws.com"
}
###############################################################################
#                     AWS SNS Topic and SNS Subscription                      #
###############################################################################
resource "aws_sns_topic" "internserverless-sns" {
  name = "internserverless-sns"
}

resource "aws_sns_topic_subscription" "receiver_to_worker_subscription" {
  topic_arn = "${aws_sns_topic.internserverless-sns.arn}"
  protocol  = "lambda"
  endpoint  = "${aws_lambda_function.lambda_worker.arn}"
}

resource "aws_lambda_permission" "lambda_sns_permission" {
    statement_id = "AllowExecutionFromSNS"
    action = "lambda:InvokeFunction"
    function_name = "${aws_lambda_function.lambda_worker.arn}"
    principal = "sns.amazonaws.com"
    source_arn = "${aws_sns_topic.internserverless-sns.arn}"
}

###############################################################################
#                                 AWS API Gateway                             #
###############################################################################
# API root
resource "aws_api_gateway_rest_api" "slack_lamdba_api" {
  name = "slack_lamdba_api"
  description = "API Gateway to connect slack to lambda"
}

# API resource
resource "aws_api_gateway_resource" "slack" {
  rest_api_id = "${aws_api_gateway_rest_api.slack_lamdba_api.id}"
  parent_id = "${aws_api_gateway_rest_api.slack_lamdba_api.root_resource_id}"
  path_part = "slack"
}

# API Method
resource "aws_api_gateway_method" "slack_method" {
  rest_api_id = "${aws_api_gateway_rest_api.slack_lamdba_api.id}"
  resource_id = "${aws_api_gateway_resource.slack.id}"
  http_method = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = "${aws_api_gateway_rest_api.slack_lamdba_api.id}"
  resource_id = "${aws_api_gateway_resource.slack.id}"
  http_method = "${aws_api_gateway_method.slack_method.http_method}"
  type = "AWS"
  uri = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${var.region}:${var.account_id}:function:${aws_lambda_function.lambda_receiver.function_name}/invocations"
  integration_http_method = "POST"
  passthrough_behavior = "WHEN_NO_TEMPLATES"
  request_templates {
    "application/x-www-form-urlencoded" = <<EOF
    {
      "body" : $input.json('$')
    }
EOF
  }
}

resource "aws_api_gateway_method_response" "200" {
  rest_api_id = "${aws_api_gateway_rest_api.slack_lamdba_api.id}"
  resource_id = "${aws_api_gateway_resource.slack.id}"
  http_method = "${aws_api_gateway_method.slack_method.http_method}"
  status_code = "200"
  response_models{
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "slack_integration_response" {
  depends_on = ["aws_api_gateway_integration.lambda_integration"]
  rest_api_id = "${aws_api_gateway_rest_api.slack_lamdba_api.id}"
  resource_id = "${aws_api_gateway_resource.slack.id}"
  http_method = "${aws_api_gateway_method.slack_method.http_method}"
  status_code = "${aws_api_gateway_method_response.200.status_code}"

  response_templates {
    "application/json" = ""
  }
}

resource "aws_api_gateway_deployment" "dev" {
  depends_on = [
    "aws_api_gateway_method.slack_method",
    "aws_api_gateway_integration.lambda_integration"
  ]
  rest_api_id = "${aws_api_gateway_rest_api.slack_lamdba_api.id}"
  stage_name = "dev"
}

###############################################################################
#                                    Output                                   #
###############################################################################
output "dev_url" {
  value = "https://${aws_api_gateway_deployment.dev.rest_api_id}.execute-api.${var.region}.amazonaws.com/${aws_api_gateway_deployment.dev.stage_name}/slack"
}
