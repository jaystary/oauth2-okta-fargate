FROM python:3.8.8-slim-buster


RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

COPY . /app
RUN pip install -r requirements.txt


EXPOSE 8080

ENTRYPOINT [ "python" ]

CMD [ "okta-hosted-login/main.py" ]