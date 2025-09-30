import json
import pytest
from lambda_function import lambda_handler


class MockContext:
    """Mock Lambda context for testing"""
    def __init__(self):
        self.function_name = "hello-world-test"
        self.function_version = "$LATEST"
        self.aws_request_id = "test-request-id"
        self.remaining_time_in_millis = 30000  # 30 seconds
    
    def get_remaining_time_in_millis(self):
        return self.remaining_time_in_millis


def test_lambda_handler_with_name():
    """Test lambda handler with a name parameter"""
    event = {
        "Details": {
            "Parameters": {
                "Name": "Alice"
            }
        }
    }
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['status-code'] == 200
    assert response['data']['name'] == 'Alice'
    assert response['data']['message'] == 'Hello, Alice!'


def test_lambda_handler_no_name():
    """Test lambda handler with no name (default 'World')"""
    event = {}
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['status-code'] == 200
    assert response['data']['name'] == 'World'
    assert response['data']['message'] == 'Hello, World!'


def test_lambda_handler_with_contact_data():
    """Test lambda handler with Amazon Connect contact data"""
    event = {
        "Details": {
            "ContactData": {
                "ContactId": "04535341-6712-4b6d-a710-bf5c5df4ba78"
            },
            "Parameters": {
                "Name": "Bob"
            }
        },
        "Name": "ContactFlowEvent"
    }
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['status-code'] == 200
    assert response['data']['name'] == 'Bob'
    assert response['data']['message'] == 'Hello, Bob!'


def test_lambda_handler_empty_parameters():
    """Test lambda handler with empty parameters"""
    event = {
        "Details": {
            "Parameters": {}
        }
    }
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['status-code'] == 200
    assert response['data']['name'] == 'World'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
