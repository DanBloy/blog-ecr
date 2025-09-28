# Lambda ECR Deployment Repository

This repository contains Lambda functions that are automatically built and deployed to Amazon ECR (Elastic Container Registry) for use within your AWS account.

The images are referenced within the [blog](https://bloy.me.uk/)

## Repository Structure

```
├── hello-world/            # Example Lambda function
│   ├── Dockerfile          # Container definition
│   ├── lambda_function.py  # Lambda handler code
│   ├── requirements.txt    # Python dependencies
│   ├── version.json        # Version information and changelog
│   └── test_lambda.py      # Local test script
├── push_to_ecr.sh          # Build and deployment script
├── config.example.sh       # Configuration example
├── build_state.json        # State tracking (auto-generated, gitignored)
└── README.md               # This file
```

## Setup Instructions

### 1. Prerequisites

- Docker installed and running
- AWS CLI v2 installed
- Python 3.x installed
- AWS account with ECR permissions

### 2. Configure AWS Credentials

**⚠️ Important**: You must set the AWS_PROFILE environment variable before running the scripts:

```bash
export AWS_PROFILE=your-profile-name
```

#### Option A: Environment Variables (Recommended)

```bash
export AWS_PROFILE=your-profile-name
export AWS_REGION=eu-west-2  # Optional, defaults to eu-west-2
```

#### Option B: AWS CLI Profile

Create a new AWS profile for this project:

```bash
aws configure --profile your-profile-name
```

When prompted, enter:
- AWS Access Key ID: [Your access key]
- AWS Secret Access Key: [Your secret key]
- Default region name: eu-west-2 (or your preferred region)
- Default output format: json

#### Required AWS Permissions

Your AWS credentials need the following permissions:
- `ecr:CreateRepository`
- `ecr:DescribeRepositories`
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:GetDownloadUrlForLayer`
- `ecr:BatchGetImage`
- `ecr:InitiateLayerUpload`
- `ecr:UploadLayerPart`
- `ecr:CompleteLayerUpload`
- `ecr:PutImage`
- `ecr:PutLifecyclePolicy`

### 3. Configuration

#### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AWS_PROFILE` | **Yes** | AWS CLI profile to use |
| `AWS_REGION` | No | AWS region for ECR repositories (defaults to `eu-west-2`) |

#### Set Your Configuration

```bash
# Required
export AWS_PROFILE=your-profile-name

# Optional (defaults to eu-west-2)
export AWS_REGION=us-east-1

# Example
export AWS_PROFILE=my-lambda-profile
export AWS_REGION=eu-west-2
```

### 4. Make Scripts Executable

```bash
chmod +x push_to_ecr.sh
```

### 5. Test the Setup

Run the deployment script:

```bash
./push_to_ecr.sh
```

## Creating New Lambda Functions

To add a new Lambda function:

1. Create a new directory with your function name
2. Add the following files:
   - `Dockerfile` - Container definition
   - `lambda_function.py` - Your Lambda handler
   - `requirements.txt` - Python dependencies
   - `version.json` - Version tracking

### version.json Format

```json
{
  "version": "1.0.0",
  "description": "Function description",
  "python_version": "3.13",
  "architecture": "arm64",
  "powertools_layer": true,
  "repository": {
    "short_description": "Brief one-line description for documentation",
    "about": "Detailed description of what the function does, its purpose, and key features",
    "usage": "Instructions on how to use the function, including input/output examples"
  },
  "changelog": [
    {
      "version": "1.0.0",
      "date": "2025-09-28",
      "changes": [
        "Initial version",
        "Feature description"
      ]
    }
  ]
}
```

### Repository Metadata

The `repository` section in `version.json` is used for documentation purposes:

- **short_description**: Brief description of the function
- **about**: Detailed description of the function's purpose and features
- **usage**: Usage instructions and examples for developers

## Deployment Process

The `push_to_ecr.sh` script automatically:

1. Detects your AWS account ID and region
2. Scans all directories for `version.json` files
3. Compares versions against the state file
4. Creates private ECR repositories if they don't exist
5. Builds Docker images for changed versions
6. Pushes images to your private ECR repositories
7. Updates the state tracking

### ECR Repository Structure

Each Lambda function gets its own private ECR repository:
- Repository format: `{account-id}.dkr.ecr.{region}.amazonaws.com/{function-name}`
- Example: `123456789012.dkr.ecr.eu-west-2.amazonaws.com/hello-world`

Tags format:
- `{version}` (e.g., `1.0.0`)
- `LATEST`

### Lifecycle Management

Repositories are automatically configured with lifecycle policies to:
- Keep the last 10 images
- Automatically delete older images to save storage costs

## Usage in Lambda

After building and pushing your images, create Lambda functions using the container image:

### AWS Console
1. Go to AWS Lambda Console
2. Click "Create function"
3. Select "Container image"
4. Set the image URI to: `{account-id}.dkr.ecr.{region}.amazonaws.com/{function-name}:LATEST`
5. Set architecture to ARM64
6. Create the function

### AWS CLI
```bash
# Get your account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile your-profile)

# Create Lambda function
aws lambda create-function \
  --function-name hello-world-lambda \
  --package-type Image \
  --code ImageUri=$AWS_ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/hello-world:LATEST \
  --role arn:aws:iam::$AWS_ACCOUNT_ID:role/lambda-execution-role \
  --architectures arm64 \
  --timeout 30 \
  --memory-size 512 \
  --region eu-west-2 \
  --profile your-profile
```

## Function Details

### hello-world

A simple Hello World function demonstrating:
- Python 3.13 runtime
- ARM64 architecture
- AWS PowerTools integration
- Proper logging and metrics
- Error handling

**Usage**: Send a JSON payload with an optional `name` field:

```json
{
  "name": "Alice"
}
```

**Response**:

```json
{
  "message": "Hello, Alice!",
  "version": "1.0.1",
  "runtime": "python3.13",
  "architecture": "arm64",
  "powertools": true
}
```

#### Environment Variables

The function includes sensible defaults but can be customized with these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POWERTOOLS_SERVICE_NAME` | `hello-world-lambda` | Service name for logging/tracing |
| `POWERTOOLS_METRICS_NAMESPACE` | `HelloWorld` | CloudWatch metrics namespace |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `POWERTOOLS_LOGGER_SAMPLE_RATE` | `0.1` | Log sampling rate (0.0-1.0) |
| `POWERTOOLS_LOGGER_LOG_EVENT` | `false` | Whether to log the incoming event |
| `POWERTOOLS_TRACE_MIDDLEWARES` | `true` | Enable middleware tracing |


## Troubleshooting

### Common Issues

1. **ECR Login Failed**: Ensure your AWS credentials are properly configured
2. **Docker Build Failed**: Check that Docker is running and you have sufficient disk space
3. **Permission Denied**: Make sure the script is executable (`chmod +x push_to_ecr.sh`)
4. **Repository Creation Failed**: Verify your AWS permissions include ECR access
5. **Lambda Image Not Supported**: Ensure the image was built for ARM64 architecture

### Manual Testing

To manually test your AWS configuration:

```bash
# Test AWS credentials
aws sts get-caller-identity --profile your-profile

# Test ECR access
aws ecr describe-repositories --region eu-west-2 --profile your-profile

# Test image architecture
docker inspect your-account.dkr.ecr.region.amazonaws.com/function:LATEST --format='{{.Architecture}}'
```

### Logs

The script provides colored output:
- Blue: Information
- Green: Success
- Yellow: Warnings
- Red: Errors

## Cost Optimization

- **Lifecycle Policies**: Automatically applied to keep only the last 3 images
- **ARM64 Architecture**: More cost-effective than x86_64 for Lambda
- **Private ECR**: No data transfer costs within the same region

## Security

- **Private Repositories**: Images are only accessible within your AWS account
- **No Hardcoded Credentials**: Uses AWS CLI profiles and IAM roles
- **Least Privilege**: Script only requires necessary ECR permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your Lambda function following the structure guidelines
4. Update the version.json with appropriate changelog
5. Test locally before submitting
6. Create a pull request

### Development Setup

```bash
# Clone the repo
git clone https://github.com/your-username/blog-ecr.git
cd blog-ecr

# Set up your configuration
export AWS_PROFILE=your-development-profile
export AWS_REGION=eu-west-2

# Make scripts executable
chmod +x *.sh

# Test the setup
./push_to_ecr.sh
```

## License

See LICENSE file for details.
