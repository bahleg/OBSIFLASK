FROM python:3.12-slim
COPY src /src 
COPY example /example
COPY example/config.yml /config.yml
RUN cd /src; pip3  install --upgrade pip --no-cache && pip3 --no-cache install .
CMD flobsidian /config.yml