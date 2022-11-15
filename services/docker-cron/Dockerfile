FROM python:bullseye

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends install -y cron \
    # Remove package lists for smaller image sizes
    && rm -rf /var/lib/apt/lists/* \
    && which cron \
    && rm -rf /etc/cron.*/* \

RUN apt-get install python3-pip

RUN python -m pip install pip --upgrade

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY config.ini /usr/src/app/
COPY entrypoint.sh /usr/src/app/
COPY poll_metadata_and_obs_types.py /usr/src/app/
COPY requirements.txt /usr/src/app/
RUN pip3 install -r requirements.txt

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

# https://manpages.ubuntu.com/manpages/kinetic/man8/cron.8.html
# -f | Stay in foreground mode, don./ec't daemonize.
# -L loglevel | Tell  cron  what to log about jobs (errors are logged regardless of this value) as the sum of the following values:
CMD ["cron","-f", "-L", "2"]
