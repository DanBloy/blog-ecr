# Use the official AWS Lambda Python 3.13 base image for ARM64
FROM public.ecr.aws/lambda/python:3.13-arm64

# Set default PowerTools environment variables
ENV POWERTOOLS_SERVICE_NAME="hello-world-lambda"
ENV POWERTOOLS_METRICS_NAMESPACE="HelloWorld"
ENV LOG_LEVEL="INFO"
ENV POWERTOOLS_LOGGER_SAMPLE_RATE="0.1"
ENV POWERTOOLS_LOGGER_LOG_EVENT="false"
ENV POWERTOOLS_TRACE_MIDDLEWARES="true"

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY version.json ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["lambda_function.lambda_handler"]
