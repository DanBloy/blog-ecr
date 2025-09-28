import base64
import json
import os
from typing import Dict, Any, Optional

import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

# Pre-import all required libraries at module level to avoid timeout
try:
    import aws_encryption_sdk
    from aws_cryptographic_material_providers.mpl import AwsCryptographicMaterialProviders
    from aws_cryptographic_material_providers.mpl.config import MaterialProvidersConfig
    from aws_cryptographic_material_providers.mpl.models import CreateRawRsaKeyringInput, PaddingScheme
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    
    # Initialize material providers at module level
    MAT_PROVIDERS = AwsCryptographicMaterialProviders(config=MaterialProvidersConfig())
    
    # Create encryption client with compatible commitment policy for Amazon Connect
    # Amazon Connect uses older algorithms that don't support key commitment
    ENCRYPTION_CLIENT = aws_encryption_sdk.EncryptionSDKClient(
        commitment_policy=aws_encryption_sdk.CommitmentPolicy.FORBID_ENCRYPT_ALLOW_DECRYPT
    )
    
    logger = Logger(
        service=os.getenv('POWERTOOLS_SERVICE_NAME', 'connect-encryption-lambda'),
        level=os.getenv('LOG_LEVEL', 'INFO')
    )
    logger.info("Successfully initialized encryption libraries at module level")
    
except ImportError as e:
    logger = Logger(
        service=os.getenv('POWERTOOLS_SERVICE_NAME', 'connect-encryption-lambda'),
        level=os.getenv('LOG_LEVEL', 'INFO')
    )
    logger.error(f"Failed to import encryption libraries: {str(e)}")
    MAT_PROVIDERS = None
    ENCRYPTION_CLIENT = None

# Initialize PowerTools
tracer = Tracer(service=os.getenv('POWERTOOLS_SERVICE_NAME', 'connect-encryption-lambda'))
metrics = Metrics(
    namespace=os.getenv('POWERTOOLS_METRICS_NAMESPACE', 'ConnectEncryption'),
    service=os.getenv('POWERTOOLS_SERVICE_NAME', 'connect-encryption-lambda')
)


class ConnectDecryption:
    """Fast Amazon Connect decryption service with pre-initialized components"""
    
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'eu-west-2')
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        logger.info("Initialized Connect decryption service")
    
    @tracer.capture_method
    def get_private_key_pem(self, key_id: str) -> str:
        """Get private key PEM from Parameter Store using key ID"""
        try:
            # Use key-id to construct the parameter name
            parameter_name = f"/amazon-connect/encryption/{key_id}/private-key"
            
            response = self.ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=True
            )
            
            logger.info(f"Successfully retrieved private key from Parameter Store for key ID: {key_id}")
            return response['Parameter']['Value']
            
        except Exception as e:
            logger.error(f"Failed to get private key for key ID {key_id}: {str(e)}")
            raise
    
    @tracer.capture_method
    def decrypt_data(self, encrypted_data: str, key_id: str) -> str:
        """Decrypt the encrypted data from Amazon Connect using pre-initialized components"""
        try:
            logger.info(f"Starting decryption for key ID: {key_id}")
            
            # Check if libraries are available
            if MAT_PROVIDERS is None or ENCRYPTION_CLIENT is None:
                raise RuntimeError("Encryption libraries not properly initialized")
            
            # Base64 decode
            encrypted_bytes = base64.b64decode(encrypted_data)
            logger.info(f"Decoded {len(encrypted_bytes)} bytes")
            
            # Get private key using the key ID
            private_key_pem = self.get_private_key_pem(key_id)
            logger.info("Retrieved private key, preparing for keyring creation")
            
            # For AWS Cryptographic Material Providers Library, pass the PEM directly
            # The library expects PEM format, not DER
            keyring_input = CreateRawRsaKeyringInput(
                key_namespace="AmazonConnect",
                key_name=key_id,
                private_key=private_key_pem.encode('utf-8'),  # Use PEM directly
                padding_scheme=PaddingScheme.OAEP_SHA512_MGF1
            )
            
            keyring = MAT_PROVIDERS.create_raw_rsa_keyring(input=keyring_input)
            logger.info(f"Created keyring for key ID: {key_id}")
            
            # Decrypt using pre-initialized client
            logger.info("Starting decryption operation")
            decrypted_bytes, decrypt_header = ENCRYPTION_CLIENT.decrypt(
                source=encrypted_bytes,
                keyring=keyring
            )
            
            # Convert to string
            decrypted_text = decrypted_bytes.decode('utf-8')
            logger.info(f"Successfully decrypted {len(decrypted_text)} characters")
            
            metrics.add_metric(name="DecryptionSuccess", unit=MetricUnit.Count, value=1)
            return decrypted_text
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            metrics.add_metric(name="DecryptionError", unit=MetricUnit.Count, value=1)
            raise


def create_connect_response(success: bool, message: str, decrypted_data: Optional[str] = None, 
                          contact_id: str = "unknown", request_id: str = "unknown", 
                          error: str = None) -> Dict[str, Any]:
    """Create Amazon Connect compatible response"""
    
    status_code = 200 if success else 500
    
    # Build data object
    data = {
        "success": success,
        "message": message,
        "contactId": contact_id,
        "requestId": request_id
    }
    
    if success and decrypted_data:
        data["decryptedData"] = decrypted_data
        data["dataLength"] = len(decrypted_data)
    
    # Build response object
    response = {
        "status-code": status_code,
        "data": data
    }
    
    if not success and error:
        response["error"] = error
    
    return response


@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler for Amazon Connect decryption
    
    Expected event structure:
    {
        "Details": {
            "Parameters": {
                "my-secret-string": "base64_encrypted_data",
                "key-id": "encryption_key_id"
            },
            "ContactData": {
                "ContactId": "contact_id"
            }
        }
    }
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
    
    # Log remaining time for debugging
    remaining_time = context.get_remaining_time_in_millis()
    logger.info(f"Lambda started with {remaining_time}ms remaining")
    
    # Extract contact information
    contact_data = event.get('Details', {}).get('ContactData', {})
    contact_id = contact_data.get('ContactId', 'unknown')
    
    # Extract parameters
    parameters = event.get('Details', {}).get('Parameters', {})
    encrypted_data = parameters.get('my-secret-string')
    key_id = parameters.get('key-id')
    
    logger.info("Processing decryption request", extra={
        "contact_id": contact_id,
        "has_encrypted_data": bool(encrypted_data),
        "has_key_id": bool(key_id),
        "encrypted_data_length": len(encrypted_data) if encrypted_data else 0,
        "remaining_time_ms": remaining_time
    })
    
    try:
        # Validate inputs
        if not encrypted_data:
            return create_connect_response(
                success=False,
                message="Missing encrypted data parameter 'my-secret-string'",
                contact_id=contact_id,
                request_id=context.aws_request_id,
                error="Missing required parameter"
            )
        
        if not key_id:
            return create_connect_response(
                success=False,
                message="Missing key ID parameter 'key-id'",
                contact_id=contact_id,
                request_id=context.aws_request_id,
                error="Missing required parameter"
            )
        
        # Initialize decryption service and decrypt
        start_time = context.get_remaining_time_in_millis()
        decryption_service = ConnectDecryption()
        decrypted_data = decryption_service.decrypt_data(encrypted_data, key_id)
        end_time = context.get_remaining_time_in_millis()
        
        logger.info(f"Decryption took {start_time - end_time}ms")
        
        # Log the decrypted result (remove in production for security)
        logger.info(f"Decryption successful. Decrypted data: {decrypted_data}")
        
        # Return success response
        response = create_connect_response(
            success=True,
            message="Data decrypted successfully",
            decrypted_data=decrypted_data,
            contact_id=contact_id,
            request_id=context.aws_request_id
        )
        
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
        logger.error("Decryption process failed", extra={
            "error": str(e),
            "contact_id": contact_id,
            "error_type": type(e).__name__,
            "remaining_time_ms": context.get_remaining_time_in_millis()
        })
        
        error_response = create_connect_response(
            success=False,
            message="Decryption failed",
            contact_id=contact_id,
            request_id=context.aws_request_id,
            error=str(e)
        )
        
        # Log the complete error response
        logger.error("=== ERROR RESPONSE TO AMAZON CONNECT ===")
        logger.error("Full error response being returned to Amazon Connect", extra={
            "response": error_response,
            "contact_id": contact_id,
            "success": False,
            "error": str(e),
            "remaining_time_ms": context.get_remaining_time_in_millis()
        })
        
        return error_response
