FROM ubuntu:latest

RUN apt-get update && apt-get install -y python3.10 python3.10-distutils

RUN apt-get install -y python3-pip

RUN pip install --upgrade redis
RUN pip install --upgrade python-telegram-bot --pre


WORKDIR /data/app
#ENV BOT_TOKEN=5837154858:AAHbb7MPsPrDx_TQ4Sv-ZgTIwiGMjJ9uV9g

CMD ["python3", "main.py"]