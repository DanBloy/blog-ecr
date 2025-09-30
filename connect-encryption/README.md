# Connect Encryption

This lambda decrypts customer input data from Amazon Connect contact flows using AWS Encryption SDK v3.x. It supports the workflow described in this [blog post](https://bloy.me.uk/amazon-connect-flow-security-keys).

## Features

- Decrypts data encrypted by Amazon Connect using RSA keys
- Retrieves private keys securely from AWS Systems Manager Parameter Store
- Full AWS PowerTools instrumentation (logging, tracing, metrics)
- Optimized for low-latency decryption with pre-initialized components
- Uses modern AWS Encryption SDK v3.x with Material Providers Library

## Deployment

- Follow the repo [README](../README.md) to ensure you have the images in your private ECR
- Create a lambda function using the following settings:
  - Type: Container Image 
  - Function name: Connect Encryption
  - Container image URI: {ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/connect-encryption:LATEST
  - Architecture: arm64
  - **Timeout: Default 1 minute is sufficient**

## Permissions

Add an inline policy to the Lambda execution role:

```json
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

## Environment Variables

Environment variables are set in the code with default values and can be overridden in the Lambda console:

- `POWERTOOLS_SERVICE_NAME`: Service name for PowerTools (default: "connect-encryption-lambda")
- `POWERTOOLS_METRICS_NAMESPACE`: CloudWatch metrics namespace (default: "ConnectEncryption")
- `LOG_LEVEL`: Logging level (default: "INFO")
- `AWS_REGION`: AWS region for SSM Parameter Store (default: "eu-west-2")

## Parameters

### Input

The lambda expects parameters from Amazon Connect in the following format:

```json
{
  "Details": {
    "Parameters": {
      "my-secret-string": "base64_encoded_encrypted_data",
      "key-id": "encryption_key_identifier"
    },
    "ContactData": {
      "ContactId": "04535341-6712-4b6d-a710-bf5c5df4ba78"
    }
  }
}
```

**Parameters:**
- `my-secret-string`: Base64-encoded encrypted data from Amazon Connect
- `key-id`: The encryption key identifier used to locate the private key in Parameter Store

**Note:** The parameter names use kebab-case as they come directly from Amazon Connect's encryption flow.

### Output

**Success Response:**
```json
{
  "status-code": 200,
  "data": {
    "success": true,
    "message": "Data decrypted successfully",
    "contactId": "04535341-6712-4b6d-a710-bf5c5df4ba78",
    "requestId": "abc-123-def-456",
    "decryptedData": "the decrypted customer input",
    "dataLength": 28
  }
}
```

**Error Response:**
```json
{
  "status-code": 500,
  "data": {
    "success": false,
    "message": "Decryption failed",
    "contactId": "04535341-6712-4b6d-a710-bf5c5df4ba78",
    "requestId": "abc-123-def-456"
  },
  "error": "Detailed error message"
}
```

## Private Key Setup

The lambda retrieves private keys from AWS Systems Manager Parameter Store. Store your private keys using this naming convention:

```
/amazon-connect/encryption/{key-id}/private-key
```

Where `{key-id}` matches the key identifier used in your Amazon Connect encryption configuration.

**Example:**
If your `key-id` is `my-connect-key`, store the private key PEM at:
```
/amazon-connect/encryption/my-connect-key/private-key
```

Make sure the parameter is created as a **SecureString** type for encryption at rest.

## Testing

See the [blog post](https://bloy.me.uk/amazon-connect-flow-security-keys) for complete testing instructions including:
- Setting up encryption keys in Amazon Connect
- Configuring contact flows to use encryption
- Testing the full encryption/decryption workflow

## Architecture Notes

- Uses AWS Encryption SDK v3.x with `EncryptionSDKClient` and Raw RSA keyrings
- Encryption libraries are pre-imported at module level to reduce cold start latency
- Compatible with Amazon Connect's OAEP SHA-512 MGF1 padding scheme
- Supports older algorithm suites without key commitment (required for Amazon Connect compatibility)

## Version History

See [version.json](version.json) for detailed changelog.
