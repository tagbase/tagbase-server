import logging
import pika
import time

logger = logging.getLogger(__name__)


def publish_message(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()
    channel.queue_declare(queue="events_log")
    channel.basic_publish(exchange="", routing_key="events_log", body=message)
    logger.info(" [x] Sent: {}".format(message))
    connection.close()
