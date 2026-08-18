/**
 * VPC and networking for Aurora, Neptune, and Lambda functions.
 * Phase 9: add subnets, NAT gateway, security groups.
 */
import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";

export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.IVpc;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Stub VPC — replace with production-grade layout in Phase 9.
    this.vpc = new ec2.Vpc(this, "VziggoVpc", {
      maxAzs: 2,
      natGateways: 0, // cost-saving stub; enable for private Lambda egress
    });

    new cdk.CfnOutput(this, "VpcId", { value: this.vpc.vpcId });
  }
}
