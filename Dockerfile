FROM python:3.9-alpine

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

CMD ["/bin/sh", "docker-entrypoint.sh"]
