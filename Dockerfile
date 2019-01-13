FROM python:2

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
    bluez \
    libglib2.0-dev && \
    rm -rf /var/lib/apt/lists/*

ADD . .

RUN pip install -r requirements.txt && \
    rm -rv /root/.cache/pip

CMD ["./start.sh"]
