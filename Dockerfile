FROM python:3.6.2-alpine

RUN addgroup -g 8110 tartare
RUN adduser -H -D -u 8110 -G tartare tartare

WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app

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

# you can pass a TARTARE_VERSION to the build (with cli argument --build-arg or in docker-compose)
ARG TARTARE_VERSION
ENV TARTARE_VERSION ${TARTARE_VERSION:-unknown_version}
EXPOSE 5000

COPY ./tartare /usr/src/app/tartare
COPY ./migrations /usr/src/app/migrations

# Used for celery
#Running a worker with superuser privileges when the
#worker accepts messages serialized with pickle is a very bad idea!
#
#If you really want to continue then you have to set the C_FORCE_ROOT
#environment variable (but please think about this before you do).
#
#User information: uid=0 euid=0 gid=0 egid=0
USER tartare

CMD ["celery", "-A", "tartare.tasks.celery", "worker"]
