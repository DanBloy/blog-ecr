#!/usr/bin/env python3
"""
Test script for the hello-world Lambda function
"""

import json
import sys
import os

# Add the current directory to the path to import the lambda function
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambda_function import lambda_handler

def test_hello_world():
    """Test the hello world lambda function"""
    
    print("Testing hello-world Lambda function...")
    
    # Test 1: Default case (no name provided)
    print("\n1. Testing default case:")
    event1 = {}
    context1 = {}
    
    result1 = lambda_handler(event1, context1)
    print(f"Status Code: {result1['statusCode']}")
    print(f"Response: {result1['body']}")
    
    # Test 2: With name provided
    print("\n2. Testing with name provided:")
    event2 = {"name": "Daniel"}
    context2 = {}
    
    result2 = lambda_handler(event2, context2)
    print(f"Status Code: {result2['statusCode']}")
    print(f"Response: {result2['body']}")
    
    # Test 3: With complex event
    print("\n3. Testing with complex event:")
    event3 = {
        "name": "AWS Lambda",
        "extra_field": "should be ignored"
    }
    context3 = {}
    
    result3 = lambda_handler(event3, context3)
    print(f"Status Code: {result3['statusCode']}")
    print(f"Response: {result3['body']}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_hello_world()
