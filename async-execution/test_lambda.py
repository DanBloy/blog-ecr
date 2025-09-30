import json
import pytest
from lambda_function import lambda_handler


class MockContext:
    """Mock Lambda context for testing"""
    def __init__(self):
        self.function_name = "async-execution-test"
        self.function_version = "$LATEST"
        self.aws_request_id = "test-request-id"
        self.remaining_time_in_millis = 30000  # 30 seconds
    
    def get_remaining_time_in_millis(self):
        return self.remaining_time_in_millis


def test_lambda_handler_with_delay():
    """Test lambda handler with a delay"""
    event = {
        "Details": {
            "Parameters": {
                "SecondsDelay": "2"
            }
        }
    }
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['status-code'] == 200
    assert response['data']['seconds-delay'] == '2'
    assert 'message' in response['data']


def test_lambda_handler_with_integer_delay():
    """Test lambda handler with integer parameter"""
    event = {
        "Details": {
            "Parameters": {
                "SecondsDelay": 3
            }
        }
    }
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['status-code'] == 200
    assert response['data']['seconds-delay'] == '3'


def test_lambda_handler_no_delay():
    """Test lambda handler with no delay (default 0)"""
    event = {}
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['status-code'] == 200
    assert response['data']['seconds-delay'] == '0'


def test_lambda_handler_invalid_delay():
    """Test lambda handler with invalid delay value"""
    event = {
        "Details": {
            "Parameters": {
                "SecondsDelay": "invalid"
            }
        }
    }
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['status-code'] == 200
    assert response['data']['seconds-delay'] == '0'


def test_lambda_handler_negative_delay():
    """Test lambda handler with negative delay"""
    event = {
        "Details": {
            "Parameters": {
                "SecondsDelay": -5
            }
        }
    }
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['status-code'] == 200
    assert response['data']['seconds-delay'] == '0'


def test_lambda_handler_with_contact_data():
    """Test lambda handler with Amazon Connect contact data and Parameters"""
    event = {
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
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    assert response['status-code'] == 200
    assert response['data']['seconds-delay'] == '3'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
