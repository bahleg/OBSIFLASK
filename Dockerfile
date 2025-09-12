FROM python:3.12-slim
COPY /src/requirements.txt /tmp
RUN cd tmp;  pip3  install --upgrade pip --no-cache && pip3 install -r requirements.txt --no-cache && rm requirements.txt
COPY src /src 
RUN cd /src; pip3  install --upgrade pip --no-cache && pip3 --no-cache install .
COPY example /example
COPY example/config.yml /config.yml
CMD obsiflask /config.yml