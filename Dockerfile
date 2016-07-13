FROM python:3.4-alpine

VOLUME /var/tartare/input
VOLUME /var/tartare/output
VOLUME /var/tartare/current

ENV TARTARE_INPUT /var/tartare/input
ENV TARTARE_OUTPUT /var/tartare/output
ENV TARTARE_CURRENT /var/tartare/current

COPY ./tartare /usr/src/app/tartare
COPY requirements.txt /usr/src/app
WORKDIR /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

ENV TARTARE_RABBITMQ_HOST amqp://guest:guest@localhost:5672//
RUN chown -R daemon:daemon /usr/src/app
USER daemon
CMD ["celery", "-A", "tartare.tasks.celery", "worker"]
