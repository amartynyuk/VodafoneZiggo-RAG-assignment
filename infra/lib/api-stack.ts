/**
 * API Gateway + container Lambdas for ai-assistant and kb-builder.
 * Phase 9: add API routes, Lambda functions, IAM roles.
 */
import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";
import { DataStack } from "./data-stack";

export interface ApiStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  dataStack: DataStack;
}

export class ApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    new cdk.CfnOutput(this, "ApiStackStatus", {
      value: "stub — API Gateway and container Lambdas pending Phase 9",
    });
  }
}
