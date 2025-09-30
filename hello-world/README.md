# Hello World

This lambda is a simple demonstration function that returns a greeting message. It's useful for testing the ECR workflow and Lambda deployment.

## Features

- Accepts an optional `Name` parameter for personalized greetings
- Returns a simple greeting message
- Full AWS PowerTools instrumentation (logging, tracing, metrics)
- Demonstrates standard response format

## Deployment

- Follow the repo [README](../README.md) to ensure you have the images in your private ECR
- Create a lambda function using the following settings:
  - Type: Container Image 
  - Function name: Hello World
  - Container image URI: {ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/hello-world:LATEST
  - Architecture: arm64
  - **Timeout: Default 1 minute is sufficient**

## Permissions

None required

## Environment Variables

Environment variables are set in the code with default values and can be overridden in the Lambda console:

- `POWERTOOLS_SERVICE_NAME`: Service name for PowerTools (default: "hello-world-lambda")
- `POWERTOOLS_METRICS_NAMESPACE`: CloudWatch metrics namespace (default: "HelloWorld")
- `LOG_LEVEL`: Logging level (default: "INFO")
- `POWERTOOLS_LOGGER_SAMPLE_RATE`: Sample rate for logging (default: "0.1")
- `POWERTOOLS_LOGGER_LOG_EVENT`: Whether to log the full event (default: "false")
- `POWERTOOLS_TRACE_MIDDLEWARES`: Enable trace middlewares (default: "true")

## Parameters

### Input

The lambda accepts an optional `Name` parameter in the Amazon Connect Parameters section:

```json
{
  "Details": {
    "ContactData": {
      "ContactId": "04535341-6712-4b6d-a710-bf5c5df4ba78"
    },
    "Parameters": {
      "Name": "Alice"
    }
  },
  "Name": "ContactFlowEvent"
}
```

- **Type**: String
- **Default**: "World" (if not provided)

### Output

```json
{
  "status-code": 200,
  "data": {
    "name": "Alice",
    "message": "Hello, Alice!"
  }
}
```

## Testing

### AWS Console Testing

**Test with Name parameter:**
```json
{
  "Details": {
    "ContactData": {
      "ContactId": "04535341-6712-4b6d-a710-bf5c5df4ba78"
    },
    "Parameters": {
      "Name": "Alice"
    }
  },
  "Name": "ContactFlowEvent"
}
```

**Sample Response:**
```json
{
  "status-code": 200,
  "data": {
    "name": "Alice",
    "message": "Hello, Alice!"
  }
}
```

**Test without Name parameter (uses default):**
```json
{
  "Details": {
    "ContactData": {
      "ContactId": "04535341-6712-4b6d-a710-bf5c5df4ba78"
    },
    "Parameters": {}
  },
  "Name": "ContactFlowEvent"
}
```

## Version History

See [version.json](version.json) for detailed changelog.
