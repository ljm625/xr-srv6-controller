FROM python:3.6-slim-stretch
RUN apt-get update
RUN apt-get install -y iproute2 python3-dev gcc
COPY ./requirements.txt /
RUN pip3 install -r /requirements.txt
RUN mkdir /app
COPY ./ /app
RUN chmod +x /app/startup.sh
WORKDIR /app
ENTRYPOINT ["sh","/app/startup.sh","python3","main.py"]