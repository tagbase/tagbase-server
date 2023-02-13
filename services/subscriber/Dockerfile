FROM python:slim-bullseye

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apt update && \
	apt install -y --force-yes bash curl gcc iputils-ping && \
	apt clean all && \
	python3 -m pip install --upgrade pip && \
	python3 -m pip install -r requirements.txt --no-cache-dir


ADD rabbitmq_subscriber.py rabbitmq_subscriber.py
ADD db_utils.py db_utils.py

CMD ["python3", "rabbitmq_subscriber.py"]
