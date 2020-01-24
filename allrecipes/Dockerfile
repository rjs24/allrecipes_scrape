FROM python:latest

WORKDIR /usr/src/app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

ENTRYPOINT python3 ./spider_start.py