FROM python:3.11.9-slim
WORKDIR /app
COPY  . /app
RUN apt-get update
RUN apt -y install unzip
RUN apt -y install curl
RUN pip install reflex update
RUN pip install -r requirements.txt

CMD reflex init
CMD reflex run