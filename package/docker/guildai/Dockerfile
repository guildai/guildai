FROM ubuntu:18.04

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN apt-get update --assume-yes \
    && apt-get install --assume-yes \
        wget \
        unzip \
        python3 \
        python3-pip \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3 2 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 2 \
    &&  rm -rf /var/lib/apt/lists/*

RUN pip install --pre guildai \
    && pip install tensorflow \
    && pip install virtualenv==16

WORKDIR /root

RUN wget --quiet https://github.com/guildai/examples/archive/master.zip \
    && unzip master.zip \
    && mv examples-master guild-examples \
    && rm master.zip

CMD [ "/bin/bash" ]
