#!/bin/bash

# Check for Docker
if ! command -v docker &> /dev/null
then
    echo "Docker is not installed."
else
    echo "Docker is installed."
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose is not installed."
else
    echo "Docker Compose is installed."
fi

# Check for Python
if ! command -v python &> /dev/null
then
    echo "Python is not installed."
else
    echo "Python is installed."
fi