FROM jjuanda/numpy-pandas

WORKDIR /

# Install any needed packages specified in requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container
ADD . /

RUN /bin/bash deploy-fix.sh

# Expose port
EXPOSE 5000

ENTRYPOINT ["python", "/run.py"]
