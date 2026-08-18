#!/usr/bin/env node
/**
 * CDK application entrypoint.
 *
 * Stacks are stubbed for Phase 0 — resources are added in Phase 9.
 * Run: npm run synth (from infra/) or npm run synth (from root via turbo).
 */
import * as cdk from "aws-cdk-lib";
import { NetworkStack } from "../lib/network-stack";
import { DataStack } from "../lib/data-stack";
import { ApiStack } from "../lib/api-stack";
import { IngestStack } from "../lib/ingest-stack";

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION ?? "eu-west-1",
};

const network = new NetworkStack(app, "VziggoNetworkStack", { env });
const data = new DataStack(app, "VziggoDataStack", { vpc: network.vpc, env });
new ApiStack(app, "VziggoApiStack", {
  vpc: network.vpc,
  dataStack: data,
  env,
});
new IngestStack(app, "VziggoIngestStack", {
  vpc: network.vpc,
  dataStack: data,
  env,
});

app.synth();
