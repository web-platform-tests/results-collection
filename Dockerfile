FROM golang:1.8-jessie

ARG PB_VERSION=3.4.0

# Used by dev server shell script
ENV PB_LIB="/protobuf/src"
ENV BQ_LIB="/protoc-gen-bq-schema"
ENV PROTOS="/wptdashboard/protos"
ENV BQ_OUT="/wptdashboard/bq-schema"
ENV PY_OUT="/wptdashboard/run/protos"

RUN apt-get update && apt-get install --assume-yes --no-install-suggests --no-install-recommends unzip inotify-tools

RUN mkdir /protobuf-fetch
WORKDIR /protobuf-fetch
RUN curl -L -o "protobuf.zip" "https://github.com/google/protobuf/archive/v${PB_VERSION}.zip" && \
  unzip "protobuf.zip" -d / && \
  mv "/protobuf-${PB_VERSION}" "/protobuf" && \
  cd /  && \
  rm -rf /protobuf-fetch

RUN mkdir /pip
WORKDIR /pip
RUN curl -o "get-pip.py" "https://bootstrap.pypa.io/get-pip.py" && \
  python "get-pip.py" "pip===9.0.1" && \
  pip install requests==2.18.1 pycodestyle==2.3.1 google-cloud==0.26.1 protobuf==${PB_VERSION} && \
  cd /  && \
  rm -rf /pip

RUN mkdir /protoc
WORKDIR /protoc
RUN curl -L -o "protoc.zip" "https://github.com/google/protobuf/releases/download/v${PB_VERSION}/protoc-${PB_VERSION}-linux-x86_64.zip" && \
  unzip "protoc.zip" && \
  cp "bin/protoc" /usr/local/bin/ && \
  cd /  && \
  rm -rf /protoc

WORKDIR /
RUN git clone "https://github.com/GoogleCloudPlatform/protoc-gen-bq-schema.git" && \
  cd "protoc-gen-bq-schema" && \
  make && \
  cp bin/protoc-gen-bq-schema /usr/local/bin/

RUN mkdir -p "/wptdashboard"
