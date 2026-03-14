# syntax=docker/dockerfile:1
# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set work directory
WORKDIR /code

# Install system dependencies (Moved up to cache effectively)
RUN apt-get update && apt-get install -y make

# Copy requirements file (Assumes build context is project root)
COPY requirements.txt /code/

# Fix the ENV format from "ENV key value" to "ENV key=value"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies with BuildKit cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --default-timeout=1000 -r requirements.txt
# Install system dependencies
RUN apt-get update && apt-get install -y make

# Copy project files
COPY . /code/

# Ensure database file directory exists
RUN mkdir -p /code/db