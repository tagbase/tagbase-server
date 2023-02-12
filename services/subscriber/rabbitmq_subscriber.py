#!/usr/bin/env python3
import logging
import os
import pika
import sys

from logging.handlers import RotatingFileHandler

LOGGER_NAME = "rabbitmq_subscriber"

os.makedirs("./logs/{}".format(LOGGER_NAME), exist_ok=True)
logger = logging.getLogger(LOGGER_NAME)
if logger.hasHandlers():
    logger.handlers = []
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s"
)

s_handler = logging.StreamHandler()
s_handler.setFormatter(formatter)
logger.addHandler(s_handler)

rf_handler = RotatingFileHandler(
    f"./logs/{LOGGER_NAME}/{LOGGER_NAME}_log.txt",
    mode="a",
    maxBytes=100000,
    backupCount=10,
)
rf_handler.setFormatter(formatter)
logger.addHandler(rf_handler)


def process_topic(topic=None, msg_parts=None):
    import db_utils
    import uuid

    if topic == "event_log/create":
        db_utils.create_event(
            event_category=msg_parts[0],
            event_id=uuid.UUID(msg_parts[1]),
            event_name=msg_parts[2],
            event_status=msg_parts[3],
            time_start=msg_parts[4],
        )
    else:
        db_utils.update_event(
            duration=msg_parts[0],
            event_id=uuid.UUID(msg_parts[1]),
            event_status=msg_parts[2],
            submission_id=msg_parts[3],
            tag_id=msg_parts[4],
            time_end=msg_parts[5],
        )


def subscriber():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()
    channel.queue_declare(queue="event_log")

    def callback(ch, method, properties, body):
        logger.info("Received: %r" % body)
        topic, messagedata = body.decode("utf-8").split(" ", 1)
        process_topic(topic, messagedata.split(" "))

    channel.basic_consume(
        queue="event_log", on_message_callback=callback, auto_ack=True
    )
    logger.info("Waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    subscriber()
