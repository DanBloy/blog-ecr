import json
import os
import time
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit

# Initialize PowerTools with sensible defaults
logger = Logger(
    service=os.getenv('POWERTOOLS_SERVICE_NAME', 'async-execution-lambda'),
    level=os.getenv('LOG_LEVEL', 'INFO')
)

tracer = Tracer(
    service=os.getenv('POWERTOOLS_SERVICE_NAME', 'async-execution-lambda')
)

metrics = Metrics(
    namespace=os.getenv('POWERTOOLS_METRICS_NAMESPACE', 'AsyncExecution'),
    service=os.getenv('POWERTOOLS_SERVICE_NAME', 'async-execution-lambda')
)

@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics
def lambda_handler(event, context):
    """
    Async Execution Lambda function that waits for a specified delay before returning
    """

    # Log the complete incoming event
    logger.info("=== INCOMING AMAZON CONNECT EVENT ===")
    logger.info("Full event received from Amazon Connect", extra={
        "event": event,
        "function_name": context.function_name,
        "function_version": context.function_version,
        "aws_request_id": context.aws_request_id,
        "remaining_time_ms": context.get_remaining_time_in_millis()
    })

    # Add custom metric
    metrics.add_metric(name="AsyncExecutionInvocation", unit=MetricUnit.Count, value=1)

    # Extract contact information
    contact_data = event.get('Details', {}).get('ContactData', {})
    contact_id = contact_data.get('ContactId', 'unknown')
    
    try:
        # Extract SecondsDelay from Amazon Connect Parameters
        parameters = event.get('Details', {}).get('Parameters', {})
        seconds_delay = parameters.get('SecondsDelay', 0)
        
        # Validate and convert to integer
        try:
            seconds_delay = int(seconds_delay)
            if seconds_delay < 0:
                seconds_delay = 0
        except (ValueError, TypeError):
            logger.warning(f"Invalid SecondsDelay value: {seconds_delay}, defaulting to 0")
            seconds_delay = 0
        
        # Log the delay and check remaining time
        remaining_time = context.get_remaining_time_in_millis() / 1000
        logger.info(f"Requested delay: {seconds_delay} seconds, Remaining execution time: {remaining_time:.2f} seconds")
        
        # Add delay metric
        metrics.add_metric(name="ExecutionDelay", unit=MetricUnit.Seconds, value=seconds_delay)
        
        # Check if we have enough time
        if seconds_delay > remaining_time - 1:
            logger.warning(f"Requested delay ({seconds_delay}s) exceeds available time ({remaining_time:.2f}s)")
            # Adjust delay to leave 1 second for response
            seconds_delay = max(0, int(remaining_time - 1))
            logger.info(f"Adjusted delay to {seconds_delay} seconds")
        
        # Wait for the specified duration
        if seconds_delay > 0:
            logger.info(f"Starting delay of {seconds_delay} seconds")
            time.sleep(seconds_delay)
            logger.info(f"Completed delay of {seconds_delay} seconds")
        
        # Create response
        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Execution completed after {seconds_delay} seconds',
                'seconds_delay': seconds_delay,
                'version': '1.0.0',
                'runtime': 'python3.13',
                'architecture': 'arm64',
                'powertools': True
            })
        }

        # Log the complete outgoing response
        logger.info("=== OUTGOING RESPONSE TO AMAZON CONNECT ===")
        logger.info("Full response being returned to Amazon Connect", extra={
            "response": response,
            "contact_id": contact_id,
            "success": True,
            "seconds_delay": seconds_delay,
            "remaining_time_ms": context.get_remaining_time_in_millis()
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        
        # Add error metric
        metrics.add_metric(name="ExecutionError", unit=MetricUnit.Count, value=1)
        
        error_response = {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
        
        return error_response
