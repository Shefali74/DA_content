#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { DevOpsAgentDemoStack } from "../lib/devops-agent-demo-stack";

const app = new cdk.App();

new DevOpsAgentDemoStack(app, "DevnovateDevOpsAgentDemo", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: "us-east-1",
  },
  description:
    "Devnovate Mumbai Demo: CloudWatch Alarm -> Lambda -> DevOps Agent Webhook",
});
