FROM python:3.12-slim
RUN mkdir /src
COPY requirements.txt /src
RUN cd src;  pip3  install --upgrade pip --no-cache && pip3 install -r requirements.txt --no-cache && rm requirements.txt
COPY obsiflask /src/obsiflask 
COPY setup.py /src/
RUN cd /src; pip3  install --upgrade pip --no-cache && pip3 --no-cache install .
COPY example /example
COPY example/config.yml /config.yml
CMD obsiflask /config.yml
