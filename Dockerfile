FROM python:2.7.18-slim-buster

WORKDIR /usr/src/Anova
COPY AnovaMaster/ /usr/src/Anova/AnovaMaster/
COPY config/ /usr/src/Anova/config/
COPY requirements.txt /usr/src/Anova/
COPY run.py /usr/src/Anova/

RUN apt-get update && apt-get install -y \
    bluez \
    python-pip \
    virtualenv \
    git \
    libglib2.0-dev && \
    rm -rf /var/lib/apt/lists/*


# Copy in docker scripts to root of container...
COPY dockerscripts/ /

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/cmd.sh"]