FROM golang:1.8-jessie

# Install pip 9.0.1
RUN curl -o "get-pip.py" "https://bootstrap.pypa.io/get-pip.py" && \
  python "get-pip.py" "pip===9.0.1" && \
  rm "get-pip.py"

# Mount code and install dependencies that it specifies
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
