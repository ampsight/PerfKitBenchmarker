ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}

WORKDIR /pkb

COPY requirements.txt /pkb

RUN pip install -r requirements.txt

RUN apt-get install -y vim

COPY . /pkb

RUN pip install -r requirements-testing.txt

#CMD python -m unittest discover -s tests -p '*test.py' -v

RUN pip install -r perfkitbenchmarker/providers/aws/requirements.txt

RUN pip install -r perfkitbenchmarker/providers/ibmcloud/requirements.txt

# Update package lists and download the make and gcc packages to /tmp
RUN apt-get update && \
    apt-get download make -o=Dir::Cache=/tmp && \
    apt-get download gcc -o=Dir::Cache=/tmp

# Create the /mypackages directory and move the downloaded .deb files there
RUN mkdir -p /mypackages && \
    mv /tmp/var/cache/apt/archives/make_*.deb /pkb/build_packages && \
    mv /tmp/var/cache/apt/archives/gcc_*.deb /pkb/build_packages

# Install vim

CMD tail -f /dev/null
