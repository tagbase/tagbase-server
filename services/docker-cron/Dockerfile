FROM python:bullseye

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends install -y cron \
    # Remove package lists for smaller image sizes
    && rm -rf /var/lib/apt/lists/* \
    && which cron \
    && rm -rf /etc/cron.*/* \

RUN apt-get install python3-pip

RUN python -m pip install pip --upgrade

COPY requirements.txt /requirements.txt

RUN chmod 744 /requirements.txt

RUN pip3 install -r /requirements.txt

COPY entrypoint.sh /entrypoint.sh

RUN chmod 744 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# https://manpages.ubuntu.com/manpages/kinetic/man8/cron.8.html
# -f | Stay in foreground mode, don't daemonize.
# -L loglevel | Tell  cron  what to log about jobs (errors are logged regardless of this value) as the sum of the following values:
CMD ["cron","-f", "-L", "2"]
