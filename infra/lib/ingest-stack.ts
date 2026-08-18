/**
 * Step Functions orchestration for long-running KB ingest jobs.
 * Phase 9: define scrape → chunk → embed → load state machine.
 */
import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";
import { DataStack } from "./data-stack";

export interface IngestStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  dataStack: DataStack;
}

export class IngestStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: IngestStackProps) {
    super(scope, id, props);

    new cdk.CfnOutput(this, "IngestStackStatus", {
      value: "stub — Step Functions ingest pipeline pending Phase 9",
    });
  }
}
