# Async Execution Lambda

This lambda waits for a specified duration (SecondsDelay parameter) and then returns a 200 status code. It's useful for testing asynchronous execution patterns and delays in workflows.

## Features

- Accepts a `SecondsDelay` parameter to control execution time
- Returns status code 200 after the delay completes
- Includes safety checks to prevent exceeding Lambda timeout
- Full AWS PowerTools instrumentation (logging, tracing, metrics)
- Validates input parameters and handles edge cases

## Deployment

- Follow the repo [README](../README.md) to ensure you have the images in your private ECR
- Create a lambda function using the following settings:
  - Type: Container Image 
  - Function name: Async Execution
  - Container image URI: {ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/async-execution:LATEST
  - Architecture: arm64
  - **Timeout: Set to the maximum delay you expect plus 5 seconds (e.g., for 30 second delays, set timeout to 35 seconds). Default recommendation: 1 minute**

## Permissions

None required

## Environment Variables

Environment variables are set in the code with default values and can be overridden in the Lambda console:

- `POWERTOOLS_SERVICE_NAME`: Service name for PowerTools (default: "async-execution-lambda")
- `POWERTOOLS_METRICS_NAMESPACE`: CloudWatch metrics namespace (default: "AsyncExecution")
- `LOG_LEVEL`: Logging level (default: "INFO")
- `POWERTOOLS_LOGGER_SAMPLE_RATE`: Sample rate for logging (default: "0.1")
- `POWERTOOLS_LOGGER_LOG_EVENT`: Whether to log the full event (default: "false")
- `POWERTOOLS_TRACE_MIDDLEWARES`: Enable trace middlewares (default: "true")

## Parameters

### Input

The lambda accepts a `SecondsDelay` parameter in the Amazon Connect Parameters section:

```json
{
  "Details": {
    "ContactData": {
      "ContactId": "04535341-6712-4b6d-a710-bf5c5df4ba78"
    },
    "Parameters": {
      "SecondsDelay": "3"
    }
  },
  "Name": "ContactFlowEvent"
}
```

- **Type**: String or Integer (will be converted to integer)
- **Default**: 0 (no delay)
- **Validation**: Automatically clamps negative values to 0
- **Safety**: If the requested delay exceeds available Lambda execution time, it will be adjusted automatically

### Output

```json
{
  "status-code": 200,
  "data": {
    "seconds-delay": "3",
    "message": "Execution completed after 3 seconds"
  }
}
```

## Testing

A sample [contact flow](./contact-flow/AsyncExecution.json) is provided, import andf assign a phone numnber.

### Local Testing

Run the included tests:

```bash
cd async-execution
pip install -r requirements.txt pytest
python test_lambda.py
```

### AWS Console Testing

Use the following test event:

**Test with Amazon Connect format (recommended):**
```json
{
  "Details": {
    "ContactData": {
      "ContactId": "04535341-6712-4b6d-a710-bf5c5df4ba78"
    },
    "Parameters": {
      "SecondsDelay": "3"
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
    "seconds-delay": "3",
    "message": "Execution completed after 3 seconds"
  }
}
```

**Test with no delay:**
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

## Use Cases

1. **Testing Asynchronous Workflows**: Simulate long-running operations
2. **Timeout Testing**: Verify timeout handling in calling services
3. **Load Testing**: Create predictable delays for performance testing
4. **Step Function Testing**: Test state machine wait conditions and error handling
5. **Amazon Connect Testing**: Simulate delays in contact flows

## Notes

- The Lambda includes automatic timeout protection - it will adjust the delay if it would exceed available execution time
- Metrics are published to CloudWatch under the `AsyncExecution` namespace
- All executions are fully traced with AWS X-Ray when enabled
- Logs include detailed information about the delay execution
- **Remember to set the Lambda timeout in the console to accommodate your maximum expected delay (Max 60s)**

## Version History

See [version.json](version.json) for detailed changelog.
