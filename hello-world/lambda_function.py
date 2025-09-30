import json
import os
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit

# Initialize PowerTools with sensible defaults
logger = Logger(
    service=os.getenv('POWERTOOLS_SERVICE_NAME', 'hello-world-lambda'),
    level=os.getenv('LOG_LEVEL', 'INFO')
)

tracer = Tracer(
    service=os.getenv('POWERTOOLS_SERVICE_NAME', 'hello-world-lambda')
)

metrics = Metrics(
    namespace=os.getenv('POWERTOOLS_METRICS_NAMESPACE', 'HelloWorld'),
    service=os.getenv('POWERTOOLS_SERVICE_NAME', 'hello-world-lambda')
)

@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics
def lambda_handler(event, context):
    """
    Hello World Lambda function with AWS PowerTools
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
    metrics.add_metric(name="HelloWorldInvocation", unit=MetricUnit.Count, value=1)

    # Extract contact information
    contact_data = event.get('Details', {}).get('ContactData', {})
    contact_id = contact_data.get('ContactId', 'unknown')
    
    try:
        # Extract Name from Amazon Connect Parameters
        parameters = event.get('Details', {}).get('Parameters', {})
        name = parameters.get('Name', 'World')
        
        # Log the processing
        logger.info(f"Processing hello message for: {name}")
        
        # Create response
        response = {
            'status-code': 200,
            'data': {
                'name': name,
                'message': f'Hello, {name}!'
            }
        }

        # Log the complete outgoing response
        logger.info("=== OUTGOING RESPONSE TO AMAZON CONNECT ===")
        logger.info("Full response being returned to Amazon Connect", extra={
            "response": response,
            "contact_id": contact_id,
            "success": True,
            "remaining_time_ms": context.get_remaining_time_in_millis()
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        
        error_response = {
            'status-code': 500,
            'data': {
                'error': 'Internal server error',
                'message': str(e)
            }
        }
        
        return error_response
