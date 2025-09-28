#!/bin/bash

# Configuration Example for Lambda ECR Deployment
# Copy this file to .env and customize for your setup
# 
# REQUIRED: Set the AWS_PROFILE environment variable before running the scripts

# AWS Configuration (REQUIRED)
export AWS_PROFILE="your-aws-profile-name"

# Optional: Set specific AWS region (defaults to eu-west-2)
export AWS_REGION="eu-west-2"

# Examples:
# export AWS_PROFILE="my-lambda-profile"
# export AWS_REGION="us-east-1"

# Load this configuration by running:
# source config.example.sh
# or
# cp config.example.sh .env && source .env

if [ -z "$AWS_PROFILE" ] || [ "$AWS_PROFILE" = "your-aws-profile-name" ]; then
    echo "⚠️  Please set AWS_PROFILE to your actual AWS CLI profile name"
else
    echo "Configuration loaded:"
    echo "  AWS Profile: $AWS_PROFILE"
    
    # Auto-detect account ID and region
    if command -v aws >/dev/null 2>&1; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile $AWS_PROFILE 2>/dev/null)
        if [ -n "$AWS_ACCOUNT_ID" ]; then
            echo "  AWS Account: $AWS_ACCOUNT_ID"
            echo "  AWS Region: $AWS_REGION"
            echo "  ECR Registry: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
        fi
    fi
fi

echo ""
echo "Run './push_to_ecr.sh' to build and deploy your Lambda functions"
