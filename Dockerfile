# Base image - tried a few others, this one was the easiest and most resilient
FROM python:3.10.0-slim-buster

# Specify root directory in image
WORKDIR /app/dash

# Updating apt & installing
RUN apt-get update \
    && apt-get install -y --no-install-recommends -qq --force-yes cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installing python requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy scraper-cron and apply it
COPY ./scraper-cron /etc/cron.d/scraper-cron
RUN chmod 0644 /etc/cron.d/scraper-cron
RUN crontab /etc/cron.d/scraper-cron
RUN touch /var/log/cron.log

# Copy dash files to image
COPY . /app/dash
RUN chmod 0744 dataLoader.py

# Run cron, run scraper, run dashboard
CMD cron && python3 dataLoader.py && waitress-serve --host=0.0.0.0 --port=80 --call app:returnApp 