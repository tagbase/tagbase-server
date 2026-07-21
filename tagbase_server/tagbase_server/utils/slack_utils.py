import logging
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


def _slack_token():
    return os.environ.get("SLACK_BOT_TOKEN", "").strip()


def _slack_client(token=None):
    return WebClient(token=token if token is not None else _slack_token())


def post_msg(msg):
    logger.warning(msg)
    token = _slack_token()
    # Slack bot tokens are typically xoxb-...; anything else just spams errors.
    if not token.startswith("xoxb-"):
        return
    try:
        _slack_client(token).chat_postMessage(
            channel="metadata_ops", text="<!channel> :warning: " + msg
        )
    except SlackApiError:
        logger.exception("Slack API error while posting message")
    except Exception:
        logger.exception("Something went wrong while posting to slack")
