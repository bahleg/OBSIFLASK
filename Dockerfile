FROM python:3.12-slim

RUN mkdir /src

COPY requirements.txt /src/requirements.txt
RUN cd src; \
    pip3 install --upgrade pip --no-cache && \
    pip3 install -r requirements.txt --no-cache

COPY obsiflask /src/obsiflask
COPY setup.py /src/setup.py
RUN cd /src; \
    pip3 install --upgrade pip --no-cache && \
    pip3 --no-cache install .

COPY tests /tests
COPY example /example
COPY example/config.yml /config.yml

CMD obsiflask /config.yml
