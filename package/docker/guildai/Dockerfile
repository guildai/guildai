FROM ubuntu:18.04

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN apt-get update --assume-yes \
    && apt-get install --assume-yes \
        wget=1.19.* \ 
        unzip=6.0-* \ 
        python3=3.6.* \ 
        python3-pip=9.0.* \ 
    && update-alternatives --install /usr/bin/python python /usr/bin/python3 2 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 2 \
    &&  rm -rf /var/lib/apt/lists/*

RUN pip install --pre guildai \
    && pip install virtualenv --upgrade

WORKDIR /root

RUN wget --quiet https://github.com/guildai/guildai/archive/master.zip \
    && unzip master.zip \
    && mv guildai-master/examples guild-examples \
    && rm -rf guildai-master \
    && rm master.zip

CMD [ "/bin/bash" ]
