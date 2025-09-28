# Connect Encryption

This lambda supports this [post](https://bloy.me.uk/amazon-connect-flow-security-keys)

## Deployment

- Follow the repo [README](../README.md) to ensure you have the images in your private ECR
- Create a lambda function using the following settings
  - Type: Container Image 
  - Function name: Connect Encryption
  - Container image URI: {ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/connect-encryption:LATEST
  - Architecture: arm64

## Permissions

Add an inline policy to the role

```
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": [
				"ssm:GetParameter"
			],
			"Resource": "arn:aws:ssm:*:*:parameter/amazon-connect/encryption/*"
		}
	]
}
```

## Envinronment Variables

None Required

## Verify

See the blog

