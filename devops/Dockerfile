FROM ubuntu:20.04

RUN apt-get update && apt-get install -y python3.9 &&  apt-get -y install python3-pip
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1 && update-alternatives --set python /usr/bin/python3.9
RUN apt-get install -y curl

## allows the container to continue running regardless of the PostgreSQL service inside the container
ENTRYPOINT ["tail", "-f", "/dev/null"]
## downside: need to manually start PostgreSQL in the container once the container is running
