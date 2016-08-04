FROM python:3.4-alpine

VOLUME /var/tartare/input
VOLUME /var/tartare/output
VOLUME /var/tartare/current

ENV TARTARE_INPUT /var/tartare/input
ENV TARTARE_OUTPUT /var/tartare/output
ENV TARTARE_CURRENT /var/tartare/current

RUN addgroup -g 8110 tartare
RUN adduser -H -D -u 8110 -G tartare tartare

RUN mkdir -p /var/tartare/
RUN chown -R tartare:tartare /var/tartare/

# those are needed for uwsgi
RUN apk --update add \
        g++ \
        build-base \
        python-dev \
        zlib-dev \
        linux-headers \
        musl \
        musl-dev \
        memcached \
        libmemcached-dev

RUN pip install uwsgi

COPY ./tartare /usr/src/app/tartare
COPY requirements.txt /usr/src/app
WORKDIR /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

RUN apk del \
        g++ \
        build-base \
        python-dev \
        zlib-dev \
        linux-headers \
        musl \
        musl-dev \
        memcached \
        libmemcached-dev

ENV TARTARE_RABBITMQ_HOST amqp://guest:guest@localhost:5672//
RUN chown -R tartare:tartare /usr/src/app
USER tartare

# you can pass a TARTARE_VERSION to the build (with cli argument --build-arg or in docker-compose)
ARG TARTARE_VERSION
ENV TARTARE_VERSION ${TARTARE_VERSION:-unknown_version}

CMD ["celery", "-A", "tartare.tasks.celery", "worker"]
