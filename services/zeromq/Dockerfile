FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y --force-yes python python-dev python-setuptools software-properties-common gcc python-pip
RUN apt-get clean all

RUN pip install pyzmq

ADD zeromq_server.py /tmp/zeromq_server.py

# Zmq Sub Server
EXPOSE 5555

CMD ["python","/tmp/zmqserver.py"]
