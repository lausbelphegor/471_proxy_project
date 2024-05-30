# Use the official Python image from the Docker Hub, specifying the version 3.10.5
FROM python:3.10.5-slim

# Install dependencies for tkinter and other packages
RUN apt-get update && apt-get install -y \
    python3-tk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Run the application
CMD ["python", "main.py"]
