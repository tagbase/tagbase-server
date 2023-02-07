import signal
import zmq

logging.basicConfig(filename="subscriber.log", level=logging.INFO)

signal.signal(signal.SIGINT, signal.SIG_DFL)

context = zmq.Context()

socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5555")
socket.setsockopt(zmq.SUBSCRIBE, b"event_log")


def process_topic(topic=None):
    import db_utils.py

    if topic is "event_log/create":
        db_utils.create_event(
            event_category=msg_parts[0],
            event_id=msg_parts[1],
            event_name=msg_parts[2],
            event_status=msg_parts[3],
            time_start=msg_parts[4],
        )
    else:
        db_utils.update_event(
            duration=msg_parts[0],
            event_id=msg_parts[1],
            event_status=msg_parts[2],
            submission_id=msg_parts[3],
            tag_id=msg_parts[4],
            time_end=msg_parts[5],
        )


while True:
    message = socket.recv()
    topic, messagedata = string.split()
    msg_parts = messagedata.split(" ")
    logging.info(
        "topic: {} message: {} - {}".format(
            topic, messagedata, time.strftime("%Y-%m-%d %H:%M")
        )
    )
    process_topic(topic)
