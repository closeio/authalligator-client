FROM ubuntu:20.04 as base

# install python3
RUN \
  DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y python3-dev python3-pip libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# install requirements
WORKDIR /src
COPY . .
RUN pip3 install .[tests]

# for convenience working inside an interactive running container
RUN echo 'alias python=python3' >> ~/.bashrc
RUN echo 'alias pip=pip3' >> ~/.bashrc
