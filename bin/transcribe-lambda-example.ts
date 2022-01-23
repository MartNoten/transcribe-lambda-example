#!/usr/bin/env node
import * as cdk from '@aws-cdk/core';
import { TranscribeLambdaExampleStack } from '../lib/transcribe-lambda-example-stack';

const app = new cdk.App();
new TranscribeLambdaExampleStack(app, 'TranscribeLambdaExampleStack');
