#!/bin/bash

# Build and Push Script for Lambda ECR Images
# This script scans for lambda functions, checks versions, and pushes to ECR

set -e

# Configuration - Set these via environment variables
AWS_PROFILE="${AWS_PROFILE}"
AWS_REGION="${AWS_REGION:-eu-west-2}"  # Use your preferred region
AWS_ACCOUNT_ID=""  # Will be auto-detected
ECR_REGISTRY_PREFIX=""  # Will be auto-generated
STATE_FILE="build_state.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if AWS CLI is configured with the profile
check_aws_config() {
    print_status "Checking AWS configuration for profile: $AWS_PROFILE"
    
    if ! aws configure list --profile $AWS_PROFILE > /dev/null 2>&1; then
        print_error "AWS profile '$AWS_PROFILE' not found!"
        print_error "Please configure it using:"
        print_error "aws configure --profile $AWS_PROFILE"
        exit 1
    fi
    
    print_success "AWS profile '$AWS_PROFILE' is configured"
}

# Function to authenticate with ECR
ecr_login() {
    print_status "Logging into AWS Public ECR (for base images)..."
    aws ecr-public get-login-password --region us-east-1 --profile $AWS_PROFILE | \
        docker login --username AWS --password-stdin public.ecr.aws
    print_success "Public ECR login successful"
    
    print_status "Logging into private ECR..."
    aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | \
        docker login --username AWS --password-stdin $ECR_REGISTRY_PREFIX
    print_success "Private ECR login successful"
}

# Function to load the current state
load_state() {
    if [ -f "$STATE_FILE" ]; then
        cat "$STATE_FILE"
    else
        echo "{}"
    fi
}

# Function to save the state
save_state() {
    echo "$1" > "$STATE_FILE"
    print_status "State saved to $STATE_FILE"
}

# Function to get version from version.json
get_version() {
    local lambda_dir="$1"
    if [ -f "$lambda_dir/version.json" ]; then
        python3 -c "import json; print(json.load(open('$lambda_dir/version.json'))['version'])"
    else
        echo ""
    fi
}

# Function to check if version has changed
version_changed() {
    local lambda_name="$1"
    local current_version="$2"
    local state="$3"
    
    local last_version=$(echo "$state" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('$lambda_name', {}).get('version', ''))
except:
    print('')
")
    
    if [ "$current_version" != "$last_version" ]; then
        return 0  # True - version changed
    else
        return 1  # False - version unchanged
    fi
}

# Function to get repository metadata from version.json
get_repo_metadata() {
    local lambda_dir="$1"
    local field="$2"
    
    if [ -f "$lambda_dir/version.json" ]; then
        python3 -c "
import json
try:
    with open('$lambda_dir/version.json') as f:
        data = json.load(f)
        repo = data.get('repository', {})
        value = repo.get('$field', '')
        if isinstance(value, list):
            print(json.dumps(value))
        else:
            print(value)
except:
    print('')
"
    else
        echo ""
    fi
}

# Function to create ECR repository if it doesn't exist
create_ecr_repo_if_needed() {
    local repo_name="$1"
    local lambda_name="$2"
    local lambda_dir="$3"
    
    print_status "Checking if private ECR repository exists: $repo_name"
    
    # Check if repository exists
    if aws ecr describe-repositories --repository-names "$repo_name" --region $AWS_REGION --profile $AWS_PROFILE > /dev/null 2>&1; then
        print_status "Repository $repo_name already exists"
        return 0
    fi
    
    print_status "Repository $repo_name does not exist, creating it..."
    
    # Get repository metadata from version.json
    local short_desc=$(get_repo_metadata "$lambda_dir" "short_description")
    local about=$(get_repo_metadata "$lambda_dir" "about")
    local usage=$(get_repo_metadata "$lambda_dir" "usage")
    
    # Use defaults if not provided
    if [ -z "$short_desc" ]; then
        short_desc="Lambda function: $lambda_name"
    fi
    
    if [ -z "$about" ]; then
        about="Containerized Lambda function built and deployed automatically from source code."
    fi
    
    if [ -z "$usage" ]; then
        usage="Deploy to AWS Lambda using container image. Check function documentation for specific usage instructions."
    fi
    
    # Create the repository (private ECR doesn't support catalog data)
    print_status "Creating private ECR repository with basic configuration"
    
    if aws ecr create-repository \
        --repository-name "$repo_name" \
        --region $AWS_REGION \
        --profile $AWS_PROFILE > /dev/null 2>&1; then
        print_success "Successfully created private ECR repository: $repo_name"
        
        # Set lifecycle policy to manage image retention
        local lifecycle_policy='{
            "rules": [
                {
                    "rulePriority": 1,
                    "description": "Keep last 3 images",
                    "selection": {
                        "tagStatus": "any",
                        "countType": "imageCountMoreThan",
                        "countNumber": 3
                    },
                    "action": {
                        "type": "expire"
                    }
                }
            ]
        }'
        
        echo "$lifecycle_policy" | aws ecr put-lifecycle-policy \
            --repository-name "$repo_name" \
            --lifecycle-policy-text file:///dev/stdin \
            --region $AWS_REGION \
            --profile $AWS_PROFILE > /dev/null 2>&1
        
        print_status "Applied lifecycle policy to manage image retention"
        
        # Wait a moment for the repository to be fully created
        sleep 2
        
        print_status "Repository will be available at: $ECR_REGISTRY_PREFIX/$repo_name"
    else
        print_error "Failed to create private ECR repository: $repo_name"
        return 1
    fi
}

# Function to build and push Docker image
build_and_push() {
    local lambda_dir="$1"
    local lambda_name="$2"
    local version="$3"
    
    # Construct ECR repository name
    local ecr_repo="$ECR_REGISTRY_PREFIX/$lambda_name"
    local repo_name="$lambda_name"
    
    # Create repository if it doesn't exist
    if ! create_ecr_repo_if_needed "$repo_name" "$lambda_name" "$lambda_dir"; then
        print_error "Failed to ensure repository exists, skipping build"
        return 1
    fi
    
    print_status "Building Docker image for $lambda_name:$version"
    
    # Ensure buildx is available and create/use a builder that supports ARM64
    if ! docker buildx inspect lambda-builder >/dev/null 2>&1; then
        print_status "Creating Docker buildx builder for multi-platform builds..."
        docker buildx create --name lambda-builder --driver docker-container --bootstrap >/dev/null 2>&1 || true
    fi
    
    # Build the Docker image with explicit platform specification
    print_status "Building ARM64 image with buildx..."
    docker buildx build \
        --builder lambda-builder \
        --platform linux/arm64 \
        --tag "$lambda_name:$version" \
        --load \
        "$lambda_dir"
    
    # Tag for ECR
    docker tag "$lambda_name:$version" "$ecr_repo:$version"
    docker tag "$lambda_name:$version" "$ecr_repo:LATEST"
    
    print_status "Pushing $lambda_name:$version to ECR repository: $ecr_repo"
    
    # Push both versioned and LATEST tags
    docker push "$ecr_repo:$version"
    docker push "$ecr_repo:LATEST"
    
    print_success "Successfully pushed $lambda_name:$version to $ecr_repo"
    
    # Clean up local images to save space
    docker rmi "$lambda_name:$version" "$ecr_repo:$version" "$ecr_repo:LATEST" || true
}

# Function to update state
update_state() {
    local lambda_name="$1"
    local version="$2"
    local state="$3"
    
    echo "$state" | python3 -c "
import json, sys
data = json.load(sys.stdin)
data['$lambda_name'] = {
    'version': '$version',
    'last_build': '$(date -u +"%Y-%m-%dT%H:%M:%SZ")'
}
print(json.dumps(data, indent=2))
"
}

# Main execution
main() {
    # Validate required environment variables
    if [ -z "$AWS_PROFILE" ]; then
        print_error "AWS_PROFILE environment variable is required"
        print_error "Example: export AWS_PROFILE=my-profile"
        exit 1
    fi
    
    # Auto-detect AWS account ID and set ECR registry prefix
    print_status "Detecting AWS account information..."
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile $AWS_PROFILE)
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        print_error "Failed to get AWS account ID. Check your AWS credentials."
        exit 1
    fi
    
    ECR_REGISTRY_PREFIX="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    print_status "Starting Lambda ECR build and push process..."
    print_status "Using AWS Profile: $AWS_PROFILE"
    print_status "Using AWS Account: $AWS_ACCOUNT_ID"
    print_status "Using AWS Region: $AWS_REGION"
    print_status "Using ECR Registry: $ECR_REGISTRY_PREFIX"
    
    # Check prerequisites
    check_aws_config
    
    # Login to ECR
    ecr_login
    
    # Load current state
    current_state=$(load_state)
    updated_state="$current_state"
    
    # Find all lambda directories (those containing version.json)
    lambda_dirs=$(find . -maxdepth 2 -name "version.json" -not -path "./.git/*" | sed 's|/version.json||' | sed 's|^./||')
    
    if [ -z "$lambda_dirs" ]; then
        print_warning "No lambda functions found (no version.json files)"
        exit 0
    fi
    
    built_count=0
    
    # Process each lambda directory
    for lambda_dir in $lambda_dirs; do
        lambda_name=$(basename "$lambda_dir")
        
        print_status "Processing lambda: $lambda_name"
        
        # Check if Dockerfile exists
        if [ ! -f "$lambda_dir/Dockerfile" ]; then
            print_warning "Skipping $lambda_name: No Dockerfile found"
            continue
        fi
        
        # Get current version
        current_version=$(get_version "$lambda_dir")
        
        if [ -z "$current_version" ]; then
            print_warning "Skipping $lambda_name: No version found in version.json"
            continue
        fi
        
        print_status "Current version for $lambda_name: $current_version"
        
        # Check if version has changed
        if version_changed "$lambda_name" "$current_version" "$updated_state"; then
            print_status "Version changed for $lambda_name, building and pushing..."
            
            # Build and push
            build_and_push "$lambda_dir" "$lambda_name" "$current_version"
            
            # Update state
            updated_state=$(update_state "$lambda_name" "$current_version" "$updated_state")
            
            built_count=$((built_count + 1))
        else
            print_status "No version change for $lambda_name, skipping build"
        fi
    done
    
    # Save updated state
    save_state "$updated_state"
    
    if [ $built_count -eq 0 ]; then
        print_success "No new versions to build. All lambdas are up to date."
    else
        print_success "Successfully built and pushed $built_count lambda function(s)"
    fi
    
    print_success "Build and push process completed!"
}

# Check if script is being sourced or executed
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
