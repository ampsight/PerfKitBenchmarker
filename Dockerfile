ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}

WORKDIR /pkb

COPY requirements.txt /pkb

RUN pip install -r requirements.txt

# Update package lists and install vim
RUN apt-get update && apt-get install -y vim

# Create the directory for the downloaded packages and set permissions
RUN mkdir -p /mypackages && chmod 777 /mypackages

# Copy necessary files
COPY . /pkb

# Install Python dependencies
RUN pip install -r requirements-testing.txt
RUN pip install -r perfkitbenchmarker/providers/aws/requirements.txt
RUN pip install -r perfkitbenchmarker/providers/ibmcloud/requirements.txt

# Download the make and gcc packages to /mypackages with correct permissions
RUN apt-get update && \
    apt-get download make -o=Dir::Cache::archives=/mypackages && \
    apt-get download gcc -o=Dir::Cache::archives=/mypackages

# Verify the contents of /mypackages
RUN find /mypackages -type f

# Keep the container running (if needed for testing)
CMD tail -f /dev/null
