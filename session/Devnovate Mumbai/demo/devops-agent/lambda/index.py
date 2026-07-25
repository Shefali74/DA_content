"""
Lambda: CloudWatch Alarm (via SNS) -> AWS DevOps Agent Webhook

Based on the official AWS pattern from:
- https://aws.amazon.com/blogs/networking-and-content-delivery/automated-network-incident-response-with-aws-devops-agent/
- https://github.com/aws-samples/sample-automated-aws-devops-agent-network-incident-response

Flow: CloudWatch Alarm -> SNS -> this Lambda -> DevOps Agent Webhook (HMAC signed)

The Lambda reads webhook credentials from AWS Secrets Manager,
builds an incident payload from the CloudWatch Alarm JSON,
signs it with HMAC SHA-256, and POSTs to the DevOps Agent webhook.
"""

import json
import os
import hashlib
import hmac
import base64
import urllib.request
import boto3
from datetime import datetime, timezone


def get_webhook_credentials():
    """Retrieve webhook URL and secret from Secrets Manager."""
    secret_name = os.environ.get(
        "WEBHOOK_SECRET_NAME", "devnovate-demo-webhook-credentials"
    )
    region = os.environ.get("AWS_REGION", "us-east-1")

    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])

    return secret["webhook_url"], secret["webhook_secret"]


def lambda_handler(event, context):
    """Process SNS event from CloudWatch Alarm and trigger DevOps Agent investigation."""

    print(f"Received event: {json.dumps(event)}")

    # Get webhook credentials from Secrets Manager
    webhook_url, webhook_secret = get_webhook_credentials()

    # Parse SNS message (CloudWatch Alarm payload)
    sns_record = event["Records"][0]["Sns"]
    alarm = json.loads(sns_record["Message"])

    alarm_name = alarm.get("AlarmName", "Unknown")
    alarm_desc = alarm.get("AlarmDescription", "No description")
    new_state = alarm.get("NewStateValue", "ALARM")
    reason = alarm.get("NewStateReason", "")
    region = alarm.get("Region", "us-east-1")

    # Only trigger investigation for ALARM state (not OK or INSUFFICIENT_DATA)
    if new_state != "ALARM":
        print(f"Skipping - alarm state is {new_state}, not ALARM")
        return {"statusCode": 200, "body": "Skipped - not in ALARM state"}

    # Build DevOps Agent webhook payload
    # Schema: https://docs.aws.amazon.com/devopsagent/latest/userguide/configuring-integrations-and-knowledge-invoking-devops-agent-through-webhook.html
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    incident_id = f"cw-{alarm_name}-{int(datetime.now(timezone.utc).timestamp())}"

    payload = json.dumps({
        "eventType": "incident",
        "incidentId": incident_id,
        "action": "created",
        "priority": "HIGH",
        "title": f"CloudWatch Alarm: {alarm_name}",
        "description": (
            f"CloudWatch Alarm '{alarm_name}' transitioned to {new_state} "
            f"in region {region}. "
            f"Description: {alarm_desc}. "
            f"Reason: {reason}"
        ),
        "timestamp": timestamp,
        "service": "devnovate-demo",
        "data": {
            "source": "cloudwatch",
            "alarm_name": alarm_name,
            "alarm_description": alarm_desc,
            "new_state": new_state,
            "state_reason": reason,
            "region": region,
        }
    })

    # Sign the request with HMAC-SHA256
    # Format: HMAC(secret, "timestamp:payload")
    signature_input = f"{timestamp}:{payload}"
    signature = base64.b64encode(
        hmac.new(
            webhook_secret.encode("utf-8"),
            signature_input.encode("utf-8"),
            hashlib.sha256
        ).digest()
    ).decode("utf-8")

    # POST to DevOps Agent webhook
    req = urllib.request.Request(
        webhook_url,
        data=payload.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-amzn-event-timestamp": timestamp,
            "x-amzn-event-signature": signature,
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            body = response.read().decode("utf-8")
            print(f"DevOps Agent webhook response: {status} - {body}")
    except urllib.error.HTTPError as e:
        print(f"ERROR: DevOps Agent webhook returned {e.code}: {e.read().decode()}")
        raise
    except Exception as e:
        print(f"ERROR calling DevOps Agent webhook: {e}")
        raise

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "DevOps Agent investigation triggered",
            "alarmName": alarm_name,
            "incidentId": incident_id,
            "webhookStatus": status,
        })
    }
