ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}

WORKDIR /pkb

COPY requirements.txt /pkb

RUN pip install -r requirements.txt

COPY . /pkb

RUN pip install -r requirements-testing.txt

#CMD python -m unittest discover -s tests -p '*test.py' -v

RUN pip install -r providers/aws/requirements.txt
