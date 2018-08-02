FROM python:3

# Install base requirements for a pandas / flask application
RUN pip3 install pandas flask

WORKDIR /

# Install any needed packages specified in requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container
ADD . /

RUN deploy-fix.sh

# Expose port
EXPOSE 5000

ENTRYPOINT ["python", "/run.py"]
