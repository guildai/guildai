FROM ubuntu

RUN apt-get update -y
RUN apt-get upgrade -y

RUN apt-get install -y wget
RUN apt-get install -y unzip
RUN apt-get install -y python
RUN apt-get install -y python-pip

RUN pip install --upgrade pip
RUN pip install --pre guildai
RUN pip install tensorflow

WORKDIR /root

RUN wget -q https://github.com/guildai/examples/archive/master.zip
RUN unzip master.zip
RUN mv examples-master guild-examples
RUN rm master.zip

CMD /bin/bash
