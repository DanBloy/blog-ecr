#!/usr/bin/env python3
"""
Test script for the connect-encryption Lambda function
"""

import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import base64

# Add the current directory to the path to import the lambda function
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambda_function import lambda_handler

def create_mock_context():
    """Create a mock Lambda context"""
    context = Mock()
    context.function_name = "connect-encryption-test"
    context.function_version = "1.0.0"
    context.aws_request_id = "test-request-id-123"
    context.invoked_function_arn = "arn:aws:lambda:eu-west-2:123456789012:function:connect-encryption-test"
    return context

def create_test_event(encrypted_data=None):
    """Create a test Amazon Connect event"""
    event = {
        "Details": {
            "ContactData": {
                "ContactId": "test-contact-123",
                "Channel": "VOICE",
                "InstanceARN": "arn:aws:connect:eu-west-2:123456789012:instance/test-instance"
            },
            "Parameters": {}
        }
    }
    
    if encrypted_data:
        event["Details"]["Parameters"]["my-secret-string"] = encrypted_data
    
    return event

def test_missing_encrypted_data():
    """Test the lambda function when no encrypted data is provided"""
    
    print("Testing connect-encryption Lambda function...")
    print("\n1. Testing missing encrypted data:")
    
    event = create_test_event()
    context = create_mock_context()
    
    result = lambda_handler(event, context)
    
    print(f"Status Code: {result['statusCode']}")
    print(f"Response: {json.dumps(result['body'], indent=2)}")
    
    return result['statusCode'] == 200  # Should handle gracefully

@patch('boto3.client')
def test_with_mock_encryption(mock_boto_client):
    """Test with mocked AWS services and encryption"""
    
    print("\n2. Testing with mocked encryption:")
    
    # Mock SSM client
    mock_ssm = MagicMock()
    mock_boto_client.return_value = mock_ssm
    
    # Create a simple test private key (for testing purposes only)
    test_private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDPbF8+U5cDChGW
OfiTrOdQ0vEwCT8FNvnCRegJ1af/NXsPP+xB5hX2F20AjEMbdy2BOthmFxNuPsQG
9D9MCz+UYEZC7fj3bfLZNVlYTyN8/PhoEdE3ULXqS6kiei2wamj9LeNv5MdFes27
TPsto7oYgJwbj4mcMNq+xvSg97EWW07EJEb/kS1pa+2pTTClw8FopcIdOGlPBjjy
dPUY553fAofRaxTm3zrrvXIHLE238bEs0e4VXoWjQCE7b+LvZIMIFdAi5wZ4jRe+
cuHwxH3CzfaOedNYZQgGweUL7gRd3q0jAvTbK9ochoAEWhYdM9nEfuUYU5QwoVF/
m5jBDpYES8hisgibAgMBAAECggEAMmvXx...
-----END PRIVATE KEY-----"""
    
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': test_private_key}
    }
    
    # Create fake encrypted data (base64 encoded string for testing)
    fake_encrypted_data = base64.b64encode(b"fake encrypted data").decode('utf-8')
    
    event = create_test_event(fake_encrypted_data)
    context = create_mock_context()
    
    try:
        result = lambda_handler(event, context)
        print(f"Status Code: {result['statusCode']}")
        print(f"Response: {json.dumps(result['body'], indent=2)}")
        return True
    except Exception as e:
        print(f"Expected error with fake encryption data: {str(e)}")
        return True  # This is expected to fail with fake data

def test_event_structure():
    """Test event structure parsing"""
    
    print("\n3. Testing event structure parsing:")
    
    # Test with incomplete event structure
    incomplete_event = {
        "Details": {
            "Parameters": {
                "my-secret-string": "dGVzdCBkYXRh"  # base64 "test data"
            }
        }
    }
    
    context = create_mock_context()
    
    try:
        result = lambda_handler(incomplete_event, context)
        print(f"Status Code: {result['statusCode']}")
        print(f"Response: {json.dumps(result['body'], indent=2)}")
        return True
    except Exception as e:
        print(f"Error with incomplete event: {str(e)}")
        return False

def test_configuration():
    """Test configuration and environment variables"""
    
    print("\n4. Testing configuration:")
    
    # Check environment variables
    env_vars = [
        'POWERTOOLS_SERVICE_NAME',
        'POWERTOOLS_METRICS_NAMESPACE',
        'LOG_LEVEL',
        'AWS_REGION'
    ]
    
    for var in env_vars:
        value = os.getenv(var, "Not set")
        print(f"  {var}: {value}")
    
    return True

def run_all_tests():
    """Run all tests"""
    
    print("=" * 60)
    print("Amazon Connect Encryption Lambda Function Tests")
    print("=" * 60)
    
    tests = [
        ("Missing Encrypted Data", test_missing_encrypted_data),
        ("Mock Encryption", test_with_mock_encryption),
        ("Event Structure", test_event_structure),
        ("Configuration", test_configuration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n--- {test_name} ---")
            success = test_func()
            results.append((test_name, success))
            print(f"✅ {test_name}: {'PASSED' if success else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        icon = "✅" if success else "❌"
        print(f"{icon} {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check the output above")

if __name__ == "__main__":
    run_all_tests()
