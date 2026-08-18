/**
 * Data layer: Aurora PostgreSQL (pgvector) + Amazon Neptune.
 * Phase 9: wire actual clusters with encryption and backup policies.
 */
import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";

export interface DataStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
}

export class DataStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DataStackProps) {
    super(scope, id, props);

    // Placeholder outputs — Aurora pgvector + Neptune added in Phase 9.
    new cdk.CfnOutput(this, "DataStackStatus", {
      value: "stub — Aurora pgvector and Neptune resources pending Phase 9",
    });
  }
}
