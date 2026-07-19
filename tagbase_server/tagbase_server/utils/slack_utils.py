import logging
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
client = WebClient(token=slack_token)
logger = logging.getLogger(__name__)


def post_msg(msg):
    logger.warning(msg)
    try:
        client.chat_postMessage(
            channel="metadata_ops", text="<!channel> :warning: " + msg
        )
    except SlackApiError:
        logger.exception("Slack API error while posting message")
    except Exception:
        logger.exception("Something went wrong while posting to slack")
