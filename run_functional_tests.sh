#!/usr/bin/env bash

docker-compose -f docker-compose.test.yml down
docker build -t tartare_functional_tests .
docker-compose -f docker-compose.test.yml up -d
export TARTARE_HOST_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose -f docker-compose.test.yml ps -q tartare_webservice))
export HTTP_SERVER_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'  $(docker-compose -f docker-compose.test.yml ps -q http_download_server))
py.test -vv  tests/functional
RESULT=$?
docker-compose -f docker-compose.test.yml down
exit $RESULT
