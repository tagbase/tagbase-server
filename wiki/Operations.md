# Introduction

This document provides details of several features associated with tagbase-server operations.

## Audience

It is written primarily for **system administrators** rather than developers or users.

## Features

## Logging

tagbase-server uses a very traditional logging convention where application, HTTP server events and logs are captured. Upon initialization, the tagbase-server stack will begin to capture events and log them _in the application container_. If this were all that were configured then these logs would be lost if the tagbase-server application container were destroyed! Don't worry, keep reading below.

With log preservation in mind, we therefore configured a volume mount within the [docker-compose.yml configuration file](https://github.com/tagbase/tagbase-server/blob/main/docker-compose.yml#L53-L54) which persists an exact copy of the logging artifacts to the physical host machine running tagbase-server virtual host. See below for more details on the logging artifacts.

### What are the log artifacts

When you start tagbase-server, on the physical host machine you will now see a `logs` directory which contains

```text
logs % tree
.
├── gunicorn_access_log.txt        <<<<< gunicorn WSGI HTTP server access requests
├── gunicorn_error_log.txt         <<<<< gunicorn WSGI HTTP server errors
└── tagbase_server_log.txt         <<<<< tagbase-server Flask application logs
```

This log separation is aimed to provide an intuitive and simple mechanism for understanding how tagbase-server is being used, what the application is being asked to do, how it is doing it and maybe most importantly what is going wrong!

If you have suggestions or requests concerning logging, please [open an issue](https://github.com/tagbase/tagbase-server/issues).

## TagbaseDB Backup and Recovery

You will be glad to know that similar to how logs (see above) are streamed to a persistent volume claim on the physical host, so is all PostgreSQL data. A physical duplicate is created upon the PostgreSQL container initialization and is stored on the physical host in a directory named `postgres-data` which contains similar to the following...

```text
postgres-data % tree -L 2
.
└── pgdata
    ├── PG_VERSION
    ├── base
    ├── global
    ├── pg_commit_ts
    ├── pg_dynshmem
    ├── pg_hba.conf
    ├── pg_ident.conf
    ├── pg_logical
    ├── pg_multixact
    ├── pg_notify
    ├── pg_replslot
    ├── pg_serial
    ├── pg_snapshots
    ├── pg_stat
    ├── pg_stat_tmp
    ├── pg_subtrans
    ├── pg_tblspc
    ├── pg_twophase
    ├── pg_wal
    ├── pg_xact
    ├── postgresql.auto.conf
    ├── postgresql.conf
    ├── postmaster.opts
    └── postmaster.pid

18 directories, 7 files
```

### Duplicating your backup

**We cannot stress enough how important it is to create another duplicate copy of the physical `postgres-data` and `logs` directories.** Ideally they would be stored on a separate physical machine or maybe in the cloud. It would be wise to back up these artifacts frequently to avoid data loss. For example, one could easily write a [cron job](https://www.man7.org/linux/man-pages/man8/cron.8.html) which uses [scp](https://www.man7.org/linux/man-pages/man1/scp.1.html) to duplicate the artifacts to another machine every hour. This will give you confidence, improve your operational readiness and give you a fighting chance of recovering quickly in a disaster recovery situation.

## Real-time metadata anomaly notifications

tagbase-server can be (optionally) very easily configured to post real-time notifications to a [Slack](https://slack.com/) workspace channel. With Slack now being the defacto workplace messaging platform, integration with tagbase-server can really streamline operations tasks because

1. all tagbase **metadata** anomalies are sent to a centralized Slack _channel_ which Admins can also join
2. events and associated notifications are sent in real-time and can be acted upon in a prompt fashion

### Prerequisite

If you don't already have one, [create a Slack workspace](https://slack.com/help/articles/206845317-Create-a-Slack-workspace). Also create the following two channels

- **metadata_ops**: used to report metadata anomalies
- **deploy_ops**: used to report (docker) deployment events

### Create and install an app

[Create and install an app](https://api.slack.com/apps); specifically follow the prompts (click on "Create an app" > "From an app manifest")
![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/create_app.png?raw=true)
![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/select_manifest.png?raw=true)
![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/select_workspace.png?raw=true)
![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/app_manifest.png?raw=true)

Add features and functionality; always save your work so it doesn't get lost!

![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/display_info.png?raw=true)

If you wish, you can grab the [Tagbase logo](https://raw.githubusercontent.com/tagbase/tagbase.github.io/master/images/tagbase.jpg)

Note the App Credentials

![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/app_creds.png?raw=true)

You need to add at least one feature or **permission scope** before you can install your app. Until you do that the _Install to Workspace_ button will be grey as follows, Simply follow the **permission scope** hyperlink

![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/install_app.png?raw=true)

Add the following scopes to the **Scopes** section

![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/set_scopes.png?raw=true)

The _Install to Workspace_ button will now be green so click it and add the app to the relevant channel (e.g., **deploy_ops**) you created earlier.

![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/post_where.png?raw=true)

Once you complete the installation you will be rewarded with a **OAUTH TOKEN** as below. Make note of the one you generate as you will use it later on.

![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/oauth_token.png?raw=true)

Back in your Slack client, on the left hand side, you will now see that your App is registered

![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/app_registered.png?raw=true)

Invite your app to the channel specified above. Simply use the `@` in the channel and look for the app name then tag the app. This will prompt you to add the app to the channel as follows

![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/add_bot.png?raw=true)

Send a test message to make sure everything is working fine. Note this operation will require working knowledge of Python (refer to the [Python Slack API](https://github.com/slackapi/python-slack-sdk) for details).

```python
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack_token = os.environ["SLACK_BOT_TOKEN"]     <<<<<<<<< OAUTH token you created above
client = WebClient(token=slack_token)

try:
    response = client.chat_postMessage(
        channel="C0XXXXXX",                    <<<<<<<<<<< target channel you wish to post to
        text="Hello from your app! :tada:"
    )
except SlackApiError as e:
    # You will get a SlackApiError if "ok" is False
    assert e.response["error"]    # str like 'invalid_auth', 'channel_not_found'
```

If everything went well you will see something similar to the following

![Slack setup screenshot](https://github.com/tagbase/tagbase.github.io/blob/master/images/sample_msg.png?raw=true)

### Configure tagbase-server with the the App credentials

Simply add the following parameters to the `.env` configuration file

1. `SLACK_BOT_TOKEN` - OAUTH token (from above)
2. `SLACK_BOT_CHANNEL` - Slack channel you wish to post your messages to

## Real-time docker event notifications

### Configure tagbase-server with the the Webhook credentials

This can be very useful if administrators desire insight into **docker events**.

1. Create a new channel (`deploy_ops`) in the existing Slack workspace
1. Setup [an Incoming WebHook](https://my.slack.com/services/new/incoming-webhook) on the desired Slack workspace and obtain the WebHook URL.
1. Simply add a `webhook` parameter to the `.env` configuration file with the value being the Webhook URL.
1. Once `docker-compose up` is executed all docker events will now be sent to the Slack channel.

## Logging in to PostgreSQL container

Obtain the container identifier

```text
tagbase-server % docker ps
CONTAINER ID   IMAGE                           COMMAND                  CREATED         STATUS                   PORTS                                     NAMES
...
3962ed298641   tagbase-server_postgres         "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:5432->5432/tcp                    tagbase-server_postgres_1
```

SSH into the container

```text
docker exec -it 3962ed298641 /bin/bash
```

You can now access PostgreSQL via the [psql interactive terminal](https://www.postgresql.org/docs/current/app-psql.html).

To access _any other PostgreSQL database_ you can simply use the _-h_ (hostname) parameters.
