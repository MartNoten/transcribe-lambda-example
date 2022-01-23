import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import * as lambdaEventSources from '@aws-cdk/aws-lambda-event-sources';
import * as lambda from '@aws-cdk/aws-lambda';
import { PythonFunction } from "@aws-cdk/aws-lambda-python";  
import * as iam from '@aws-cdk/aws-iam';
import { Duration } from '@aws-cdk/core';

export class TranscribeLambdaExampleStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Adding two S3 buckets to our stack
    const audioFilesBucket = new s3.Bucket(this, 'AudioFilesBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true // Destroy+AutoDelete allows you to easily destroy your project: for dev only.
    });

    const transcriptsBucket = new s3.Bucket(this, 'TranscriptsBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true // Destroy+AutoDelete allows you to easily destroy your project: for dev only.
    });

    // Creating the AWS Lambda function and the S3 trigger that invokes it
    const lambdaFunction = new PythonFunction(this, 'GenerateTranscriptionFunction', {
      entry: 'lambda/GenerateTranscriptionFunction',
      functionName: 'GenerateTranscriptionFunction',
      environment: {
        'TRANSCRIPT_BUCKET': transcriptsBucket.bucketName
      },
      index: 'main.py',
      timeout: Duration.seconds(120),
      runtime: lambda.Runtime.PYTHON_3_9
    });

    const s3PutEventSource = new lambdaEventSources.S3EventSource(audioFilesBucket, {
      events: [
        s3.EventType.OBJECT_CREATED_PUT
      ]
    });

    lambdaFunction.addEventSource(s3PutEventSource);
    transcriptsBucket.grantReadWrite(lambdaFunction);
    audioFilesBucket.grantReadWrite(lambdaFunction);

    // Creating the IAM policy and adding it to our Lambda function
    const adminTranscribePolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['transcribe:*'],
      resources: ['*'],
    });

    lambdaFunction.role?.attachInlinePolicy(
      new iam.Policy(this, 'admin-transcribe', {
        statements: [adminTranscribePolicy],
      }),
    );
  }
}
