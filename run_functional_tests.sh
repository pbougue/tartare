#!/usr/bin/env bash

docker build -t tartare_functional_tests .
docker build -t tartare_ruspell_functional_tests -f Dockerfile.ruspell.test .
docker-compose -f docker-compose.test.yml up -d
HTTP_SERVER_ID=$(docker-compose -f docker-compose.test.yml ps -q http_download_server)
export TARTARE_HOST_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose -f docker-compose.test.yml ps -q tartare_webservice))
export HTTP_SERVER_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'  $HTTP_SERVER_ID)
docker cp tests/fixtures/. $HTTP_SERVER_ID:/var/www
py.test -vv tests/functional
RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "Tests passed"
else
    echo "/!\ Tests failed, last logs:"
    docker logs $(docker-compose -f docker-compose.test.yml ps -q tartare_worker)
    docker logs $(docker-compose -f docker-compose.test.yml ps -q ruspell_worker)
fi
docker-compose -f docker-compose.test.yml down -v
exit $RESULT
