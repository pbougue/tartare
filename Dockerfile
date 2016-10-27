FROM python:3.4-alpine

RUN addgroup -g 8110 tartare
RUN adduser -H -D -u 8110 -G tartare tartare

RUN mkdir -p /var/tartare/
RUN chown -R tartare:tartare /var/tartare/

COPY ./tartare /usr/src/app/tartare
COPY requirements.txt /usr/src/app
WORKDIR /usr/src/app

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
        libmemcached-dev && \
    pip install uwsgi && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del \
        g++ \
        build-base \
        python-dev \
        zlib-dev \
        linux-headers \
        musl \
        musl-dev \
        memcached \
        libmemcached-dev && \
    rm -rf /var/apk/cache/*

ENV TARTARE_RABBITMQ_HOST amqp://guest:guest@localhost:5672//
RUN chown -R tartare:tartare /usr/src/app
USER tartare

# you can pass a TARTARE_VERSION to the build (with cli argument --build-arg or in docker-compose)
ARG TARTARE_VERSION
ENV TARTARE_VERSION ${TARTARE_VERSION:-unknown_version}
EXPOSE 5000

CMD ["celery", "-A", "tartare.tasks.celery", "worker"]
