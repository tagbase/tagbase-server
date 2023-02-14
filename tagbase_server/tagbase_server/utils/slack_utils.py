import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
slack_channel = os.environ.get("SLACK_BOT_CHANNEL", "tagbase-server")
client = WebClient(token=slack_token)
logger = logging.getLogger(__name__)


def post_msg(msg):
    logger.warning(msg)
    try:
        client.chat_postMessage(
            channel=slack_channel, text="<!channel> :warning: " + msg
        )
    except SlackApiError as e:
        logger.error(e)
