FROM python:3.6.2-alpine

# Used for celery
#Running a worker with superuser privileges when the
#worker accepts messages serialized with pickle is a very bad idea!
#
#If you really want to continue then you have to set the C_FORCE_ROOT
#environment variable (but please think about this before you do).
#
#User information: uid=0 euid=0 gid=0 egid=0
RUN addgroup -g 8110 tartare
RUN adduser -H -D -u 8110 -G tartare tartare

WORKDIR /usr/src/app

# avoid Permission denied: '/usr/src/app/celerybeat.pid'
RUN chown -R tartare:tartare /usr/src/app
COPY requirements.txt /usr/src/app

# those are needed for uwsgi
RUN apk --update add \
        g++ \
        libstdc++ \
        linux-headers && \
    pip install uwsgi && \
    pip install --no-cache-dir -r requirements.txt && \
    find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + && \
    apk del \
        g++ \
        linux-headers && \
    rm -rf /var/apk/cache/*

ENV TARTARE_RABBITMQ_HOST amqp://guest:guest@localhost:5672//

EXPOSE 5000
USER tartare

COPY ./migrations /usr/src/app/migrations

# you can pass a TARTARE_VERSION to the build (with cli argument --build-arg or in docker-compose)
ARG TARTARE_VERSION
ENV TARTARE_VERSION ${TARTARE_VERSION:-unknown_version}

COPY ./tartare /usr/src/app/tartare

CMD ["celery", "-A", "tartare.tasks.celery", "worker"]
