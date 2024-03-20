# Use the official Python image as a base
FROM python:3.8.10

# Set the working directory in the container
WORKDIR /testing

# ENV SSL_CERT_DIR /usr/lib/ssl/certs

# Install system dependencies for Azure Speech SDK
RUN apt-get update

RUN apt-get install -y alsa-utils libasound2 build-essential libssl-dev ca-certificates wget



# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any Python dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

EXPOSE $PORT

# Command to run the Flask application with the port specified by the environment variable
CMD ["python", "main.py", "--port", "$PORT"]
