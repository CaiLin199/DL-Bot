# Use a base image with Python
FROM python:3.8-slim-buster

# Install git
RUN apt-get update && apt-get install -y git

# Set the working directory to /app
WORKDIR /app

# Copy requirements.txt to the container
COPY requirements.txt requirements.txt

# Install the Python dependencies
RUN pip3 install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Start aria2c and the bot
CMD aria2c --enable-rpc --rpc-listen-all=true --rpc-allow-origin-all & python3 main.py



