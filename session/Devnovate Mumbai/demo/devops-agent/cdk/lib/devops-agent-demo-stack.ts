import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as sns from "aws-cdk-lib/aws-sns";
import * as snsSubscriptions from "aws-cdk-lib/aws-sns-subscriptions";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";
import * as cwActions from "aws-cdk-lib/aws-cloudwatch-actions";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as iam from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import * as path from "path";

export class DevOpsAgentDemoStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ─────────────────────────────────────────────────────────
    // 1. ERROR-GENERATING LAMBDA (the "broken" workload)
    //    Based on official AWS DevOps Agent test environment docs:
    //    https://docs.aws.amazon.com/devopsagent/latest/userguide/getting-started-with-aws-devops-agent-creating-a-test-environment.html
    // ─────────────────────────────────────────────────────────
    const errorLambda = new lambda.Function(this, "ErrorLambda", {
      functionName: "devnovate-demo-error-generator",
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "index.lambda_handler",
      code: lambda.Code.fromInline(`
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

def lambda_handler(event, context):
    """
    Intentionally generates errors for DevOps Agent testing.
    Based on official AWS DevOps Agent test environment pattern.
    """
    error_message = (
        "CRITICAL: Database connection pool exhausted. "
        "Max connections (100) reached. "
        "Active queries: 98, Waiting: 47. "
        "Service: payment-processor, Region: us-east-1"
    )
    
    logger.error(f"ServiceError: {error_message}")
    logger.error(f"RequestId: {context.aws_request_id}")
    logger.error("Stack trace: ConnectionPoolExhausted at pool.acquire() -> timeout after 30000ms")
    
    # Always throw an error - DevOps Agent will investigate this
    raise Exception(error_message)
`),
      timeout: cdk.Duration.seconds(10),
      memorySize: 128,
      description:
        "Intentionally throws errors to trigger CloudWatch Alarm for DevOps Agent investigation",
    });

    // ─────────────────────────────────────────────────────────
    // 2. CLOUDWATCH ALARM (watches Lambda errors)
    // ─────────────────────────────────────────────────────────
    const errorMetric = errorLambda.metricErrors({
      period: cdk.Duration.minutes(1),
      statistic: "Sum",
    });

    const alarm = new cloudwatch.Alarm(this, "LambdaErrorAlarm", {
      alarmName: "devnovate-demo-lambda-errors",
      alarmDescription:
        "[DEMO] Lambda error rate spike detected. " +
        "Function: devnovate-demo-error-generator. " +
        "Simulates payment-processor database connection failure.",
      metric: errorMetric,
      threshold: 3,
      evaluationPeriods: 1,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    // ─────────────────────────────────────────────────────────
    // 3. WEBHOOK CREDENTIALS (Secrets Manager)
    // ─────────────────────────────────────────────────────────
    const webhookCredentials = new secretsmanager.Secret(
      this,
      "WebhookCredentials",
      {
        secretName: "devnovate-demo-webhook-credentials",
        description:
          "DevOps Agent webhook URL and HMAC secret. " +
          "Update after deploy with your actual credentials.",
        secretObjectValue: {
          webhook_url: cdk.SecretValue.unsafePlainText(
            "REPLACE_WITH_YOUR_WEBHOOK_URL"
          ),
          webhook_secret: cdk.SecretValue.unsafePlainText(
            "REPLACE_WITH_YOUR_WEBHOOK_SECRET"
          ),
        },
      }
    );

    // ─────────────────────────────────────────────────────────
    // 4. SNS TOPIC + WEBHOOK LAMBDA (alarm -> DevOps Agent)
    // ─────────────────────────────────────────────────────────
    const alarmTopic = new sns.Topic(this, "AlarmTopic", {
      topicName: "devnovate-demo-alarms",
    });

    const webhookLambda = new lambda.Function(this, "WebhookLambda", {
      functionName: "devnovate-DevOpsAgent-Webhook",
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "index.lambda_handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "..", "lambda")),
      timeout: cdk.Duration.seconds(30),
      memorySize: 128,
      environment: {
        WEBHOOK_SECRET_NAME: webhookCredentials.secretName,
      },
      description:
        "Receives alarm via SNS, forwards to DevOps Agent webhook with HMAC signature",
    });

    webhookCredentials.grantRead(webhookLambda);

    // Wire: Alarm -> SNS -> Webhook Lambda
    alarm.addAlarmAction(new cwActions.SnsAction(alarmTopic));
    alarmTopic.addSubscription(
      new snsSubscriptions.LambdaSubscription(webhookLambda)
    );

    // ─────────────────────────────────────────────────────────
    // OUTPUTS
    // ─────────────────────────────────────────────────────────
    new cdk.CfnOutput(this, "ErrorLambdaName", {
      value: errorLambda.functionName,
      description: "Invoke this Lambda to generate errors for the demo",
    });

    new cdk.CfnOutput(this, "AlarmName", {
      value: alarm.alarmName,
      description: "CloudWatch Alarm name",
    });

    new cdk.CfnOutput(this, "WebhookSecretName", {
      value: webhookCredentials.secretName,
      description: "Update this secret with your DevOps Agent webhook credentials",
    });

    new cdk.CfnOutput(this, "TriggerCommand", {
      value: `for i in $(seq 1 5); do aws lambda invoke --function-name ${errorLambda.functionName} --region us-east-1 /dev/null 2>&1; done`,
      description: "Run this to trigger errors and fire the alarm",
    });
  }
}
