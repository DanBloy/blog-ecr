# Lambda Functions Update Summary

## Overview
Updated all three lambda functions for consistency with Amazon Connect integration patterns, response formats, and documentation.

## Changes Applied to All Lambdas

### 1. Response Format Standardization
**Before:**
```json
{
  "statusCode": 200,
  "headers": {...},
  "body": "{...}"
}
```

**After (Consistent across all lambdas):**
```json
{
  "status-code": 200,
  "data": {
    "key-name": "value",
    "message": "descriptive message"
  }
}
```

**Key Changes:**
- Use kebab-case for response keys (`status-code` instead of `statusCode`)
- Simplified structure: removed headers, body wrapping
- All data now in `data` object
- Consistent error format with `status-code: 500`

### 2. Input Parameter Conventions
**Amazon Connect Parameters:**
- All input parameters use **PascalCase** (e.g., `SecondsDelay`, `Name`)
- Parameters extracted from `event['Details']['Parameters']`
- Follows AWS/Amazon Connect naming conventions

### 3. Environment Variables
**Before:**
- Set in Dockerfile with ENV statements

**After:**
- Set in code with `os.getenv()` and default values
- Can be overridden in Lambda console
- Dockerfiles simplified (removed ENV statements)

### 4. Documentation Updates
All READMEs now include:
- Clear timeout recommendations
- Environment variable override instructions
- Consistent parameter documentation
- Sample input/output in correct format
- Version history reference

## Lambda-Specific Changes

### async-execution (v1.0.0 → v1.1.0)

**Code Changes:**
- Parameter: `SecondsDelay` (PascalCase)
- Response: `seconds-delay` (kebab-case) as string
- Simplified response structure

**Example Response:**
```json
{
  "status-code": 200,
  "data": {
    "seconds-delay": "3",
    "message": "Execution completed after 3 seconds"
  }
}
```

**README Updates:**
- Added timeout configuration instructions (set to max delay + 5 seconds, default 1 minute)
- Environment variable override section
- Updated all examples with new format

### hello-world (v1.0.1 → v1.1.0)

**Code Changes:**
- Parameter: `Name` (PascalCase) from `Details.Parameters`
- Previously extracted from event root, now from Parameters
- Response: simplified to match standard format

**Example Response:**
```json
{
  "status-code": 200,
  "data": {
    "name": "Alice",
    "message": "Hello, Alice!"
  }
}
```

**README Updates:**
- Complete rewrite with proper structure
- Environment variable override section
- Sample inputs/outputs
- Timeout recommendation (1 minute default)

### connect-encryption (v1.0.0 - no version change)

**Status:**
- Already using PascalCase for parameters (`my-secret-string`, `key-id` are from Connect, not user-defined)
- Already using correct response format (`status-code`, `data`)
- No code changes needed

**README Updates:**
- Comprehensive documentation added
- Environment variable override section
- Input/output examples
- Private key setup instructions
- Architecture notes
- Timeout recommendation (1 minute default)

## File Changes Summary

### Updated Files:
1. **async-execution/**
   - `lambda_function.py` - Response format, parameter extraction
   - `Dockerfile` - Removed ENV statements
   - `version.json` - Incremented to 1.1.0, added changelog
   - `README.md` - Complete update
   - `test_lambda.py` - Updated assertions for new format

2. **hello-world/**
   - `lambda_function.py` - Response format, parameter extraction
   - `Dockerfile` - Removed ENV statements  
   - `version.json` - Incremented to 1.1.0, added changelog
   - `README.md` - Complete rewrite
   - `test_lambda.py` - Created/updated with new format

3. **connect-encryption/**
   - `Dockerfile` - Removed ENV statements
   - `README.md` - Complete rewrite with comprehensive documentation
   - No code changes (already compliant)

4. **push_to_ecr.sh**
   - Added AWS Public ECR authentication for base image pulls

## Testing

All lambdas include updated test files that verify:
- Correct response format
- Parameter extraction from `Details.Parameters`
- PascalCase parameter handling
- Default value behavior
- Error handling

Run tests:
```bash
cd <lambda-directory>
pip install -r requirements.txt pytest
python test_lambda.py
```

## Deployment

To deploy updated lambdas:

```bash
export AWS_PROFILE=your-profile
./push_to_ecr.sh
```

The script will:
1. Authenticate with AWS Public ECR (for base images)
2. Authenticate with your private ECR
3. Build and push all lambdas with version changes
4. Update build state

## Configuration Checklist

When deploying/updating lambdas in AWS Console:

- [ ] Set timeout appropriately:
  - async-execution: Max delay + 5 seconds (default: 1 minute)
  - hello-world: 1 minute (default sufficient)
  - connect-encryption: 1 minute (default sufficient)

- [ ] Override environment variables if needed:
  - `LOG_LEVEL` - Change from INFO to DEBUG for troubleshooting
  - `POWERTOOLS_SERVICE_NAME` - Customize service name
  - `POWERTOOLS_METRICS_NAMESPACE` - Customize metrics namespace
  - `AWS_REGION` (connect-encryption only) - Override region

- [ ] Ensure permissions are set (connect-encryption requires SSM access)

## Naming Conventions Summary

| Context | Convention | Example |
|---------|-----------|---------|
| Input Parameters (Amazon Connect) | PascalCase | `SecondsDelay`, `Name` |
| Response Keys | kebab-case | `status-code`, `seconds-delay` |
| Environment Variables | UPPER_SNAKE_CASE | `LOG_LEVEL`, `AWS_REGION` |
| Python Variables | snake_case | `seconds_delay`, `contact_id` |

## Version History

| Lambda | Previous | New | Changes |
|--------|----------|-----|---------|
| async-execution | 1.0.0 | 1.1.0 | Response format, PascalCase params |
| hello-world | 1.0.1 | 1.1.0 | Response format, PascalCase params, parameter extraction |
| connect-encryption | 1.0.0 | 1.0.0 | Documentation only (already compliant) |
