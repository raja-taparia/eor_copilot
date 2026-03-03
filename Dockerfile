FROM python:3.10-slim

# set working directory inside container
WORKDIR /app

# copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy application source
COPY . .

# ensure Python can import the package rooted at /app
ENV PYTHONPATH=/app
