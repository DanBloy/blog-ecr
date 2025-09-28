# Hello World

This lambda is here to test the ECR workflow. It has no other purpose.

## Deployment

- Follow the repo [README](../README.md) to ensure you have the images in your private ECR
- Create a lambda function using the following settings
  - Type: Container Image 
  - Function name: Hello World
  - Container image URI: {ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/hello-world:LATEST
  - Architecture: arm64

## Permissions

None required

## Envinronment Variables

None Required

## Verify

Use any same test event within the AWS Console

