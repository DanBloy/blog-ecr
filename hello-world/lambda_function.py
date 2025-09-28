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
    
    logger.info("Hello World Lambda function started", extra={"event": event})
    
    # Add custom metric
    metrics.add_metric(name="HelloWorldInvocation", unit=MetricUnit.Count, value=1)
    
    try:
        # Extract name from event or use default
        name = event.get('name', 'World')
        
        # Log the processing
        logger.info(f"Processing hello message for: {name}")
        
        # Create response
        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Hello, {name}!',
                'version': '1.0.0',
                'runtime': 'python3.13',
                'architecture': 'arm64',
                'powertools': True
            })
        }
        
        logger.info("Hello World Lambda function completed successfully", 
                   extra={"response": response})
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        
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
