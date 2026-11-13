FROM mcr.microsoft.com/playwright/python:v1.55.0-noble
WORKDIR /opt/uat
COPY requirements-uat.txt /opt/uat/requirements-uat.txt
RUN python -m pip install --no-cache-dir -r /opt/uat/requirements-uat.txt
