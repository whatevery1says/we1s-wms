FROM python:3.7.0-stretch
# @sha256:825141134528aa58f1c0c6c7ad02e080968847338506c23c14a063ac6645bca5

# Install base requirements for a numpy / pandas
RUN pip install cython \
 && pip install pandas

WORKDIR /we1s-wms/

# Install any needed packages specified in requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container
ADD . /

RUN /bin/bash deploy-fix.sh

# Expose port
EXPOSE 5000

ENTRYPOINT ["python", "/we1s-wms/run.py"]
